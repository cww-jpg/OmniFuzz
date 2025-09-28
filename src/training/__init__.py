"""
训练模块 - 多智能体训练和协调

包含训练器、奖励计算器、多智能体协调器等组件
"""

from .trainer import OmniFuzzTrainer
from .reward_calculator import RewardCalculator
from .multi_agent_coordinator import MultiAgentCoordinator

__all__ = [
    'OmniFuzzTrainer',
    'RewardCalculator',
    'MultiAgentCoordinator'
]
