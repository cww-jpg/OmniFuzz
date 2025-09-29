import torch
from typing import Dict, List, Any
import numpy as np

class RewardCalculator:
    """Multi-objective Reward Function Calculator"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vulnerability_weights = config['rewards']['vulnerability_scores']
        self.reward_weights = config['rewards']['weights']
        
        # Track discovered vulnerability types for diversity calculation
        self.discovered_vulnerabilities = set()
        
    def calculate_reward(self, fuzzing_results: Dict[str, Any]) -> float:
        """Calculate comprehensive reward value"""
        
        # Vulnerability discovery reward
        vuln_reward = self._calculate_vulnerability_reward(
            fuzzing_results['vulnerabilities']
        )
        
        # Deep path exploration reward
        depth_reward = self._calculate_depth_reward(
            fuzzing_results['execution_depth']
        )
        
        # Vulnerability diversity reward
        diversity_reward = self._calculate_diversity_reward(
            fuzzing_results['vulnerability_types']
        )
        
        # Comprehensive reward (Equation 10)
        total_reward = (
            self.reward_weights['vulnerability'] * vuln_reward +
            self.reward_weights['depth'] * depth_reward +
            self.reward_weights['diversity'] * diversity_reward
        )
        
        return total_reward
    
    def _calculate_vulnerability_reward(self, vulnerabilities: List[Dict]) -> float:
        """Calculate vulnerability discovery reward (Equations 6-7)"""
        total_score = 0
        
        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'none')
            score = self.vulnerability_weights.get(severity, 0)
            
            # According to the paper, high-risk vulnerabilities have 3x weight
            if severity == 'critical':
                score *= 3
            elif severity == 'major':
                score *= 2
                
            total_score += score
            
        return total_score
    
    def _calculate_depth_reward(self, execution_depth: Dict[str, float]) -> float:
        """Calculate deep path exploration reward (Equation 8)"""
        if not execution_depth:
            return 0
            
        # Calculate average path depth for all agents
        total_depth = sum(execution_depth.values())
        avg_depth = total_depth / len(execution_depth)
        
        return avg_depth
    
    def _calculate_diversity_reward(self, vulnerability_types: List[str]) -> float:
        """Calculate vulnerability diversity reward (Equation 9)"""
        # Update discovered vulnerability types
        for vuln_type in vulnerability_types:
            self.discovered_vulnerabilities.add(vuln_type)
            
        # Return the number of unique vulnerability types
        return len(self.discovered_vulnerabilities)
    
    def reset_diversity_tracking(self):
        """Reset diversity tracking (for new training episodes)"""
        self.discovered_vulnerabilities.clear()