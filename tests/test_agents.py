import unittest
import torch
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.agent_array import AgentArray
from core.policy_network import PolicyNetwork
from core.value_network import ValueNetwork

class TestAgentArray(unittest.TestCase):

    def setUp(self):
        """测试设置"""
        self.protocol_name = 'modbus_tcp'
        self.field_config = {
            'function_code': {'state_dim': 10, 'action_dim': 5, 'mutation_actions': ['flip', 'delete']},
            'data': {'state_dim': 20, 'action_dim': 8, 'mutation_actions': ['flip', 'delete', 'duplicate']}
        }
        
        # 创建共享价值网络
        self.shared_value_network = ValueNetwork(state_dim=30, action_dim=13)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.agent_array = AgentArray(
            protocol_name=self.protocol_name,
            field_config=self.field_config,
            shared_value_network=self.shared_value_network,
            device=self.device
        )

    def test_agent_initialization(self):
        """测试智能体初始化"""
        self.assertEqual(self.agent_array.protocol_name, self.protocol_name)
        self.assertEqual(len(self.agent_array.agents), 2)
        
        # 检查每个字段都有对应的智能体
        field_names = [agent.field_name for agent in self.agent_array.agents]
        self.assertIn('function_code', field_names)
        self.assertIn('data', field_names)

    def test_action_selection(self):
        """测试动作选择"""
        observations = {
            'function_code': torch.randn(10),
            'data': torch.randn(20)
        }
        
        actions = self.agent_array.select_actions(observations)
        
        self.assertIn('function_code', actions)
        self.assertIn('data', actions)
        self.assertIsInstance(actions['function_code'], torch.Tensor)
        self.assertIsInstance(actions['data'], torch.Tensor)

    def test_global_observation(self):
        """测试全局观察"""
        individual_observations = {
            'function_code': torch.randn(10),
            'data': torch.randn(20)
        }
        
        global_obs = self.agent_array.get_global_observation(individual_observations)
        
        self.assertIsInstance(global_obs, torch.Tensor)
        self.assertEqual(global_obs.shape[0], 30)  # 10 + 20

class TestPolicyNetwork(unittest.TestCase):

    def setUp(self):
        self.input_dim = 10
        self.hidden_dims = [64, 32]
        self.output_dim = 5
        self.policy_net = PolicyNetwork(self.input_dim, self.hidden_dims, self.output_dim)

    def test_forward_pass(self):
        """测试前向传播"""
        batch_size = 4
        input_tensor = torch.randn(batch_size, self.input_dim)
        
        output = self.policy_net(input_tensor)
        
        self.assertEqual(output.shape, (batch_size, self.output_dim))
        # 检查输出是概率分布（和为1）
        self.assertTrue(torch.allclose(output.sum(dim=1), torch.ones(batch_size), atol=1e-6))

if __name__ == '__main__':
    unittest.main()