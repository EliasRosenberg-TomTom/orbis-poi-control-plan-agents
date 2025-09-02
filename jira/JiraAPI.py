import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

class JiraAPI:
    def __init__(self, domain=None, email=None, api_token=None):
        load_dotenv()

        self.domain = domain or os.getenv("JIRA_DOMAIN")
        self.email = email or os.getenv("JIRA_EMAIL")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN")

        self.base_url = f"https://{self.domain}.atlassian.net/rest/api/2/issue"
        self.auth = HTTPBasicAuth(self.email, self.api_token)

    def get_ticket_description(self, issue_id_or_key):
        url = f"{self.base_url}/{issue_id_or_key}"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            description = response.json().get('fields', {}).get('description', 'No description found')
            return description
        else:
            return f'Error: {response.status_code} - {response.text}'