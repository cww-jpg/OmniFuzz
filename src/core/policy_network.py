import torch
import torch.nn as nn
import torch.nn.functional as F

class PolicyNetwork(nn.Module):
    """多层感知机策略网络"""
    
    def __init__(self, input_dim: int, hidden_dims: List[int], output_dim: int):
        super(PolicyNetwork, self).__init__()
        
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
            
        # 输出层
        layers.append(nn.Linear(prev_dim, output_dim))
        layers.append(nn.Softmax(dim=-1))
        
        self.network = nn.Sequential(*layers)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)
    
    def get_action_probabilities(self, state: torch.Tensor) -> torch.Tensor:
        """获取动作概率分布"""
        return self.forward(state)

class PolicyNetworkMLP(nn.Module):
    """论文中描述的三层感知机策略网络"""
    
    def __init__(self, input_dim: int, hidden1_dim: int = 64, 
                 hidden2_dim: int = 32, output_dim: int = 8):
        super(PolicyNetworkMLP, self).__init__()
        
        # 根据论文中的公式(11)-(14)
        self.W1 = nn.Linear(input_dim, hidden1_dim)
        self.b1 = nn.Parameter(torch.randn(hidden1_dim))
        self.W2 = nn.Linear(hidden1_dim, hidden2_dim)
        self.b2 = nn.Parameter(torch.randn(hidden2_dim))
        self.W3 = nn.Linear(hidden2_dim, output_dim)
        self.b3 = nn.Parameter(torch.randn(output_dim))
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # H^(1) = ReLU(XW_1 + b_1)
        h1 = F.relu(self.W1(x) + self.b1)
        # H^(2) = ReLU(H^(1)W_2 + b_2)
        h2 = F.relu(self.W2(h1) + self.b2)
        # O = H^(2)W_3 + b_3
        output = self.W3(h2) + self.b3
        
        return F.softmax(output, dim=-1)