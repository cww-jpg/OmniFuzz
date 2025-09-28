"""
OmniFuzz: A Multi-Agent Reinforcement Learning Framework for Protocol-Aware Fuzzing in Power IoT Devices

This package provides a comprehensive fuzzing framework for power IoT devices
using multi-agent reinforcement learning to test multiple industrial protocols
concurrently.
"""

__version__ = "1.0.0"
__author__ = "Yubo Song, Weiwei Chen, et al."
__email__ = "songyubo@seu.edu.cn"
__description__ = "Multi-Agent Reinforcement Learning Framework for Protocol-Aware Fuzzing"

# 核心组件导出
from .core.agent_array import AgentArray
from .core.protocol_agent import ProtocolAgent
from .core.policy_network import PolicyNetwork, PolicyNetworkMLP
from .core.value_network import ValueNetwork, ValueNetworkMLP
from .core.experience_buffer import ExperienceBuffer, PrioritizedExperienceBuffer

# 环境组件导出
from .environment.power_iot_env import PowerIoTEnvironment
from .environment.protocol_parser import ProtocolParser
from .environment.device_interface import DeviceInterface

# 模糊测试组件导出
from .fuzzing.mutation_engine import MutationEngine, MutationAction
from .fuzzing.test_case_generator import TestCaseGenerator, TestCasePriority
from .fuzzing.coverage_tracker import CoverageTracker, LLVMCoverageTracker

# 训练组件导出
from .training.trainer import OmniFuzzTrainer
from .training.reward_calculator import RewardCalculator
from .training.multi_agent_coordinator import MultiAgentCoordinator

# 工具组件导出
from .utils.data_preprocessor import DataPreprocessor
from .utils.protocol_utils import ProtocolUtils
from .utils.monitoring import ResourceMonitor, PerformanceProfiler

# 评估组件导出
from .evaluation.metrics_calculator import MetricsCalculator
from .evaluation.baseline_comparison import BaselineComparator
from .evaluation.vulnerability_analyzer import VulnerabilityAnalyzer

__all__ = [
    # 核心组件
    'AgentArray', 'ProtocolAgent', 'PolicyNetwork', 'PolicyNetworkMLP',
    'ValueNetwork', 'ValueNetworkMLP', 'ExperienceBuffer', 'PrioritizedExperienceBuffer',
    
    # 环境组件
    'PowerIoTEnvironment', 'ProtocolParser', 'DeviceInterface',
    
    # 模糊测试组件
    'MutationEngine', 'MutationAction', 'TestCaseGenerator', 'TestCasePriority',
    'CoverageTracker', 'LLVMCoverageTracker',
    
    # 训练组件
    'OmniFuzzTrainer', 'RewardCalculator', 'MultiAgentCoordinator',
    
    # 工具组件
    'DataPreprocessor', 'ProtocolUtils', 'ResourceMonitor', 'PerformanceProfiler',
    
    # 评估组件
    'MetricsCalculator', 'BaselineComparator', 'VulnerabilityAnalyzer'
]