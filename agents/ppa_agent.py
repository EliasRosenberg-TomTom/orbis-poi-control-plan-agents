"""
PPA (Process Performance Analysis) Agent Module

This module contains the PPA agent creation function for analyzing
process performance metrics in APR data.
"""

from agent import Agent
from agent_tools import (
    get_ppa_metrics_for_apr, get_pull_request_title, 
    get_jira_ticket_title, get_jira_ticket_description, get_feature_rankings
)
from metric_instructions import build_metric_agent_instructions


def create_ppa_agent(model_deployment_name: str) -> Agent:
    """
    Create a PPA (Process Performance Analysis) metrics analysis agent.
    
    Args:
        model_deployment_name: Name of the model deployment to use
        
    Returns:
        Agent: Configured PPA agent ready for deployment
    """
    return Agent(
        name="PPA_Agent",
        instructions=build_metric_agent_instructions('PPA'),
        model=model_deployment_name,
        functions={
            get_ppa_metrics_for_apr, 
            get_pull_request_title,
            get_jira_ticket_title, 
            get_jira_ticket_description, 
            get_feature_rankings
        },
        metadata={"timeout": 360}
    )