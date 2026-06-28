"""Marketing Dashboard - inteligentní nástroj pro analýzu marketingových dat"""

from .analyzer import DataAnalyzer
try:
    from .gads import GoogleAdsConnector
except ImportError:  # google-ads je volitelná závislost
    GoogleAdsConnector = None
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
