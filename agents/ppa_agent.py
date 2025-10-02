
from agent import Agent
from agent_tools import (
    get_ppa_metrics_for_apr, get_pull_request_title, 
    get_jira_ticket_title, get_jira_ticket_description, get_feature_rankings
)
from agent_instructions import build_metric_agent_instructions


def create_ppa_agent(model_deployment_name: str) -> Agent:
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