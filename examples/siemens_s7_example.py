#!/usr/bin/env python3
"""
Siemens S7 协议模糊测试示例
展示多智能体协作和奖励计算
"""

import torch
import yaml
from pathlib import Path

from src.core.agent_array import AgentArray
from src.core.value_network import ValueNetwork
from src.environment.power_iot_env import PowerIoTEnvironment
from src.training.reward_calculator import RewardCalculator
from src.fuzzing.coverage_tracker import CoverageTracker

def run_siemens_s7_example():
    """运行Siemens S7示例"""
    print("=== Siemens S7 协议模糊测试示例 ===")
    
    # 加载配置
    config_path = Path('config/default_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    
    try:
        # 1. 创建覆盖率跟踪器
        print("\n1. 初始化覆盖率跟踪器...")
        coverage_tracker = CoverageTracker()
        coverage_tracker.set_total_counts(1000, 200)  # 1000个基本块，200个函数
        
        # 记录一些执行路径
        execution_data = [
            {
                'basic_blocks': ['bb1', 'bb2', 'bb3', 'bb4'],
                'functions': ['func1', 'func2'],
                'execution_sequence': ['bb1', 'bb2', 'bb3', 'bb4']
            },
            {
                'basic_blocks': ['bb1', 'bb2', 'bb5'],
                'functions': ['func1', 'func3'],
                'execution_sequence': ['bb1', 'bb2', 'bb5']
            }
        ]
        
        for data in execution_data:
            coverage_data = coverage_tracker.record_execution(
                data['basic_blocks'],
                data['functions'],
                data['execution_sequence']
            )
            print(f"  新基本块: {coverage_data['new_blocks']}, "
                  f"新函数: {coverage_data['new_functions']}, "
                  f"路径深度: {coverage_data['path_depth']}")
        
        # 2. 创建奖励计算器
        print("\n2. 初始化奖励计算器...")
        reward_calculator = RewardCalculator(config)
        
        # 模拟模糊测试结果
        fuzzing_results = {
            'vulnerabilities': [
                {'severity': 'critical', 'type': 'buffer_overflow'},
                {'severity': 'major', 'type': 'use_after_free'},
                {'severity': 'minor', 'type': 'integer_overflow'}
            ],
            'execution_depth': {'agent1': 150, 'agent2': 80, 'agent3': 200},
            'vulnerability_types': ['buffer_overflow', 'use_after_free', 'integer_overflow']
        }
        
        reward = reward_calculator.calculate_reward(fuzzing_results)
        print(f"  计算的总奖励: {reward:.4f}")
        
        # 3. 多智能体协作演示
        print("\n3. 多智能体协作演示...")
        environment = PowerIoTEnvironment(
            protocols=['siemens_s7'],
            config=config
        )
        
        protocol_config = config['protocols']['siemens_s7']
        shared_value_network = ValueNetwork(
            state_dim=150,
            action_dim=8
        ).to(device)
        
        agent_array = AgentArray(
            protocol_name='siemens_s7',
            field_config=protocol_config['fields'],
            shared_value_network=shared_value_network,
            device=device
        )
        
        print(f"  Siemens S7 智能体数组包含 {len(agent_array.agents)} 个智能体:")
        for agent in agent_array.agents:
            print(f"    - {agent.field_name}")
        
        # 4. 运行协作测试
        print("\n4. 运行协作测试...")
        observations = environment.reset()
        
        collaboration_rewards = []
        
        for step in range(3):
            print(f"\n  协作步骤 {step + 1}:")
            
            # 各智能体独立选择动作
            individual_actions = {}
            for agent in agent_array.agents:
                observation = observations['siemens_s7'].get(agent.field_name, torch.randn(10))
                action = agent.select_action(observation)
                individual_actions[agent.field_name] = action
                print(f"    {agent.field_name} 选择动作: {action.item()}")
            
            # 合并为全局动作
            global_observation = agent_array.get_global_observation(
                observations['siemens_s7']
            )
            print(f"    全局观察维度: {global_observation.shape}")
            
            # 执行环境步骤
            next_observations, reward, done, info = environment.step(
                {'siemens_s7': individual_actions}
            )
            
            collaboration_rewards.append(reward)
            print(f"    协作奖励: {reward:.4f}")
            
            observations = next_observations
        
        avg_collaboration_reward = sum(collaboration_rewards) / len(collaboration_rewards)
        print(f"\n  平均协作奖励: {avg_collaboration_reward:.4f}")
        
        # 5. 生成最终报告
        print("\n5. 生成最终报告...")
        coverage_summary = coverage_tracker.get_coverage_summary()
        
        if 'error' not in coverage_summary:
            bb_coverage = coverage_summary['basic_block_coverage']
            func_coverage = coverage_summary['function_coverage']
            
            print(f"  基本块覆盖率: {bb_coverage['covered']}/{bb_coverage['total']} "
                  f"({bb_coverage['percentage']:.2f}%)")
            print(f"  函数覆盖率: {func_coverage['covered']}/{func_coverage['total']} "
                  f"({func_coverage['percentage']:.2f}%)")
            print(f"  唯一执行路径: {coverage_summary['path_coverage']['unique_paths']} 个")
        
        print("\n6. Siemens S7 示例完成!")
        
    except Exception as e:
        print(f"示例运行出错: {e}")
        raise

if __name__ == "__main__":
    run_siemens_s7_example()