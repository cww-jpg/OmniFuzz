import unittest
import torch
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.agent_array import AgentArray
from core.value_network import ValueNetwork
from environment.power_iot_env import PowerIoTEnvironment
from training.reward_calculator import RewardCalculator

class TestIntegration(unittest.TestCase):

    def setUp(self):
        """Set up integration test environment"""
        self.config = {
            'protocols': {
                'modbus_tcp': {
                    'fields': {
                        'function_code': {
                            'state_dim': 10,
                            'action_dim': 5,
                            'mutation_actions': ['flip', 'delete']
                        }
                    }
                }
            },
            'rewards': {
                'vulnerability_scores': {
                    'critical': 4.0,
                    'major': 3.0,
                    'minor': 2.0,
                    'general': 1.0,
                    'none': 0.0
                },
                'weights': {
                    'vulnerability': 0.5,
                    'depth': 0.25,
                    'diversity': 0.25
                }
            }
        }
        
        self.device = torch.device('cpu')

    def test_agent_environment_integration(self):
        """Test agent-environment integration"""
        # Create shared value network
        shared_value_network = ValueNetwork(state_dim=10, action_dim=5)
        
        # Create agent array
        agent_array = AgentArray(
            protocol_name='modbus_tcp',
            field_config=self.config['protocols']['modbus_tcp']['fields'],
            shared_value_network=shared_value_network,
            device=self.device
        )
        
        # Create environment
        environment = PowerIoTEnvironment(
            protocols=['modbus_tcp'],
            config=self.config
        )
        
        # Test environment reset
        observations = environment.reset()
        self.assertIn('modbus_tcp', observations)
        
        # Test action selection
        actions = agent_array.select_actions(observations['modbus_tcp'])
        self.assertIn('function_code', actions)
        
        # Test environment step
        next_observations, reward, done, info = environment.step(
            {'modbus_tcp': actions}
        )
        
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)

    def test_reward_calculation_integration(self):
        """Test reward calculation integration"""
        reward_calculator = RewardCalculator(self.config)
        
        # Simulate fuzzing results
        fuzzing_results = {
            'vulnerabilities': [
                {'severity': 'critical', 'type': 'buffer_overflow'},
                {'severity': 'minor', 'type': 'integer_overflow'}
            ],
            'execution_depth': {'agent1': 50, 'agent2': 30},
            'vulnerability_types': ['buffer_overflow', 'integer_overflow']
        }
        
        reward = reward_calculator.calculate_reward(fuzzing_results)
        
        self.assertIsInstance(reward, float)
        self.assertGreater(reward, 0)

    def test_training_loop_integration(self):
        """Test training loop integration"""
        # This test verifies components can work together
        # In a real project, a simplified training loop should run here
        
        shared_value_network = ValueNetwork(state_dim=10, action_dim=5)
        
        agent_array = AgentArray(
            protocol_name='modbus_tcp',
            field_config=self.config['protocols']['modbus_tcp']['fields'],
            shared_value_network=shared_value_network,
            device=self.device
        )
        
        environment = PowerIoTEnvironment(
            protocols=['modbus_tcp'],
            config=self.config
        )
        
        # Run simplified training steps
        observations = environment.reset()
        
        for step in range(10):  # run 10 steps
            actions = agent_array.select_actions(observations['modbus_tcp'])
            next_observations, reward, done, info = environment.step(
                {'modbus_tcp': actions}
            )
            
            # Validate data integrity
            self.assertIsInstance(reward, float)
            self.assertIsInstance(done, bool)
            
            observations = next_observations
            
            if done:
                break
        
        # Verify training completes
        self.assertTrue(True)  # Test passes if no exception is raised

if __name__ == '__main__':
    unittest.main()