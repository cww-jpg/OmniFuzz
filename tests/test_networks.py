import unittest
import torch
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.policy_network import PolicyNetwork, PolicyNetworkMLP
from core.value_network import ValueNetwork, ValueNetworkMLP

class TestPolicyNetwork(unittest.TestCase):

    def setUp(self):
        self.input_dim = 10
        self.hidden_dims = [64, 32]
        self.output_dim = 5
        self.policy_net = PolicyNetwork(self.input_dim, self.hidden_dims, self.output_dim)

    def test_forward_pass(self):
        """Test forward pass"""
        batch_size = 4
        input_tensor = torch.randn(batch_size, self.input_dim)
        
        output = self.policy_net(input_tensor)
        
        self.assertEqual(output.shape, (batch_size, self.output_dim))
        # Check output is a probability distribution (sums to 1)
        self.assertTrue(torch.allclose(output.sum(dim=1), torch.ones(batch_size), atol=1e-6))

    def test_action_probabilities(self):
        """Test action probability calculation"""
        state = torch.randn(1, self.input_dim)
        action_probs = self.policy_net.get_action_probabilities(state)
        
        self.assertEqual(action_probs.shape, (1, self.output_dim))
        self.assertAlmostEqual(action_probs.sum().item(), 1.0, places=6)

class TestPolicyNetworkMLP(unittest.TestCase):

    def setUp(self):
        self.input_dim = 1000
        self.policy_net = PolicyNetworkMLP(
            input_dim=self.input_dim,
            hidden1_dim=64,
            hidden2_dim=32,
            output_dim=8
        )

    def test_forward_pass(self):
        """Test MLP forward pass"""
        batch_size = 128
        input_tensor = torch.randn(batch_size, self.input_dim)
        
        output = self.policy_net(input_tensor)
        
        self.assertEqual(output.shape, (batch_size, 8))
        self.assertTrue(torch.allclose(output.sum(dim=1), torch.ones(batch_size), atol=1e-6))

class TestValueNetwork(unittest.TestCase):

    def setUp(self):
        self.state_dim = 100
        self.action_dim = 10
        self.value_net = ValueNetwork(self.state_dim, self.action_dim)

    def test_forward_pass(self):
        """Test value network forward pass"""
        batch_size = 4
        state = torch.randn(batch_size, self.state_dim)
        actions = torch.randn(batch_size, self.action_dim)
        
        value = self.value_net(state, actions)
        
        self.assertEqual(value.shape, (batch_size, 1))

class TestValueNetworkMLP(unittest.TestCase):

    def setUp(self):
        self.input_dim = 100  # state dim + action dim
        self.value_net = ValueNetworkMLP(
            input_dim=self.input_dim,
            hidden1_dim=64,
            hidden2_dim=32,
            output_dim=1
        )

    def test_forward_pass(self):
        """Test MLP value network forward pass"""
        batch_size = 128
        global_obs = torch.randn(batch_size, 50)  # 50-dim state
        global_actions = torch.randn(batch_size, 50)  # 50-dim action
        
        value = self.value_net(global_obs, global_actions)
        
        self.assertEqual(value.shape, (batch_size, 1))

if __name__ == '__main__':
    unittest.main()