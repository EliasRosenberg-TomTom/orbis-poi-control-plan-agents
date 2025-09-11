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
            description = response.json().get('fields', {}).get('description', '')
            if not description:
                return 'No description found'
            return description
        else:
            return f'Error: {response.status_code} - {response.text}'
    
    def get_ticket_title(self, issue_id_or_key):
        url = f"{self.base_url}/{issue_id_or_key}"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            title = response.json().get('fields', {}).get('summary', '')
            if not title:
                return 'No title found'
            return title
        else:
            return f'Error: {response.status_code} - {response.text}'
        
    def get_ticket_release_notes(self, issue_id_or_key):
        url = f"{self.base_url}/{issue_id_or_key}"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            release_notes = response.json().get('fields', {}).get('customfield_10179', '')  # Release notes consistently on customfield_10179
            if not release_notes:
                return 'No release notes found'
            return release_notes
        else:
            return f'Error: {response.status_code} - {response.text}'