"""
Evaluation module - performance evaluation and baseline comparison

Includes metrics calculator, baseline comparator, vulnerability analyzer
"""

from .metrics_calculator import MetricsCalculator
from .baseline_comparison import BaselineComparator
from .vulnerability_analyzer import VulnerabilityAnalyzer

__all__ = [
    'MetricsCalculator',
    'BaselineComparator',
    'VulnerabilityAnalyzer'
]
