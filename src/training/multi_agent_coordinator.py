import torch
import logging
from typing import Dict, List, Any, Tuple
import threading
from queue import Queue
import time

class MultiAgentCoordinator:
    """Multi-Agent Coordinator"""
    
    def __init__(self, agent_arrays: Dict, config: Dict[str, Any]):
        self.agent_arrays = agent_arrays
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Concurrency control
        self.max_workers = config.get('concurrent_threads', 4)
        self.task_queue = Queue()
        self.result_queue = Queue()
        
        # Coordination statistics
        self.coordination_stats = {
            'messages_processed': 0,
            'vulnerabilities_found': 0,
            'protocol_coverage': {},
            'agent_performance': {}
        }
    
    def coordinate_training(self, environment, num_episodes: int) -> Dict[str, Any]:
        """Coordinate multi-agent training"""
        self.logger.info("Starting multi-agent coordinated training")
        
        training_results = {}
        
        for episode in range(num_episodes):
            episode_result = self._run_coordinated_episode(environment, episode)
            training_results[episode] = episode_result
            
            # Update coordination statistics
            self._update_coordination_stats(episode_result)
            
            # Log progress
            if (episode + 1) % 10 == 0:
                self._log_coordination_progress(episode + 1, episode_result)
        
        return training_results
    
    def _run_coordinated_episode(self, environment, episode_idx: int) -> Dict[str, Any]:
        """Run coordinated training episode"""
        # Reset environment
        observations = environment.reset()
        total_reward = 0
        step_count = 0
        vulnerabilities_found = []
        
        while True:
            # Parallel execution of action selection for each protocol agent
            actions = self._parallel_action_selection(observations)
            
            # Execute environment step
            next_observations, reward, done, info = environment.step(actions)
            
            # Parallel agent update
            self._parallel_agent_update(observations, actions, reward, next_observations)
            
            # Update statistics
            total_reward += reward
            step_count += 1
            
            if 'vulnerabilities_found' in info:
                vulnerabilities_found.extend(info['vulnerabilities_found'])
            
            observations = next_observations
            
            if done or step_count >= 1000:
                break
        
        return {
            'episode': episode_idx,
            'total_reward': total_reward,
            'steps': step_count,
            'vulnerabilities_found': vulnerabilities_found,
            'protocol_performance': self._calculate_protocol_performance()
        }
    
    def _parallel_action_selection(self, observations: Dict) -> Dict[str, Dict]:
        """Parallel action selection"""
        actions = {}
        threads = []
        
        def select_actions_for_protocol(protocol, obs):
            try:
                if protocol in self.agent_arrays and protocol in obs:
                    protocol_actions = self.agent_arrays[protocol].select_actions(obs[protocol])
                    actions[protocol] = protocol_actions
            except Exception as e:
                self.logger.error(f"Protocol {protocol} action selection failed: {e}")
        
        # Create thread for each protocol
        for protocol in observations.keys():
            if protocol in self.agent_arrays:
                thread = threading.Thread(
                    target=select_actions_for_protocol,
                    args=(protocol, observations)
                )
                threads.append(thread)
                thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        return actions
    
    def _parallel_agent_update(self, observations: Dict, actions: Dict, 
                              reward: float, next_observations: Dict):
        """Parallel agent update"""
        threads = []
        
        def update_agents_for_protocol(protocol):
            try:
                if (protocol in self.agent_arrays and 
                    protocol in observations and 
                    protocol in next_observations):
                    
                    # Prepare experience data
                    experience = {
                        'observations': observations[protocol],
                        'actions': actions.get(protocol, {}),
                        'reward': reward,
                        'next_observations': next_observations[protocol],
                        'global_observation': self.agent_arrays[protocol].get_global_observation(
                            observations[protocol]
                        ),
                        'global_next_observation': self.agent_arrays[protocol].get_global_observation(
                            next_observations[protocol]
                        )
                    }
                    
                    # Update agents
                    self.agent_arrays[protocol].update_policies([experience], reward)
                    
            except Exception as e:
                self.logger.error(f"Protocol {protocol} agent update failed: {e}")
        
        # Create update thread for each protocol
        for protocol in self.agent_arrays.keys():
            thread = threading.Thread(target=update_agents_for_protocol, args=(protocol,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
    
    def _calculate_protocol_performance(self) -> Dict[str, float]:
        """Calculate protocol performance metrics"""
        performance = {}
        
        for protocol, agent_array in self.agent_arrays.items():
            # Calculate average reward (simplified implementation)
            total_reward = 0
            agent_count = 0
            
            for agent in agent_array.agents:
                # Should calculate actual performance metrics from agent experiences here
                total_reward += 1.0  # placeholder value
                agent_count += 1
            
            performance[protocol] = total_reward / agent_count if agent_count > 0 else 0
        
        return performance
    
    def _update_coordination_stats(self, episode_result: Dict[str, Any]):
        """Update coordination statistics"""
        self.coordination_stats['messages_processed'] += episode_result.get('steps', 0)
        self.coordination_stats['vulnerabilities_found'] += len(
            episode_result.get('vulnerabilities_found', [])
        )
        
        # Update protocol coverage statistics
        protocol_perf = episode_result.get('protocol_performance', {})
        for protocol, perf in protocol_perf.items():
            if protocol not in self.coordination_stats['protocol_coverage']:
                self.coordination_stats['protocol_coverage'][protocol] = []
            self.coordination_stats['protocol_coverage'][protocol].append(perf)
    
    def _log_coordination_progress(self, episode: int, episode_result: Dict[str, Any]):
        """Log coordination progress"""
        total_reward = episode_result.get('total_reward', 0)
        vulnerabilities = len(episode_result.get('vulnerabilities_found', []))
        
        self.logger.info(
            f"Coordination training progress - Episode {episode:4d} | "
            f"Total reward: {total_reward:8.2f} | "
            f"Vulnerabilities found: {vulnerabilities:3d} | "
            f"Protocol performance: {episode_result.get('protocol_performance', {})}"
        )
    
    def get_coordination_insights(self) -> Dict[str, Any]:
        """Get coordination insights"""
        insights = {
            'total_messages': self.coordination_stats['messages_processed'],
            'total_vulnerabilities': self.coordination_stats['vulnerabilities_found'],
            'protocol_performance': {},
            'coordination_efficiency': self._calculate_coordination_efficiency()
        }
        
        # Calculate average performance for each protocol
        for protocol, performances in self.coordination_stats['protocol_coverage'].items():
            if performances:
                insights['protocol_performance'][protocol] = {
                    'average_performance': sum(performances) / len(performances),
                    'stability': self._calculate_performance_stability(performances),
                    'trend': self._calculate_performance_trend(performances)
                }
        
        return insights
    
    def _calculate_coordination_efficiency(self) -> float:
        """Calculate coordination efficiency"""
        total_steps = self.coordination_stats['messages_processed']
        vulnerabilities = self.coordination_stats['vulnerabilities_found']
        
        if total_steps == 0:
            return 0.0
        
        # Efficiency = number of vulnerabilities found / total steps
        return vulnerabilities / total_steps
    
    def _calculate_performance_stability(self, performances: List[float]) -> float:
        """Calculate performance stability"""
        if len(performances) < 2:
            return 1.0
        
        mean_perf = sum(performances) / len(performances)
        variance = sum((p - mean_perf) ** 2 for p in performances) / len(performances)
        
        # Stability = 1 / (1 + variance)
        return 1.0 / (1.0 + variance)
    
    def _calculate_performance_trend(self, performances: List[float]) -> str:
        """Calculate performance trend"""
        if len(performances) < 2:
            return "stable"
        
        # Use simple linear regression to determine trend
        recent_performances = performances[-10:]  # Last 10 episodes
        if len(recent_performances) < 2:
            return "stable"
        
        x = list(range(len(recent_performances)))
        y = recent_performances
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"