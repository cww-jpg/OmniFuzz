#!/usr/bin/env python3
"""
Modbus TCP protocol fuzzing example
"""

import torch
import yaml
from pathlib import Path

from src.core.agent_array import AgentArray
from src.core.value_network import ValueNetwork
from src.environment.power_iot_env import PowerIoTEnvironment
from src.fuzzing.test_case_generator import TestCaseGenerator

def run_modbus_example():
    """Run Modbus TCP example"""
    print("=== Modbus TCP Fuzzing Example ===")
    
    # Load config
    config_path = Path('config/default_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Select device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    try:
        # 1. Create test case generator
        print("\n1. Initialize test case generator...")
        test_generator = TestCaseGenerator(config['protocols'])
        
        # Generate test cases
        test_cases = test_generator.generate_test_cases(
            protocol='modbus_tcp',
            count=5,
            priority=2  # MEDIUM
        )
        
        print(f"Generated {len(test_cases)} test cases")
        for i, test_case in enumerate(test_cases):
            print(f"  Case {i+1}: {test_case['id']}, data length: {len(test_case['mutated_data'])}")
        
        # 2. Create environment
        print("\n2. Initialize Power IoT environment...")
        environment = PowerIoTEnvironment(
            protocols=['modbus_tcp'],
            config=config
        )
        
        # 3. Create agent array (randomly initialized models)
        print("\n3. Initialize agent array...")
        protocol_config = config['protocols']['modbus_tcp']
        shared_value_network = ValueNetwork(
            state_dim=100,  # simplified dimension
            action_dim=8
        ).to(device)
        
        agent_array = AgentArray(
            protocol_name='modbus_tcp',
            field_config=protocol_config['fields'],
            shared_value_network=shared_value_network,
            device=device
        )
        
        print(f"Created agent array with {len(agent_array.agents)} agents")
        for agent in agent_array.agents:
            print(f"  - {agent.field_name}: state dim {agent.policy_network.network[0].in_features}")
        
        # 4. Run a simple test loop
        print("\n4. Run test loop...")
        observations = environment.reset()
        
        for step in range(3):  # run 3 steps
            print(f"\nStep {step + 1}:")
            
            # Agents select actions
            actions = agent_array.select_actions(observations['modbus_tcp'])
            print(f"  Selected actions: {actions}")
            
            # Step environment
            next_observations, reward, done, info = environment.step(
                {'modbus_tcp': actions}
            )
            
            print(f"  Reward: {reward:.4f}")
            print(f"  Done: {done}")
            
            if 'vulnerabilities_found' in info and info['vulnerabilities_found']:
                print(f"  Vulnerabilities found: {len(info['vulnerabilities_found'])}")
            
            observations = next_observations
            
            if done:
                print("  Environment terminated early")
                break
        
        print("\n5. Example finished!")
        
    except Exception as e:
        print(f"Example error: {e}")
        raise

if __name__ == "__main__":
    run_modbus_example()