from jira.JiraAPI import JiraAPI
from github.GithubAPI import GithubAPI

# Wrapper functions for agent tools.
def get_jira_ticket_description(issue_id_or_key: str) -> str:
    """
    Fetches the description of a Jira ticket by its ID or key.

    :param issue_id_or_key: The Jira issue ID or key (e.g., 'MPOI-6652').
    :return: The ticket description as a string.
    """
    jira = JiraAPI()
    return jira.get_ticket_description(issue_id_or_key)

def get_jira_ticket_title(issue_id_or_key: str) -> str:
    """
    Fetches the title of a Jira ticket by its ID or key.

    :param issue_id_or_key: The Jira issue ID or key (e.g., 'MPOI-6652').
    :return: The ticket title as a string.
    """
    jira = JiraAPI()
    return jira.get_ticket_title(issue_id_or_key)

def get_jira_ticket_release_notes(issue_id_or_key: str) -> str:
    """
    Fetches the release notes of a Jira ticket by its ID or key.

    :param issue_id_or_key: The Jira issue ID or key (e.g., 'MPOI-6652').
    :return: The ticket release notes as a string.
    """
    jira = JiraAPI()
    return jira.get_ticket_release_notes(issue_id_or_key)

def get_pull_request_body(pr_id: str) -> str:
    """
    Fetches the body of a pull request by its pr issue number.

    :param pr_id: The pull request ID (e.g., '3043').
    :return: The pull request body as a string.
    """
    gh = GithubAPI()
    return gh.get_pull_request_body(pr_id)

def get_control_plan_metrics_from_pr_comment(pr_id: str) -> str:
    """
    Fetches the control plan metrics from a pull request comment.

    :param pr_id: The pull request ID (e.g., '3043').
    :return: A string from the resolvable PR comment that contains the Control Plan Report PAV Metrics, if such a comment exists.  
    """
    gh = GithubAPI()
    bodyString = gh.get_control_plan_metrics_from_pr_comment(pr_id)
    return extract_control_plan_table(bodyString)

def extract_control_plan_table(body: str) -> str:
    """
    Extracts the markdown table (including header and all rows) from the given body string.
    Returns the table as a string, or an empty string if not found.
    """
    header = "| Country | Category Group | Reference | Actual | PAV Diff |"
    start_idx = body.find(header)
    if start_idx == -1:
        return "No string found"
    table = body[start_idx:]
    return table.strip()