from jira.JiraAPI import JiraAPI
from github.GithubAPI import GithubAPI
from databricks.DatabricksAPI import DatabricksAPI

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

def get_pull_request_title(pr_id: str) -> str:
    """
    Fetches the title of a pull request by its pr issue number.

    :param pr_id: The pull request ID (e.g., '3043').
    :return: The pull request title as a string.
    """
    gh = GithubAPI()
    return gh.get_pull_request_title(pr_id)

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

def get_jira_ticket_xlsx_attachment(issue_id_or_key: str, filename: str = None, index: int = 0) -> str:
    """
    Fetches and parses an xlsx attachment from a Jira ticket.
    Returns the parsed table as a string (CSV format) if successful, or an error message.
    :param issue_id_or_key: The Jira ticket key (e.g., 'MPOI-1234').
    :param filename: (Optional) The filename of the attachment to fetch.
    :param index: (Optional) The index of the attachment to fetch if filename is not provided.
    :return: CSV string of the Excel file, or an error message.
    """
    jira = JiraAPI()
    result = jira.parse_xlsx_attachment(issue_id_or_key, filename, index)
    if isinstance(result, str):
        # Error message
        return result
    try:
        # Convert DataFrame to CSV string for easy agent consumption
        return result.to_csv(index=False)
    except Exception as e:
        return f"Failed to convert Excel data to CSV: {e}"

def get_jira_ticket_attachments(issue_id_or_key: str) -> str:
    """
    Fetches the list of attachments for a Jira ticket.
    Returns a string listing the filenames of the attachments, or an error message.
    :param issue_id_or_key: The Jira ticket key (e.g., 'MPOI-1234').
    :return: A string listing attachment filenames, or an error message.
    """
    jira = JiraAPI()
    attachments = jira.get_ticket_attachments(issue_id_or_key)
    if not attachments:
        return "No attachments found for this ticket."
    filenames = [att.get("filename", "unknown") for att in attachments]
    return "Attachments: " + ", ".join(filenames)

def get_apr_metrics(aprNumber: int) -> str:
    """
    Fetches APR metrics from Databricks for a given APR number.
    :param aprNumber: The APR number (e.g., 119).
    :return: A string representation of the APR metrics, or an error message.
    """
    db = DatabricksAPI()
    catalog = "pois_aqua_dev"
    schema = f"run_apr_{aprNumber}"
    table =  "issue_list_metrics_by_category_group"
    statement = f"select diff_absolute, country, category_group_name FROM {catalog}.{schema}.{table}"

    return db.execute_sql(catalog, schema, statement)

def get_PRs_from_apr(aprNumber: int) -> str:
    """
    Fetches the list of pull request numbers associated with a given APR number from Databricks.
    :param aprNumber: The APR number (e.g., 119).
    :return: A string listing the pull request numbers, or an error message.
    """
    db = DatabricksAPI()
    catalog = "pois_aqua_dev"
    schema = f"control_plan_automation"
    table =  "release_tag_to_apr_number"
    statement = f"select consecutiveAPRPullRequests FROM {catalog}.{schema}.{table} WHERE aprNumber = {aprNumber}"

    return db.execute_sql(catalog, schema, statement)