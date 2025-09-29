import torch
import torch.nn as nn
from typing import List, Dict, Any
from .protocol_agent import ProtocolAgent
from .policy_network import PolicyNetwork
from .value_network import ValueNetwork

class AgentArray:
    """Protocol-specific agent array"""
    
    def __init__(self, protocol_name: str, field_config: Dict[str, Any], 
                 shared_value_network: ValueNetwork, device: torch.device):
        self.protocol_name = protocol_name
        self.field_config = field_config
        self.shared_value_network = shared_value_network
        self.device = device
        
        # Create a dedicated agent for each protocol field
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> List[ProtocolAgent]:
        """Initialize protocol-field agents"""
        agents = []
        for field_name, field_config in self.field_config.items():
            # Create a separate policy network for each field
            policy_net = PolicyNetwork(
                input_dim=field_config['state_dim'],
                hidden_dims=[64, 32],
                output_dim=field_config['action_dim']
            ).to(self.device)
            
            agent = ProtocolAgent(
                field_name=field_name,
                policy_network=policy_net,
                value_network=self.shared_value_network,
                mutation_actions=field_config['mutation_actions']
            )
            agents.append(agent)
            
        return agents
    
    def select_actions(self, observations: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Select actions for all agents"""
        actions = {}
        for agent in self.agents:
            obs = observations[agent.field_name]
            action = agent.select_action(obs)
            actions[agent.field_name] = action
            
        return actions
    
    def update_policies(self, experiences: List[Dict], global_reward: float):
        """Update policies for all agents"""
        for agent in self.agents:
            field_experiences = [
                exp for exp in experiences 
                if agent.field_name in exp['observations']
            ]
            if field_experiences:
                agent.update_policy(field_experiences, global_reward)
    
    def get_global_observation(self, individual_observations: Dict[str, torch.Tensor]) -> torch.Tensor:
        """Combine all agent observations into a global observation"""
        obs_list = []
        for agent in self.agents:
            if agent.field_name in individual_observations:
                obs_list.append(individual_observations[agent.field_name])
        
        return torch.cat(obs_list, dim=-1) if obs_list else torch.tensor([])