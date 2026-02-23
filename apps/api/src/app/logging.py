"""
Logging configuration — delegates to libs/observability.

Kept as a thin wrapper for backward compatibility.
"""
from packages.observability import setup_logging, get_logger

__all__ = ["setup_logging", "get_logger"]
