import torch
from typing import Dict, List, Any
import numpy as np

class RewardCalculator:
    """多目标奖励函数计算器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vulnerability_weights = config['rewards']['vulnerability_scores']
        self.reward_weights = config['rewards']['weights']
        
        # 记录已发现的漏洞类型用于多样性计算
        self.discovered_vulnerabilities = set()
        
    def calculate_reward(self, fuzzing_results: Dict[str, Any]) -> float:
        """计算综合奖励值"""
        
        # 漏洞发现数量奖励
        vuln_reward = self._calculate_vulnerability_reward(
            fuzzing_results['vulnerabilities']
        )
        
        # 深度路径探索奖励
        depth_reward = self._calculate_depth_reward(
            fuzzing_results['execution_depth']
        )
        
        # 漏洞多样性奖励
        diversity_reward = self._calculate_diversity_reward(
            fuzzing_results['vulnerability_types']
        )
        
        # 综合奖励（公式10）
        total_reward = (
            self.reward_weights['vulnerability'] * vuln_reward +
            self.reward_weights['depth'] * depth_reward +
            self.reward_weights['diversity'] * diversity_reward
        )
        
        return total_reward
    
    def _calculate_vulnerability_reward(self, vulnerabilities: List[Dict]) -> float:
        """计算漏洞发现数量奖励（公式6-7）"""
        total_score = 0
        
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'none')
            score = self.vulnerability_weights.get(severity, 0)
            
            # 根据论文，高危漏洞有3倍权重
            if severity == 'critical':
                score *= 3
            elif severity == 'major':
                score *= 2
                
            total_score += score
            
        return total_score
    
    def _calculate_depth_reward(self, execution_depth: Dict[str, float]) -> float:
        """计算深度路径探索奖励（公式8）"""
        if not execution_depth:
            return 0
            
        # 计算所有智能体的平均路径深度
        total_depth = sum(execution_depth.values())
        avg_depth = total_depth / len(execution_depth)
        
        return avg_depth
    
    def _calculate_diversity_reward(self, vulnerability_types: List[str]) -> float:
        """计算漏洞多样性奖励（公式9）"""
        # 更新已发现的漏洞类型
        for vuln_type in vulnerability_types:
            self.discovered_vulnerabilities.add(vuln_type)
            
        # 返回唯一漏洞类型数量
        return len(self.discovered_vulnerabilities)
    
    def reset_diversity_tracking(self):
        """重置多样性跟踪（用于新的训练周期）"""
        self.discovered_vulnerabilities.clear()