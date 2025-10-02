"""
SUP (Service Uptime Performance) Agent Module

This module contains the SUP agent creation function for analyzing
service uptime performance metrics in APR data.
"""

from agent import Agent
from agent_tools import (
    get_sup_metrics_for_apr, get_pull_request_title, 
    get_jira_ticket_title, get_jira_ticket_description, get_feature_rankings
)
from metric_instructions import build_metric_agent_instructions


def create_sup_agent(model_deployment_name: str) -> Agent:
    """
    Create a SUP (Service Uptime Performance) metrics analysis agent.
    
    Args:
        model_deployment_name: Name of the model deployment to use
        
    Returns:
        Agent: Configured SUP agent ready for deployment
    """
    return Agent(
        name="SUP_Agent",
        instructions=build_metric_agent_instructions('SUP'),
        model=model_deployment_name,
        functions={
            get_sup_metrics_for_apr, 
            get_pull_request_title,
            get_jira_ticket_title, 
            get_jira_ticket_description, 
            get_feature_rankings
        },
        metadata={"timeout": 360}
    )