#!/usr/bin/env python3
"""
OmniFuzz 主训练脚本
基于多智能体强化学习的电力物联网设备协议感知模糊测试框架
"""

import torch
import yaml
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

from src.core.agent_array import AgentArray
from src.core.value_network import ValueNetwork
from src.environment.power_iot_env import PowerIoTEnvironment
from src.training.trainer import OmniFuzzTrainer
from src.utils.data_preprocessor import DataPreprocessor

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('omnifuzz_training.log'),
            logging.StreamHandler()
        ]
    )

def load_config(config_path: str) -> Dict[str, Any]:
    """加载配置文件"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def main():
    parser = argparse.ArgumentParser(description='OmniFuzz 训练脚本')
    parser.add_argument('--config', type=str, default='config/default_config.yaml',
                       help='配置文件路径')
    parser.add_argument('--protocols', nargs='+', 
                       default=['modbus_tcp', 'ethernet_ip', 'siemens_s7'],
                       help='要测试的协议列表')
    parser.add_argument('--episodes', type=int, default=200,
                       help='训练周期数')
    parser.add_argument('--device', type=str, default='cuda',
                       help='训练设备 (cuda/cpu)')
    
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
    
    try:
        # 初始化组件
        logger.info("初始化OmniFuzz组件...")
        
        # 数据预处理
        preprocessor = DataPreprocessor()
        
        # 创建环境
        environment = PowerIoTEnvironment(
            protocols=args.protocols,
            config=config
        )
        
        # 创建共享价值网络
        shared_value_networks = {}
        for protocol in args.protocols:
            state_dim = config['protocols'][protocol].get('state_dim', 1000)
            action_dim = config['protocols'][protocol].get('action_dim', 8)
            shared_value_networks[protocol] = ValueNetwork(
                state_dim=state_dim,
                action_dim=action_dim
            ).to(device)
        
        # 创建智能体数组
        agent_arrays = {}
        for protocol in args.protocols:
            protocol_config = config['protocols'][protocol]
            agent_arrays[protocol] = AgentArray(
                protocol_name=protocol,
                field_config=protocol_config['fields'],
                shared_value_network=shared_value_networks[protocol],
                device=device
            )
        
        # 创建训练器
        trainer = OmniFuzzTrainer(
            agent_arrays=agent_arrays,
            environment=environment,
            config=config,
            device=device
        )
        
        logger.info("开始训练...")
        
        # 训练循环
        training_results = trainer.train(num_episodes=args.episodes)
        
        logger.info("训练完成!")
        
        # 保存模型
        trainer.save_models('models/')
        logger.info("模型已保存到 models/ 目录")
        
        # 输出训练结果
        logger.info(f"最终奖励: {training_results['final_reward']:.4f}")
        logger.info(f"发现的漏洞数量: {training_results['vulnerabilities_found']}")
        logger.info(f"平均代码覆盖率: {training_results['avg_coverage']:.2f}%")
        
    except Exception as e:
        logger.error(f"训练过程中发生错误: {e}")
        raise

if __name__ == "__main__":
    main()