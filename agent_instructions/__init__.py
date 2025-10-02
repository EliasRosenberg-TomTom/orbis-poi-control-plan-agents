"""
Agent Instructions Package

This package contains instruction templates and configuration for different types of agents
in the APR analysis system.

Available instruction functions:
- build_metric_agent_instructions: Creates instructions for metric-specific agents (PAV, PPA, SUP, DUP)
- get_coordinator_instructions: Creates instructions for the APR analysis coordinator agent
"""

from .metric_instructions import build_metric_agent_instructions
from .coordinator_instructions import get_coordinator_instructions

__all__ = [
    'build_metric_agent_instructions',
    'get_coordinator_instructions'
]