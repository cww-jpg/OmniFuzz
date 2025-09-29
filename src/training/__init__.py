"""
Training module - multi-agent training and coordination

Includes trainer, reward calculator, multi-agent coordinator
"""

from .trainer import OmniFuzzTrainer
from .reward_calculator import RewardCalculator
from .multi_agent_coordinator import MultiAgentCoordinator

__all__ = [
    'OmniFuzzTrainer',
    'RewardCalculator',
    'MultiAgentCoordinator'
]
