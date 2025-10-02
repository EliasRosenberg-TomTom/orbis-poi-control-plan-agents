"""
DUP (Data Usage Patterns) Agent Module

This module contains the DUP agent creation function for analyzing
data usage pattern metrics in APR data.
"""

from agent import Agent
from agent_tools import (
    get_dup_metrics_for_apr, get_pull_request_title, 
    get_jira_ticket_title, get_jira_ticket_description, get_feature_rankings
)
from metric_instructions import build_metric_agent_instructions


def create_dup_agent(model_deployment_name: str) -> Agent:
    """
    Create a DUP (Data Usage Patterns) metrics analysis agent.
    
    Args:
        model_deployment_name: Name of the model deployment to use
        
    Returns:
        Agent: Configured DUP agent ready for deployment
    """
    return Agent(
        name="DUP_Agent",
        instructions=build_metric_agent_instructions('DUP'),
        model=model_deployment_name,
        functions={
            get_dup_metrics_for_apr, 
            get_pull_request_title,
            get_jira_ticket_title, 
            get_jira_ticket_description, 
            get_feature_rankings
        },
        metadata={"timeout": 360}
    )