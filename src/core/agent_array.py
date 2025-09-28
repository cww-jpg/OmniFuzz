import torch
import torch.nn as nn
from typing import List, Dict, Any
from .protocol_agent import ProtocolAgent
from .policy_network import PolicyNetwork
from .value_network import ValueNetwork

class AgentArray:
    """协议专用的智能体数组"""
    
    def __init__(self, protocol_name: str, field_config: Dict[str, Any], 
                 shared_value_network: ValueNetwork, device: torch.device):
        self.protocol_name = protocol_name
        self.field_config = field_config
        self.shared_value_network = shared_value_network
        self.device = device
        
        # 为每个协议字段创建专用智能体
        self.agents = self._initialize_agents()
        
    def _initialize_agents(self) -> List[ProtocolAgent]:
        """初始化协议字段智能体"""
        agents = []
        for field_name, field_config in self.field_config.items():
            # 为每个字段创建独立的策略网络
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
        """为所有智能体选择动作"""
        actions = {}
        for agent in self.agents:
            obs = observations[agent.field_name]
            action = agent.select_action(obs)
            actions[agent.field_name] = action
            
        return actions
    
    def update_policies(self, experiences: List[Dict], global_reward: float):
        """更新所有智能体的策略"""
        for agent in self.agents:
            field_experiences = [
                exp for exp in experiences 
                if agent.field_name in exp['observations']
            ]
            if field_experiences:
                agent.update_policy(field_experiences, global_reward)
    
    def get_global_observation(self, individual_observations: Dict[str, torch.Tensor]) -> torch.Tensor:
        """合并所有智能体的观察为全局观察"""
        obs_list = []
        for agent in self.agents:
            if agent.field_name in individual_observations:
                obs_list.append(individual_observations[agent.field_name])
        
        return torch.cat(obs_list, dim=-1) if obs_list else torch.tensor([])