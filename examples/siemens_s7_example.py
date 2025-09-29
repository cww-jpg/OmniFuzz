#!/usr/bin/env python3
"""
Siemens S7 protocol fuzzing example
Demonstrates multi-agent collaboration and reward calculation
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
    """Run Siemens S7 example"""
    print("=== Siemens S7 Fuzzing Example ===")
    
    # Load config
    config_path = Path('config/default_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Select device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    try:
        # 1. Create coverage tracker
        print("\n1. Initialize coverage tracker...")
        coverage_tracker = CoverageTracker()
        coverage_tracker.set_total_counts(1000, 200)  # 1000 basic blocks, 200 functions
        
        # Record some execution paths
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
            print(f"  New basic blocks: {coverage_data['new_blocks']}, "
                  f"new functions: {coverage_data['new_functions']}, "
                  f"path depth: {coverage_data['path_depth']}")
        
        # 2. Create reward calculator
        print("\n2. Initialize reward calculator...")
        reward_calculator = RewardCalculator(config)
        
        # Simulate fuzzing results
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
        print(f"  Total reward: {reward:.4f}")
        
        # 3. Multi-agent collaboration demo
        print("\n3. Multi-agent collaboration demo...")
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
        
        print(f"  Siemens S7 agent array has {len(agent_array.agents)} agents:")
        for agent in agent_array.agents:
            print(f"    - {agent.field_name}")
        
        # 4. Run collaboration test
        print("\n4. Run collaboration test...")
        observations = environment.reset()
        
        collaboration_rewards = []
        
        for step in range(3):
            print(f"\n  Collaboration step {step + 1}:")
            
            # Each agent selects actions
            individual_actions = {}
            for agent in agent_array.agents:
                observation = observations['siemens_s7'].get(agent.field_name, torch.randn(10))
                action = agent.select_action(observation)
                individual_actions[agent.field_name] = action
                print(f"    {agent.field_name} action: {action.item()}")
            
            # Merge into global action
            global_observation = agent_array.get_global_observation(
                observations['siemens_s7']
            )
            print(f"    Global observation shape: {global_observation.shape}")
            
            # Step environment
            next_observations, reward, done, info = environment.step(
                {'siemens_s7': individual_actions}
            )
            
            collaboration_rewards.append(reward)
            print(f"    Collaboration reward: {reward:.4f}")
            
            observations = next_observations
        
        avg_collaboration_reward = sum(collaboration_rewards) / len(collaboration_rewards)
        print(f"\n  Average collaboration reward: {avg_collaboration_reward:.4f}")
        
        # 5. Generate final report
        print("\n5. Generate final report...")
        coverage_summary = coverage_tracker.get_coverage_summary()
        
        if 'error' not in coverage_summary:
            bb_coverage = coverage_summary['basic_block_coverage']
            func_coverage = coverage_summary['function_coverage']
            
            print(f"  Basic block coverage: {bb_coverage['covered']}/{bb_coverage['total']} "
                  f"({bb_coverage['percentage']:.2f}%)")
            print(f"  Function coverage: {func_coverage['covered']}/{func_coverage['total']} "
                  f"({func_coverage['percentage']:.2f}%)")
            print(f"  Unique execution paths: {coverage_summary['path_coverage']['unique_paths']}")
        
        print("\n6. Siemens S7 example finished!")
        
    except Exception as e:
        print(f"Example error: {e}")
        raise

if __name__ == "__main__":
    run_siemens_s7_example()