#!/usr/bin/env python3
"""
EtherNet/IP 协议模糊测试示例
"""

import torch
import yaml
from pathlib import Path

from src.core.agent_array import AgentArray
from src.core.value_network import ValueNetwork
from src.environment.power_iot_env import PowerIoTEnvironment
from src.fuzzing.mutation_engine import MutationEngine

def run_ethernet_ip_example():
    """运行EtherNet/IP示例"""
    print("=== EtherNet/IP 模糊测试示例 ===")
    
    # 加载配置
    config_path = Path('config/default_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    
    try:
        # 1. 创建变异引擎
        print("\n1. 初始化变异引擎...")
        protocol_config = config['protocols']['ethernet_ip']
        mutation_engine = MutationEngine(protocol_config)
        
        # 示例消息: EtherNet/IP RegisterSession
        example_message = bytes.fromhex(
            "00650004000000000000000000000000000000000100"
        )
        
        print(f"原始消息: {example_message.hex()}")
        
        # 应用变异
        mutation_actions = {
            'command': 0,  # FIELD_FLIPPING
            'length': 1,   # FIELD_DELETION
            'data': 2      # FIELD_DUPLICATION
        }
        
        mutated_message = mutation_engine.mutate_protocol_message(
            example_message, mutation_actions
        )
        
        print(f"变异消息: {mutated_message.hex()}")
        print(f"消息长度变化: {len(example_message)} -> {len(mutated_message)}")
        
        # 2. 创建环境和智能体
        print("\n2. 初始化环境和智能体...")
        environment = PowerIoTEnvironment(
            protocols=['ethernet_ip'],
            config=config
        )
        
        shared_value_network = ValueNetwork(
            state_dim=200,
            action_dim=8
        ).to(device)
        
        agent_array = AgentArray(
            protocol_name='ethernet_ip',
            field_config=protocol_config['fields'],
            shared_value_network=shared_value_network,
            device=device
        )
        
        # 3. 演示智能体决策过程
        print("\n3. 演示智能体决策...")
        observations = environment.reset()
        
        for step in range(2):
            print(f"\n决策步骤 {step + 1}:")
            
            # 显示当前观察
            for field_name, observation in observations['ethernet_ip'].items():
                if isinstance(observation, torch.Tensor):
                    print(f"  {field_name} 观察: 形状 {observation.shape}")
            
            # 智能体选择动作
            actions = agent_array.select_actions(observations['ethernet_ip'])
            
            # 显示选择的动作
            for field_name, action in actions.items():
                print(f"  {field_name}: 动作 {action.item()}")
            
            # 执行一步
            next_observations, reward, done, info = environment.step(
                {'ethernet_ip': actions}
            )
            
            print(f"  获得奖励: {reward:.4f}")
            
            observations = next_observations
        
        print("\n4. 示例完成!")
        
    except Exception as e:
        print(f"示例运行出错: {e}")
        raise

if __name__ == "__main__":
    run_ethernet_ip_example()