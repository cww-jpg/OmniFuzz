#!/usr/bin/env python3
"""
Modbus TCP 协议模糊测试示例
"""

import torch
import yaml
from pathlib import Path

from src.core.agent_array import AgentArray
from src.core.value_network import ValueNetwork
from src.environment.power_iot_env import PowerIoTEnvironment
from src.fuzzing.test_case_generator import TestCaseGenerator

def run_modbus_example():
    """运行Modbus TCP示例"""
    print("=== Modbus TCP 模糊测试示例 ===")
    
    # 加载配置
    config_path = Path('config/default_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    
    try:
        # 1. 创建测试用例生成器
        print("\n1. 初始化测试用例生成器...")
        test_generator = TestCaseGenerator(config['protocols'])
        
        # 生成测试用例
        test_cases = test_generator.generate_test_cases(
            protocol='modbus_tcp',
            count=5,
            priority=2  # MEDIUM
        )
        
        print(f"生成 {len(test_cases)} 个测试用例")
        for i, test_case in enumerate(test_cases):
            print(f"  用例 {i+1}: {test_case['id']}, 数据长度: {len(test_case['mutated_data'])}")
        
        # 2. 创建环境
        print("\n2. 初始化电力物联网环境...")
        environment = PowerIoTEnvironment(
            protocols=['modbus_tcp'],
            config=config
        )
        
        # 3. 创建智能体数组（使用随机初始化的模型）
        print("\n3. 初始化智能体数组...")
        protocol_config = config['protocols']['modbus_tcp']
        shared_value_network = ValueNetwork(
            state_dim=100,  # 简化维度
            action_dim=8
        ).to(device)
        
        agent_array = AgentArray(
            protocol_name='modbus_tcp',
            field_config=protocol_config['fields'],
            shared_value_network=shared_value_network,
            device=device
        )
        
        print(f"创建智能体数组，包含 {len(agent_array.agents)} 个智能体")
        for agent in agent_array.agents:
            print(f"  - {agent.field_name}: 状态维度 {agent.policy_network.network[0].in_features}")
        
        # 4. 运行简单的测试循环
        print("\n4. 运行测试循环...")
        observations = environment.reset()
        
        for step in range(3):  # 运行3步演示
            print(f"\n步骤 {step + 1}:")
            
            # 智能体选择动作
            actions = agent_array.select_actions(observations['modbus_tcp'])
            print(f"  选择的动作: {actions}")
            
            # 执行环境步骤
            next_observations, reward, done, info = environment.step(
                {'modbus_tcp': actions}
            )
            
            print(f"  奖励: {reward:.4f}")
            print(f"  是否结束: {done}")
            
            if 'vulnerabilities_found' in info and info['vulnerabilities_found']:
                print(f"  发现的漏洞: {len(info['vulnerabilities_found'])} 个")
            
            observations = next_observations
            
            if done:
                print("  环境提前结束")
                break
        
        print("\n5. 示例完成!")
        
    except Exception as e:
        print(f"示例运行出错: {e}")
        raise

if __name__ == "__main__":
    run_modbus_example()