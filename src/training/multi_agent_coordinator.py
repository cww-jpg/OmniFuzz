import torch
import logging
from typing import Dict, List, Any, Tuple
import threading
from queue import Queue
import time

class MultiAgentCoordinator:
    """多智能体协调器"""
    
    def __init__(self, agent_arrays: Dict, config: Dict[str, Any]):
        self.agent_arrays = agent_arrays
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 并发控制
        self.max_workers = config.get('concurrent_threads', 4)
        self.task_queue = Queue()
        self.result_queue = Queue()
        
        # 协调统计
        self.coordination_stats = {
            'messages_processed': 0,
            'vulnerabilities_found': 0,
            'protocol_coverage': {},
            'agent_performance': {}
        }
    
    def coordinate_training(self, environment, num_episodes: int) -> Dict[str, Any]:
        """协调多智能体训练"""
        self.logger.info("开始多智能体协调训练")
        
        training_results = {}
        
        for episode in range(num_episodes):
            episode_result = self._run_coordinated_episode(environment, episode)
            training_results[episode] = episode_result
            
            # 更新协调统计
            self._update_coordination_stats(episode_result)
            
            # 输出进度
            if (episode + 1) % 10 == 0:
                self._log_coordination_progress(episode + 1, episode_result)
        
        return training_results
    
    def _run_coordinated_episode(self, environment, episode_idx: int) -> Dict[str, Any]:
        """运行协调的训练周期"""
        # 重置环境
        observations = environment.reset()
        total_reward = 0
        step_count = 0
        vulnerabilities_found = []
        
        while True:
            # 并行执行各协议智能体的动作选择
            actions = self._parallel_action_selection(observations)
            
            # 执行环境步骤
            next_observations, reward, done, info = environment.step(actions)
            
            # 并行更新智能体
            self._parallel_agent_update(observations, actions, reward, next_observations)
            
            # 更新统计
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
        """并行执行动作选择"""
        actions = {}
        threads = []
        
        def select_actions_for_protocol(protocol, obs):
            try:
                if protocol in self.agent_arrays and protocol in obs:
                    protocol_actions = self.agent_arrays[protocol].select_actions(obs[protocol])
                    actions[protocol] = protocol_actions
            except Exception as e:
                self.logger.error(f"协议 {protocol} 动作选择失败: {e}")
        
        # 为每个协议创建线程
        for protocol in observations.keys():
            if protocol in self.agent_arrays:
                thread = threading.Thread(
                    target=select_actions_for_protocol,
                    args=(protocol, observations)
                )
                threads.append(thread)
                thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        return actions
    
    def _parallel_agent_update(self, observations: Dict, actions: Dict, 
                              reward: float, next_observations: Dict):
        """并行更新智能体"""
        threads = []
        
        def update_agents_for_protocol(protocol):
            try:
                if (protocol in self.agent_arrays and 
                    protocol in observations and 
                    protocol in next_observations):
                    
                    # 准备经验数据
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
                    
                    # 更新智能体
                    self.agent_arrays[protocol].update_policies([experience], reward)
                    
            except Exception as e:
                self.logger.error(f"协议 {protocol} 智能体更新失败: {e}")
        
        # 为每个协议创建更新线程
        for protocol in self.agent_arrays.keys():
            thread = threading.Thread(target=update_agents_for_protocol, args=(protocol,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
    
    def _calculate_protocol_performance(self) -> Dict[str, float]:
        """计算各协议性能指标"""
        performance = {}
        
        for protocol, agent_array in self.agent_arrays.items():
            # 计算平均奖励（简化实现）
            total_reward = 0
            agent_count = 0
            
            for agent in agent_array.agents:
                # 这里应该从智能体的经验中计算实际性能指标
                total_reward += 1.0  # 占位值
                agent_count += 1
            
            performance[protocol] = total_reward / agent_count if agent_count > 0 else 0
        
        return performance
    
    def _update_coordination_stats(self, episode_result: Dict[str, Any]):
        """更新协调统计信息"""
        self.coordination_stats['messages_processed'] += episode_result.get('steps', 0)
        self.coordination_stats['vulnerabilities_found'] += len(
            episode_result.get('vulnerabilities_found', [])
        )
        
        # 更新协议覆盖统计
        protocol_perf = episode_result.get('protocol_performance', {})
        for protocol, perf in protocol_perf.items():
            if protocol not in self.coordination_stats['protocol_coverage']:
                self.coordination_stats['protocol_coverage'][protocol] = []
            self.coordination_stats['protocol_coverage'][protocol].append(perf)
    
    def _log_coordination_progress(self, episode: int, episode_result: Dict[str, Any]):
        """记录协调进度"""
        total_reward = episode_result.get('total_reward', 0)
        vulnerabilities = len(episode_result.get('vulnerabilities_found', []))
        
        self.logger.info(
            f"协调训练进度 - 周期 {episode:4d} | "
            f"总奖励: {total_reward:8.2f} | "
            f"漏洞发现: {vulnerabilities:3d} | "
            f"协议性能: {episode_result.get('protocol_performance', {})}"
        )
    
    def get_coordination_insights(self) -> Dict[str, Any]:
        """获取协调洞察"""
        insights = {
            'total_messages': self.coordination_stats['messages_processed'],
            'total_vulnerabilities': self.coordination_stats['vulnerabilities_found'],
            'protocol_performance': {},
            'coordination_efficiency': self._calculate_coordination_efficiency()
        }
        
        # 计算各协议平均性能
        for protocol, performances in self.coordination_stats['protocol_coverage'].items():
            if performances:
                insights['protocol_performance'][protocol] = {
                    'average_performance': sum(performances) / len(performances),
                    'stability': self._calculate_performance_stability(performances),
                    'trend': self._calculate_performance_trend(performances)
                }
        
        return insights
    
    def _calculate_coordination_efficiency(self) -> float:
        """计算协调效率"""
        total_steps = self.coordination_stats['messages_processed']
        vulnerabilities = self.coordination_stats['vulnerabilities_found']
        
        if total_steps == 0:
            return 0.0
        
        # 效率 = 漏洞发现数量 / 总步数
        return vulnerabilities / total_steps
    
    def _calculate_performance_stability(self, performances: List[float]) -> float:
        """计算性能稳定性"""
        if len(performances) < 2:
            return 1.0
        
        mean_perf = sum(performances) / len(performances)
        variance = sum((p - mean_perf) ** 2 for p in performances) / len(performances)
        
        # 稳定性 = 1 / (1 + 方差)
        return 1.0 / (1.0 + variance)
    
    def _calculate_performance_trend(self, performances: List[float]) -> str:
        """计算性能趋势"""
        if len(performances) < 2:
            return "stable"
        
        # 使用简单线性回归判断趋势
        recent_performances = performances[-10:]  # 最近10个周期
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