import torch
import torch.nn as nn
import numpy as np
import logging
from typing import Dict, List, Any, Tuple
from pathlib import Path

from src.core.experience_buffer import ExperienceBuffer
from src.training.reward_calculator import RewardCalculator

class OmniFuzzTrainer:
    """OmniFuzz Trainer"""
    
    def __init__(self, agent_arrays: Dict, environment: Any, 
                 config: Dict[str, Any], device: torch.device):
        self.agent_arrays = agent_arrays
        self.environment = environment
        self.config = config
        self.device = device
        
        self.logger = logging.getLogger(__name__)
        self.reward_calculator = RewardCalculator(config)
        
        # Experience buffers
        self.experience_buffers = {
            protocol: ExperienceBuffer(config['training']['buffer_size'])
            for protocol in agent_arrays.keys()
        }
        
        # Training statistics
        self.training_stats = {
            'episode_rewards': [],
            'vulnerabilities_found': [],
            'coverage_scores': []
        }
    
    def train(self, num_episodes: int) -> Dict[str, Any]:
        """Training main loop"""
        
        self.logger.info(f"Starting training, total {num_episodes} episodes")
        
        for episode in range(num_episodes):
            episode_stats = self._run_episode(episode)
            
            # Record statistics
            self.training_stats['episode_rewards'].append(episode_stats['total_reward'])
            self.training_stats['vulnerabilities_found'].append(episode_stats['vulnerabilities_found'])
            self.training_stats['coverage_scores'].append(episode_stats['avg_coverage'])
            
            # Log progress
            if (episode + 1) % 10 == 0:
                self._log_progress(episode + 1, episode_stats)
                
            # Early stopping check
            if self._check_early_stopping(episode_stats):
                self.logger.info(f"Early stopping at episode {episode + 1}")
                break
        
        return self._compile_training_results()
    
    def _run_episode(self, episode_idx: int) -> Dict[str, Any]:
        """Run a training episode"""
        
        # Reset environment
        observations = self.environment.reset()
        total_reward = 0
        step_count = 0
        vulnerabilities_found = []
        
        # Reset diversity tracking
        self.reward_calculator.reset_diversity_tracking()
        
        while True:
            # Agents select actions
            actions = {}
            for protocol, agent_array in self.agent_arrays.items():
                if protocol in observations:
                    protocol_actions = agent_array.select_actions(observations[protocol])
                    actions[protocol] = protocol_actions
            
            # Execute actions
            next_observations, reward, done, info = self.environment.step(actions)
            
            # Store experiences
            self._store_experiences(observations, actions, reward, next_observations, done)
            
            # Update agents
            if step_count % 10 == 0:  # Update every 10 steps
                self._update_agents(reward)
            
            # Update statistics
            total_reward += reward
            step_count += 1
            
            if 'vulnerabilities_found' in info:
                vulnerabilities_found.extend(info['vulnerabilities_found'])
            
            observations = next_observations
            
            if done or step_count >= 1000:  # Maximum steps
                break
        
        return {
            'total_reward': total_reward,
            'steps': step_count,
            'vulnerabilities_found': len(vulnerabilities_found),
            'avg_coverage': self._calculate_average_coverage(info)
        }
    
    def _store_experiences(self, observations: Dict, actions: Dict, 
                          reward: float, next_observations: Dict, done: bool):
        """Store experiences in buffers"""
        
        for protocol, agent_array in self.agent_arrays.items():
            if protocol in observations and protocol in next_observations:
                # Get global observations and actions
                global_obs = agent_array.get_global_observation(observations[protocol])
                global_next_obs = agent_array.get_global_observation(next_observations[protocol])
                global_actions = torch.cat([
                    actions[protocol][field] for field in actions[protocol]
                ]) if protocol in actions else torch.tensor([])
                
                experience = {
                    'observations': observations[protocol],
                    'actions': actions.get(protocol, {}),
                    'reward': reward,
                    'next_observations': next_observations[protocol],
                    'global_observation': global_obs,
                    'global_next_observation': global_next_obs,
                    'global_actions': global_actions,
                    'done': done
                }
                
                self.experience_buffers[protocol].add(experience)
    
    def _update_agents(self, global_reward: float):
        """Update all agents"""
        
        for protocol, agent_array in self.agent_arrays.items():
            buffer = self.experience_buffers[protocol]
            
            if len(buffer) >= self.config['training']['batch_size']:
                # Sample batch experiences
                batch = buffer.sample(self.config['training']['batch_size'])
                
                # Update agent policies
                agent_array.update_policies(batch, global_reward)
    
    def _calculate_average_coverage(self, info: Dict) -> float:
        """Calculate average code coverage"""
        if 'execution_depth' in info and info['execution_depth']:
            return sum(info['execution_depth'].values()) / len(info['execution_depth'])
        return 0.0
    
    def _log_progress(self, episode: int, stats: Dict[str, Any]):
        """Log training progress"""
        self.logger.info(
            f"Episode {episode:4d} | "
            f"Reward: {stats['total_reward']:8.2f} | "
            f"Vulnerabilities: {stats['vulnerabilities_found']:3d} | "
            f"Coverage: {stats['avg_coverage']:6.2f}%"
        )
    
    def _check_early_stopping(self, stats: Dict[str, Any]) -> bool:
        """Check if early stopping should be applied"""
        # Stop if there's no improvement for consecutive episodes
        if len(self.training_stats['episode_rewards']) < 20:
            return False
            
        recent_rewards = self.training_stats['episode_rewards'][-20:]
        if max(recent_rewards) == recent_rewards[0] and stats['total_reward'] <= recent_rewards[0]:
            return True
            
        return False
    
    def _compile_training_results(self) -> Dict[str, Any]:
        """Compile training results"""
        rewards = self.training_stats['episode_rewards']
        vulnerabilities = self.training_stats['vulnerabilities_found']
        coverages = self.training_stats['coverage_scores']
        
        return {
            'final_reward': rewards[-1] if rewards else 0,
            'max_reward': max(rewards) if rewards else 0,
            'avg_reward': np.mean(rewards) if rewards else 0,
            'total_vulnerabilities': sum(vulnerabilities),
            'avg_coverage': np.mean(coverages) if coverages else 0,
            'training_episodes': len(rewards)
        }
    
    def save_models(self, save_dir: str):
        """Save trained models"""
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        for protocol, agent_array in self.agent_arrays.items():
            protocol_save_path = save_path / protocol
            protocol_save_path.mkdir(exist_ok=True)
            
            # Save each agent's policy network
            for i, agent in enumerate(agent_array.agents):
                model_path = protocol_save_path / f"agent_{agent.field_name}.pth"
                torch.save(agent.policy_network.state_dict(), model_path)
            
            # Save shared value network
            value_net_path = protocol_save_path / "value_network.pth"
            torch.save(agent_array.shared_value_network.state_dict(), value_net_path)
        
        self.logger.info(f"Models saved to: {save_dir}")
    
    def load_models(self, load_dir: str):
        """Load pre-trained models"""
        load_path = Path(load_dir)
        
        for protocol, agent_array in self.agent_arrays.items():
            protocol_load_path = load_path / protocol
            
            if protocol_load_path.exists():
                # Load each agent's policy network
                for agent in agent_array.agents:
                    model_path = protocol_load_path / f"agent_{agent.field_name}.pth"
                    if model_path.exists():
                        agent.policy_network.load_state_dict(torch.load(model_path))
                
                # Load shared value network
                value_net_path = protocol_load_path / "value_network.pth"
                if value_net_path.exists():
                    agent_array.shared_value_network.load_state_dict(torch.load(value_net_path))
        
        self.logger.info(f"Models loaded from {load_dir}")