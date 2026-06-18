"""Data Analyst Claude - Inteligentní data analysis tool"""

from .analyzer import DataAnalyzer
from .gads import GoogleAdsConnector
from .ai import ClaudeAnalyst
from .utils import format_statistics, detect_anomalies

__version__ = "0.1.0"
__all__ = [
    "DataAnalyzer",
    "GoogleAdsConnector",
    "ClaudeAnalyst",
    "format_statistics",
    "detect_anomalies",
]
