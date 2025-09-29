#!/usr/bin/env python3
"""
OmniFuzz main training script
Protocol-aware fuzzing framework for power IoT devices based on multi-agent reinforcement learning
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
    """Configure logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('omnifuzz_training.log'),
            logging.StreamHandler()
        ]
    )

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def main():
    parser = argparse.ArgumentParser(description='OmniFuzz training script')
    parser.add_argument('--config', type=str, default='config/default_config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--protocols', nargs='+', 
                       default=['modbus_tcp', 'ethernet_ip', 'siemens_s7'],
                       help='List of protocols to train')
    parser.add_argument('--episodes', type=int, default=200,
                       help='Number of training episodes')
    parser.add_argument('--device', type=str, default='cuda',
                       help='Training device (cuda/cpu)')
    
    args = parser.parse_args()
    
    # Configure logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load config
    config = load_config(args.config)
    logger.info(f"Loaded config file: {args.config}")
    
    # Select device
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    try:
        # Initialize components
        logger.info("Initializing OmniFuzz components...")
        
        # Data preprocessing
        preprocessor = DataPreprocessor()
        
        # Create environment
        environment = PowerIoTEnvironment(
            protocols=args.protocols,
            config=config
        )
        
        # Create shared value networks
        shared_value_networks = {}
        for protocol in args.protocols:
            state_dim = config['protocols'][protocol].get('state_dim', 1000)
            action_dim = config['protocols'][protocol].get('action_dim', 8)
            shared_value_networks[protocol] = ValueNetwork(
                state_dim=state_dim,
                action_dim=action_dim
            ).to(device)
        
        # Create agent arrays
        agent_arrays = {}
        for protocol in args.protocols:
            protocol_config = config['protocols'][protocol]
            agent_arrays[protocol] = AgentArray(
                protocol_name=protocol,
                field_config=protocol_config['fields'],
                shared_value_network=shared_value_networks[protocol],
                device=device
            )
        
        # Create trainer
        trainer = OmniFuzzTrainer(
            agent_arrays=agent_arrays,
            environment=environment,
            config=config,
            device=device
        )
        
        logger.info("Start training...")
        
        # Training loop
        training_results = trainer.train(num_episodes=args.episodes)
        
        logger.info("Training completed!")
        
        # Save models
        trainer.save_models('models/')
        logger.info("Models saved to models/ directory")
        
        # Output training results
        logger.info(f"Final reward: {training_results['final_reward']:.4f}")
        logger.info(f"Vulnerabilities found: {training_results['vulnerabilities_found']}")
        logger.info(f"Average code coverage: {training_results['avg_coverage']:.2f}%")
        
    except Exception as e:
        logger.error(f"Error during training: {e}")
        raise

if __name__ == "__main__":
    main()