"""
Coordinator Agent Module

This module contains the coordinator agent creation function for synthesizing
APR analysis results and correlating findings with JIRA tickets.
"""

from agent import Agent
from agent_tools import (
    get_jira_ticket_description, get_pull_request_body, get_pull_request_title,
    get_control_plan_metrics_from_pr_comment, get_jira_ticket_title, 
    get_jira_ticket_release_notes, get_jira_ticket_xlsx_attachment, 
    get_jira_ticket_attachments, get_PRs_from_apr, get_feature_rankings
)
from agent_instructions import get_coordinator_instructions


def create_coordinator_agent(model_deployment_name: str) -> Agent:
    """
    Create a coordinator agent for synthesizing APR analysis results.
    
    Args:
        model_deployment_name: Name of the model deployment to use
        
    Returns:
        Agent: Configured coordinator agent ready for deployment
    """
    return Agent(
        name="Coordinator_Agent",
        instructions=get_coordinator_instructions(),
        model=model_deployment_name,
        functions={
            get_jira_ticket_description, 
            get_pull_request_body, 
            get_pull_request_title,
            get_control_plan_metrics_from_pr_comment, 
            get_jira_ticket_title, 
            get_jira_ticket_release_notes, 
            get_jira_ticket_xlsx_attachment, 
            get_jira_ticket_attachments, 
            get_PRs_from_apr, 
            get_feature_rankings
        },
        metadata={"timeout": 600}  # Extended timeout for JIRA analysis
    )