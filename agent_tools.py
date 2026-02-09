from apis.jira import JiraAPI
from apis.github import GithubAPI
from apis.databricks import DatabricksAPI
from apis.confluence.ConfluenceAPI import ConfluenceAPI
import pandas as pd
import os

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
    statement = f"select sinceLastPublishedAPRPullRequests FROM {catalog}.{schema}.{table} WHERE aprNumber = {aprNumber}"

    return db.execute_sql(catalog, schema, statement)

def get_apr_metrics_for_given_metric_type(aprNumber: int, metricType: str) -> str:
    """
    Fetches APR metrics from Databricks for a given APR number and metric type.
    :param aprNumber: The APR number (e.g., 121, 119, 110, etc.).
    :param metricType: The metric type (e.g., 'pav', 'ppa', 'sup', 'dup').
    :return: A string representation of the APR metrics for the specified type, or an error message.
    """
    db = DatabricksAPI()
    catalog = "pois_aqua_dev"
    schema = f"run_apr_{aprNumber}"
    table =  "issue_list"
    statement = f"select  * FROM {catalog}.{schema}.{table} WHERE validation_theme = '{metricType}'"

    return db.execute_sql(catalog, schema, statement)

def get_pav_metrics_for_apr(aprNumber: int) -> str:
    """Fetches PAV metrics with BOTH metric changes and raw count changes.
    Captures rows where EITHER the metric changed significantly OR the raw POI count changed significantly."""
    db = DatabricksAPI()
    catalog = "pois_aqua_dev"
    schema = f"run_apr_{aprNumber}"
    table = "issue_list"
    statement = f"""SELECT 
        country, 
        definitiontag, 
        diff_absolute,
        count_generics.reference_poi_count as reference_count,
        count_generics.actual_poi_count as actual_count,
        pav_generics.reference_pav_available,
        pav_generics.actual_pav_available,
        CASE 
            WHEN count_generics.reference_poi_count > 0 
            THEN ((count_generics.actual_poi_count - count_generics.reference_poi_count) / count_generics.reference_poi_count) * 100
            ELSE 0 
        END as count_change_percent,
        (count_generics.actual_poi_count - count_generics.reference_poi_count) as count_change_absolute
    FROM {catalog}.{schema}.{table} 
    WHERE validation_theme = 'pav' 
    AND (
        -- Scenario 1: Significant metric change (existing logic)
        (abs(diff_absolute) > 3 AND (pav_generics.reference_pav_available >= 100 OR pav_generics.actual_pav_available >= 100))
        OR
        -- Scenario 2: Significant count change (new logic)
        ((
            -- Large percentage change (>50% increase/decrease) with meaningful base count
            (abs((count_generics.actual_poi_count - count_generics.reference_poi_count) / NULLIF(count_generics.reference_poi_count, 0)) > 0.5
             AND count_generics.reference_poi_count >= 500)
            OR
            -- Large absolute count change (>1000 POIs) regardless of percentage
            abs(count_generics.actual_poi_count - count_generics.reference_poi_count) > 1000
        ) AND (count_generics.reference_poi_count >= 100 OR count_generics.actual_poi_count >= 100))
    )
    ORDER BY 
        -- Prioritize by: 1) Large metric changes, 2) Large count changes
        abs(diff_absolute) DESC, 
        abs(count_generics.actual_poi_count - count_generics.reference_poi_count) DESC
    LIMIT 1000"""
    return db.execute_sql(catalog, schema, statement)

def get_ppa_metrics_for_apr(aprNumber: int) -> str:
    """Fetches PPA metrics with BOTH metric changes and raw count changes.
    Captures rows where EITHER the metric changed significantly OR the raw POI count changed significantly."""
    db = DatabricksAPI()
    catalog = "pois_aqua_dev"
    schema = f"run_apr_{aprNumber}"
    table = "issue_list"
    statement = f"""SELECT 
        country, 
        definitiontag, 
        diff_absolute,
        count_generics.reference_poi_count as reference_count,
        count_generics.actual_poi_count as actual_count,
        ppa_generics.reference_ppa_accurate,
        ppa_generics.actual_ppa_available,
        CASE 
            WHEN count_generics.reference_poi_count > 0 
            THEN ((count_generics.actual_poi_count - count_generics.reference_poi_count) / count_generics.reference_poi_count) * 100
            ELSE 0 
        END as count_change_percent,
        (count_generics.actual_poi_count - count_generics.reference_poi_count) as count_change_absolute
    FROM {catalog}.{schema}.{table} 
    WHERE validation_theme = 'ppa' 
    AND (
        -- Scenario 1: Significant metric change (existing logic)
        (abs(diff_absolute) > 3 AND (ppa_generics.reference_ppa_accurate >= 100 OR ppa_generics.actual_ppa_available >= 100))
        OR
        -- Scenario 2: Significant count change (new logic)
        ((
            -- Large percentage change (>50% increase/decrease) with meaningful base count
            (abs((count_generics.actual_poi_count - count_generics.reference_poi_count) / NULLIF(count_generics.reference_poi_count, 0)) > 0.5
             AND count_generics.reference_poi_count >= 500)
            OR
            -- Large absolute count change (>1000 POIs) regardless of percentage
            abs(count_generics.actual_poi_count - count_generics.reference_poi_count) > 1000
        ) AND (count_generics.reference_poi_count >= 100 OR count_generics.actual_poi_count >= 100))
    )
    ORDER BY 
        -- Prioritize by: 1) Large metric changes, 2) Large count changes
        abs(diff_absolute) DESC, 
        abs(count_generics.actual_poi_count - count_generics.reference_poi_count) DESC
    LIMIT 1000"""
    return db.execute_sql(catalog, schema, statement)

def get_sup_metrics_for_apr(aprNumber: int) -> str:
    db = DatabricksAPI()
    catalog = "pois_aqua_dev"
    schema = f"run_apr_{aprNumber}"
    table = "issue_list"
    statement = f"""SELECT country, definitiontag, diff_absolute 
        FROM {catalog}.{schema}.{table} 
        WHERE validation_theme = 'sup' 
        AND abs(diff_absolute) > 3
        AND (sup_generics.actual_sup_matched >= 100
        OR sup_generics.reference_sup_matched >= 100)
        ORDER BY abs(diff_absolute) DESC 
        LIMIT 1000"""
    return db.execute_sql(catalog, schema, statement)

def get_dup_metrics_for_apr(aprNumber: int) -> str:
    """Fetches DUP metrics with BOTH metric changes and raw count changes.
    Captures rows where EITHER the metric changed significantly OR the raw POI count changed significantly."""
    db = DatabricksAPI()
    catalog = "pois_aqua_dev"
    schema = f"run_apr_{aprNumber}"
    table = "issue_list"
    statement = f"""SELECT 
        country, 
        definitiontag, 
        diff_absolute,
        count_generics.reference_poi_count as reference_count,
        count_generics.actual_poi_count as actual_count,
        CASE 
            WHEN count_generics.reference_poi_count > 0 
            THEN ((count_generics.actual_poi_count - count_generics.reference_poi_count) / count_generics.reference_poi_count) * 100
            ELSE 0 
        END as count_change_percent,
        (count_generics.actual_poi_count - count_generics.reference_poi_count) as count_change_absolute
    FROM {catalog}.{schema}.{table} 
    WHERE validation_theme = 'dup' 
    AND (
        -- Scenario 1: Significant metric change (existing logic)
        (abs(diff_absolute) > 30 AND (count_generics.actual_poi_count >= 271 OR count_generics.reference_poi_count >= 271))
        OR
        -- Scenario 2: Significant count change (new logic)
        ((
            -- Large percentage change (>50% increase/decrease) with meaningful base count
            (abs((count_generics.actual_poi_count - count_generics.reference_poi_count) / NULLIF(count_generics.reference_poi_count, 0)) > 0.5
             AND count_generics.reference_poi_count >= 500)
            OR
            -- Large absolute count change (>1000 POIs) regardless of percentage
            abs(count_generics.actual_poi_count - count_generics.reference_poi_count) > 1000
        ) AND (count_generics.reference_poi_count >= 100 OR count_generics.actual_poi_count >= 100))
    )
    ORDER BY 
        -- Prioritize by: 1) Large metric changes, 2) Large count changes
        abs(diff_absolute) DESC, 
        abs(count_generics.actual_poi_count - count_generics.reference_poi_count) DESC
    LIMIT 1000"""
    return db.execute_sql(catalog, schema, statement)

def get_feature_rankings() -> str:
    """
    Fetches feature rankings from a CSV file to help prioritize which metric changes are significant.
    Expected CSV columns: featurename, semanticid, definitiontag, feature_rank, importance
    :return: A string representation of the feature rankings CSV data, or an error message.
    """
    try:
        # Look for rankings CSV in the current directory or a data subdirectory
        possible_paths = [
            "feature_rankings.csv",
            "data/feature_rankings.csv", 
            "../feature_rankings.csv"
        ]
        
        csv_path = None
        for path in possible_paths:
            if os.path.exists(path):
                csv_path = path
                break
        
        if csv_path is None:
            return "Error: feature_rankings.csv not found. Please ensure the file exists in the project directory."
        
        df = pd.read_csv(csv_path)
        
        # Validate expected columns exist
        required_cols = ['featurename', 'semanticid', 'definitiontag', 'feature_rank', 'importance']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return f"Error: Missing required columns in feature_rankings.csv: {missing_cols}"
        
        # Convert to string format for agent consumption
        return f"Feature Rankings Data ({len(df)} entries):\n" + df.to_string(index=False)
        
    except Exception as e:
        return f"Error reading feature rankings CSV: {e}"

def create_confluence_page(title: str, body: str, space_key: str = None, parent_id: str = None) -> str:
    """
    Creates a new Confluence page with the given title and body content.
    Uses environment variables for authentication and default space/parent settings.
    
    :param title: The title of the Confluence page to create
    :param body: The body content (markdown will be converted to Confluence storage format)
    :param space_key: Optional space key (falls back to CONFLUENCE_SPACE_KEY env var)
    :param parent_id: Optional parent page ID (falls back to CONFLUENCE_PARENT_PAGE_ID env var)
    :return: A string describing the result (success with page link or error message)
    """
    try:
        confluence = ConfluenceAPI()
        result = confluence.create_page(
            title=title,
            body=body, 
            space_key=space_key,
            parent_id=parent_id,
            markdown=True  # Convert markdown to Confluence storage format
        )
        
        if "error" in result:
            return f"Failed to create Confluence page: {result.get('error')} - {result.get('message', '')}. Details: {result.get('hint', '')}"
        else:
            page_link = result.get('link', 'No link available')
            page_id = result.get('id', 'Unknown')
            return f"Successfully created Confluence page '{title}' (ID: {page_id}). View at: {page_link}"
            
    except Exception as e:
        return f"Error creating Confluence page: {str(e)}"