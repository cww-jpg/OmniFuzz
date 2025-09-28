import torch
import torch.nn as nn
import torch.nn.functional as F

class ValueNetwork(nn.Module):
    """共享价值网络"""
    
    def __init__(self, state_dim: int, action_dim: int, 
                 hidden_dims: List[int] = [128, 64]):
        super(ValueNetwork, self).__init__()
        
        self.state_dim = state_dim
        self.action_dim = action_dim
        input_dim = state_dim + action_dim
        
        layers = []
        prev_dim = input_dim
        
        # 构建隐藏层
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(0.1)
            ])
            prev_dim = hidden_dim
            
        # 输出层 - 为每个智能体输出价值分数
        layers.append(nn.Linear(prev_dim, 1))
        
        self.network = nn.Sequential(*layers)
        
    def forward(self, state: torch.Tensor, actions: torch.Tensor) -> torch.Tensor:
        # 合并状态和动作
        x = torch.cat([state, actions], dim=-1)
        return self.network(x)

class ValueNetworkMLP(nn.Module):
    """论文中描述的多层感知机价值网络"""
    
    def __init__(self, input_dim: int, hidden1_dim: int = 64, 
                 hidden2_dim: int = 32, output_dim: int = 1):
        super(ValueNetworkMLP, self).__init__()
        
        # 根据论文中的描述扩展输入维度
        self.W1 = nn.Linear(input_dim, hidden1_dim)
        self.b1 = nn.Parameter(torch.randn(hidden1_dim))
        self.W2 = nn.Linear(hidden1_dim, hidden2_dim)
        self.b2 = nn.Parameter(torch.randn(hidden2_dim))
        self.W3 = nn.Linear(hidden2_dim, output_dim)
        self.b3 = nn.Parameter(torch.randn(output_dim))
        
    def forward(self, global_obs: torch.Tensor, global_actions: torch.Tensor) -> torch.Tensor:
        # 合并全局观察和动作
        x = torch.cat([global_obs, global_actions], dim=-1)
        
        # H^(1) = ReLU(XW_1 + b_1)
        h1 = F.relu(self.W1(x) + self.b1)
        # H^(2) = ReLU(H^(1)W_2 + b_2)
        h2 = F.relu(self.W2(h1) + self.b2)
        # V = H^(2)W_3 + b_3
        value = self.W3(h2) + self.b3
        
        return value