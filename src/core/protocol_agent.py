import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Any
from .policy_network import PolicyNetwork
from .value_network import ValueNetwork

class ProtocolAgent:
    """Protocol-field-specific agent"""
    
    def __init__(self, field_name: str, policy_network: PolicyNetwork, 
                 value_network: ValueNetwork, mutation_actions: List[str]):
        self.field_name = field_name
        self.policy_network = policy_network
        self.value_network = value_network
        self.mutation_actions = mutation_actions
        self.optimizer = torch.optim.Adam(
            self.policy_network.parameters(), 
            lr=0.01
        )
        
    def select_action(self, observation: torch.Tensor) -> torch.Tensor:
        """Select action based on current observation"""
        with torch.no_grad():
            action_probs = self.policy_network(observation)
            action_dist = torch.distributions.Categorical(action_probs)
            action = action_dist.sample()
            
        return action
    
    def update_policy(self, experiences: List[Dict], global_reward: float):
        """Update policy network using experiences"""
        if not experiences:
            return
            
        # Compute policy gradient
        policy_loss = 0
        for exp in experiences:
            obs = exp['observations'][self.field_name]
            action = exp['actions'][self.field_name]
            value = self.value_network(
                exp['global_observation'], 
                exp['global_actions']
            )
            
            # Compute advantage
            advantage = global_reward - value
            
            # Compute policy loss
            action_probs = self.policy_network(obs)
            log_prob = torch.log(action_probs[action])
            policy_loss += -log_prob * advantage
            
        # Backpropagation
        self.optimizer.zero_grad()
        policy_loss.backward()
        self.optimizer.step()