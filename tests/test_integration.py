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
        """设置集成测试环境"""
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
        """测试智能体与环境集成"""
        # 创建共享价值网络
        shared_value_network = ValueNetwork(state_dim=10, action_dim=5)
        
        # 创建智能体数组
        agent_array = AgentArray(
            protocol_name='modbus_tcp',
            field_config=self.config['protocols']['modbus_tcp']['fields'],
            shared_value_network=shared_value_network,
            device=self.device
        )
        
        # 创建环境
        environment = PowerIoTEnvironment(
            protocols=['modbus_tcp'],
            config=self.config
        )
        
        # 测试环境重置
        observations = environment.reset()
        self.assertIn('modbus_tcp', observations)
        
        # 测试动作选择
        actions = agent_array.select_actions(observations['modbus_tcp'])
        self.assertIn('function_code', actions)
        
        # 测试环境步骤
        next_observations, reward, done, info = environment.step(
            {'modbus_tcp': actions}
        )
        
        self.assertIsInstance(reward, float)
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)

    def test_reward_calculation_integration(self):
        """测试奖励计算集成"""
        reward_calculator = RewardCalculator(self.config)
        
        # 模拟模糊测试结果
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
        """测试训练循环集成"""
        # 这个测试验证各个组件能否协同工作
        # 在实际项目中，这里应该运行一个简化的训练循环
        
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
        
        # 运行简化的训练步骤
        observations = environment.reset()
        
        for step in range(10):  # 运行10步
            actions = agent_array.select_actions(observations['modbus_tcp'])
            next_observations, reward, done, info = environment.step(
                {'modbus_tcp': actions}
            )
            
            # 验证数据完整性
            self.assertIsInstance(reward, float)
            self.assertIsInstance(done, bool)
            
            observations = next_observations
            
            if done:
                break
        
        # 验证训练过程完成
        self.assertTrue(True)  # 如果没有异常抛出，测试通过

if __name__ == '__main__':
    unittest.main()