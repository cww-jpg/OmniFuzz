#!/usr/bin/env python3
"""
EtherNet/IP protocol fuzzing example
"""

import torch
import yaml
from pathlib import Path

from src.core.agent_array import AgentArray
from src.core.value_network import ValueNetwork
from src.environment.power_iot_env import PowerIoTEnvironment
from src.fuzzing.mutation_engine import MutationEngine

def run_ethernet_ip_example():
    """Run EtherNet/IP example"""
    print("=== EtherNet/IP Fuzzing Example ===")
    
    # Load config
    config_path = Path('config/default_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Select device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    try:
        # 1. Create mutation engine
        print("\n1. Initialize mutation engine...")
        protocol_config = config['protocols']['ethernet_ip']
        mutation_engine = MutationEngine(protocol_config)
        
        # Example message: EtherNet/IP RegisterSession
        example_message = bytes.fromhex(
            "00650004000000000000000000000000000000000100"
        )
        
        print(f"Original message: {example_message.hex()}")
        
        # Apply mutation
        mutation_actions = {
            'command': 0,  # FIELD_FLIPPING
            'length': 1,   # FIELD_DELETION
            'data': 2      # FIELD_DUPLICATION
        }
        
        mutated_message = mutation_engine.mutate_protocol_message(
            example_message, mutation_actions
        )
        
        print(f"Mutated message: {mutated_message.hex()}")
        print(f"Length change: {len(example_message)} -> {len(mutated_message)}")
        
        # 2. Create environment and agents
        print("\n2. Initialize environment and agents...")
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
        
        # 3. Demonstrate agent decision making
        print("\n3. Demonstrate agent decisions...")
        observations = environment.reset()
        
        for step in range(2):
            print(f"\nDecision step {step + 1}:")
            
            # Show current observation
            for field_name, observation in observations['ethernet_ip'].items():
                if isinstance(observation, torch.Tensor):
                    print(f"  {field_name} observation: shape {observation.shape}")
            
            # Agents select actions
            actions = agent_array.select_actions(observations['ethernet_ip'])
            
            # Show selected actions
            for field_name, action in actions.items():
                print(f"  {field_name}: action {action.item()}")
            
            # Step environment
            next_observations, reward, done, info = environment.step(
                {'ethernet_ip': actions}
            )
            
            print(f"  Reward: {reward:.4f}")
            
            observations = next_observations
        
        print("\n4. Example finished!")
        
    except Exception as e:
        print(f"Example error: {e}")
        raise

if __name__ == "__main__":
    run_ethernet_ip_example()