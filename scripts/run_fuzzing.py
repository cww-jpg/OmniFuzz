#!/usr/bin/env python3
"""
OmniFuzz 模糊测试运行脚本
使用训练好的模型进行多协议并发模糊测试
"""

import torch
import yaml
import argparse
import logging
import time
from pathlib import Path
from typing import Dict, List, Any

from src.core.agent_array import AgentArray
from src.core.value_network import ValueNetwork
from src.environment.power_iot_env import PowerIoTEnvironment
from src.fuzzing.mutation_engine import MutationEngine
from src.fuzzing.coverage_tracker import CoverageTracker
from src.utils.monitoring import ResourceMonitor

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('omnifuzz_fuzzing.log'),
            logging.StreamHandler()
        ]
    )

def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def load_trained_models(models_dir: str, protocols: List[str], 
                       config: Dict[str, Any], device: torch.device) -> Dict[str, AgentArray]:
    """加载训练好的模型"""
    agent_arrays = {}
    models_path = Path(models_dir)
    
    for protocol in protocols:
        protocol_path = models_path / protocol
        
        if not protocol_path.exists():
            logging.warning(f"协议 {protocol} 的模型目录不存在: {protocol_path}")
            continue
            
        # 创建共享价值网络
        state_dim = config['protocols'][protocol].get('state_dim', 1000)
        action_dim = config['protocols'][protocol].get('action_dim', 8)
        shared_value_network = ValueNetwork(
            state_dim=state_dim,
            action_dim=action_dim
        ).to(device)
        
        # 加载价值网络
        value_net_path = protocol_path / "value_network.pth"
        if value_net_path.exists():
            shared_value_network.load_state_dict(torch.load(value_net_path))
        
        # 创建智能体数组
        protocol_config = config['protocols'][protocol]
        agent_array = AgentArray(
            protocol_name=protocol,
            field_config=protocol_config['fields'],
            shared_value_network=shared_value_network,
            device=device
        )
        
        # 加载每个智能体的策略网络
        for agent in agent_array.agents:
            model_path = protocol_path / f"agent_{agent.field_name}.pth"
            if model_path.exists():
                agent.policy_network.load_state_dict(torch.load(model_path))
            else:
                logging.warning(f"智能体 {agent.field_name} 的模型文件不存在: {model_path}")
        
        agent_arrays[protocol] = agent_array
        logging.info(f"加载协议 {protocol} 的模型完成，包含 {len(agent_array.agents)} 个智能体")
    
    return agent_arrays

def main():
    parser = argparse.ArgumentParser(description='OmniFuzz 模糊测试运行脚本')
    parser.add_argument('--models_dir', type=str, default='models/',
                       help='训练好的模型目录')
    parser.add_argument('--config', type=str, default='config/default_config.yaml',
                       help='配置文件路径')
    parser.add_argument('--protocols', nargs='+', 
                       default=['modbus_tcp', 'ethernet_ip', 'siemens_s7'],
                       help='要测试的协议列表')
    parser.add_argument('--duration', type=int, default=3600,
                       help='测试持续时间（秒）')
    parser.add_argument('--output_dir', type=str, default='fuzzing_results/',
                       help='结果输出目录')
    parser.add_argument('--device', type=str, default='cuda',
                       help='运行设备 (cuda/cpu)')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 加载配置
    config = load_config(args.config)
    logger.info(f"加载配置文件: {args.config}")
    
    # 设置设备
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    logger.info(f"使用设备: {device}")
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 启动资源监控
        resource_monitor = ResourceMonitor(interval=5.0)
        resource_monitor.start_monitoring()
        
        # 加载训练好的模型
        logger.info("加载训练好的模型...")
        agent_arrays = load_trained_models(
            args.models_dir, args.protocols, config, device
        )
        
        if not agent_arrays:
            logger.error("没有加载到任何模型，请检查模型目录")
            return
        
        # 创建环境
        environment = PowerIoTEnvironment(
            protocols=args.protocols,
            config=config
        )
        
        # 创建覆盖率跟踪器
        coverage_tracker = CoverageTracker()
        
        # 创建变异引擎
        mutation_engines = {}
        for protocol in args.protocols:
            protocol_config = config['protocols'][protocol]
            mutation_engines[protocol] = MutationEngine(protocol_config)
        
        logger.info(f"开始模糊测试，持续时间: {args.duration}秒")
        start_time = time.time()
        
        # 模糊测试主循环
        test_cases_sent = 0
        vulnerabilities_found = []
        protocol_stats = {protocol: {'messages_sent': 0, 'crashes': 0} 
                         for protocol in args.protocols}
        
        while time.time() - start_time < args.duration:
            # 重置环境
            observations = environment.reset()
            
            # 运行测试周期
            episode_vulnerabilities = run_fuzzing_episode(
                agent_arrays, environment, mutation_engines, 
                observations, coverage_tracker, config
            )
            
            vulnerabilities_found.extend(episode_vulnerabilities)
            test_cases_sent += sum(stats['messages_sent'] for stats in protocol_stats.values())
            
            # 记录进度
            elapsed = time.time() - start_time
            if int(elapsed) % 60 == 0:  # 每分钟记录一次
                logger.info(
                    f"进度: {elapsed:.0f}/{args.duration}秒 | "
                    f"测试用例: {test_cases_sent} | "
                    f"漏洞发现: {len(vulnerabilities_found)}"
                )
        
        # 停止资源监控
        resource_monitor.stop_monitoring()
        
        # 生成测试报告
        generate_fuzzing_report(
            output_dir, vulnerabilities_found, protocol_stats,
            coverage_tracker, resource_monitor, args.duration
        )
        
        logger.info(f"模糊测试完成! 结果保存在: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"模糊测试过程中发生错误: {e}")
        raise

def run_fuzzing_episode(agent_arrays, environment, mutation_engines, 
                       observations, coverage_tracker, config) -> List[Dict]:
    """运行一个模糊测试周期"""
    vulnerabilities = []
    step_count = 0
    max_steps = config.get('fuzzing', {}).get('max_steps_per_episode', 100)
    
    while step_count < max_steps:
        # 智能体选择动作
        actions = {}
        for protocol, agent_array in agent_arrays.items():
            if protocol in observations:
                protocol_actions = agent_array.select_actions(observations[protocol])
                actions[protocol] = protocol_actions
        
        # 执行环境步骤
        next_observations, reward, done, info = environment.step(actions)
        
        # 记录漏洞
        if 'vulnerabilities_found' in info:
            vulnerabilities.extend(info['vulnerabilities_found'])
        
        # 记录覆盖率
        if 'coverage_data' in info:
            coverage_tracker.record_execution(
                basic_blocks=info['coverage_data'].get('basic_blocks', []),
                functions=info['coverage_data'].get('functions', []),
                execution_sequence=info['coverage_data'].get('execution_sequence', [])
            )
        
        observations = next_observations
        step_count += 1
        
        if done:
            break
    
    return vulnerabilities

def generate_fuzzing_report(output_dir: Path, vulnerabilities: List[Dict], 
                          protocol_stats: Dict, coverage_tracker: CoverageTracker,
                          resource_monitor: ResourceMonitor, duration: int):
    """生成模糊测试报告"""
    
    # 漏洞统计
    vulnerability_stats = {}
    for vuln in vulnerabilities:
        vuln_type = vuln.get('type', 'unknown')
        severity = vuln.get('severity', 'unknown')
        
        if vuln_type not in vulnerability_stats:
            vulnerability_stats[vuln_type] = {'count': 0, 'severities': {}}
        
        vulnerability_stats[vuln_type]['count'] += 1
        vulnerability_stats[vuln_type]['severities'][severity] = \
            vulnerability_stats[vuln_type]['severities'].get(severity, 0) + 1
    
    # 生成报告
    report = [
        "OmniFuzz 模糊测试报告",
        "=" * 50,
        f"测试持续时间: {duration} 秒",
        f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"总测试用例: {sum(stats['messages_sent'] for stats in protocol_stats.values())}",
        f"总漏洞发现: {len(vulnerabilities)}",
        "",
        "协议统计:"
    ]
    
    for protocol, stats in protocol_stats.items():
        crash_rate = stats['crashes'] / max(1, stats['messages_sent']) * 100
        report.append(
            f"  {protocol}: {stats['messages_sent']} 消息, "
            f"{stats['crashes']} 崩溃 ({crash_rate:.2f}%)"
        )
    
    report.append("\n漏洞统计:")
    for vuln_type, stats in vulnerability_stats.items():
        report.append(f"  {vuln_type}: {stats['count']} 个")
        for severity, count in stats['severities'].items():
            report.append(f"    {severity}: {count} 个")
    
    # 覆盖率报告
    coverage_summary = coverage_tracker.get_coverage_summary()
    if 'error' not in coverage_summary:
        report.extend([
            "",
            "代码覆盖率:",
            f"  基本块覆盖率: {coverage_summary['basic_block_coverage']['percentage']:.2f}%",
            f"  函数覆盖率: {coverage_summary['function_coverage']['percentage']:.2f}%",
            f"  唯一路径: {coverage_summary['path_coverage']['unique_paths']} 个"
        ])
    
    # 资源使用报告
    resource_report = resource_monitor.generate_report()
    report.extend(["", "资源使用:", resource_report])
    
    # 保存报告
    report_path = output_dir / "fuzzing_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    # 保存漏洞详情
    if vulnerabilities:
        vuln_details = []
        for i, vuln in enumerate(vulnerabilities, 1):
            vuln_details.append(f"漏洞 #{i}:")
            for key, value in vuln.items():
                vuln_details.append(f"  {key}: {value}")
            vuln_details.append("")
        
        vuln_path = output_dir / "vulnerability_details.txt"
        with open(vuln_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(vuln_details))
    
    logging.info(f"测试报告已生成: {report_path}")

if __name__ == "__main__":
    main()