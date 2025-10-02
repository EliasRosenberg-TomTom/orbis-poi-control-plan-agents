
from agent import Agent
from agent_tools import (
    get_pav_metrics_for_apr, get_pull_request_title, 
    get_jira_ticket_title, get_jira_ticket_description, get_feature_rankings
)
from metric_instructions import build_metric_agent_instructions


def create_pav_agent(model_deployment_name: str) -> Agent:
    return Agent(
        name="PAV_Agent",
        instructions=build_metric_agent_instructions('PAV'),
        model=model_deployment_name,
        functions={
            get_pav_metrics_for_apr, 
            get_pull_request_title,
            get_jira_ticket_title, 
            get_jira_ticket_description, 
            get_feature_rankings
        },
        metadata={"timeout": 360}
    )