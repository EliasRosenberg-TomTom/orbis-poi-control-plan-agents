import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import io
import pandas as pd

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
            print(f"DEBUG: ticket description fetched successfully: {issue_id_or_key}")
            if not description:
                return 'No description found'
            return description
        else:
            print(f"DEBUG: failed to fetch ticket description: {issue_id_or_key}")
            return f'Error: {response.status_code} - {response.text}'
    
    def get_ticket_title(self, issue_id_or_key):
        url = f"{self.base_url}/{issue_id_or_key}"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            print(f"DEBUG: ticket title fetched successfully: {issue_id_or_key}")
            title = response.json().get('fields', {}).get('summary', '')
            if not title:
                return 'No title found'
            return title
        else:
            print(f"DEBUG: failed to fetch ticket title: {issue_id_or_key}")
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

    def get_ticket_attachments(self, issue_id_or_key):
        url = f"{self.base_url}/{issue_id_or_key}"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            attachments = response.json().get('fields', {}).get('attachment', [])
            return attachments
        else:
            return []

    def download_attachment(self, attachment_url):
        response = requests.get(attachment_url, auth=self.auth, stream=True)
        if response.status_code == 200:
            return response.content
        else:
            return None

    def get_attachment_data(self, issue_id_or_key, filename=None, index=0):
        attachments = self.get_ticket_attachments(issue_id_or_key)
        if not attachments:
            return {"error": "No attachments found for this ticket."}

        # Find by filename or index
        attachment = None
        if filename:
            for att in attachments:
                if att.get("filename") == filename:
                    attachment = att
                    break
        else:
            if 0 <= index < len(attachments):
                attachment = attachments[index]

        if not attachment:
            return {"error": "Attachment not found."}

        file_bytes = self.download_attachment(attachment["content"])
        if file_bytes is None:
            return {"error": "Failed to download attachment."}

        return {
            "filename": attachment["filename"],
            "mimeType": attachment["mimeType"],
            "content_bytes": file_bytes
        }

    def parse_xlsx_attachment(self, issue_id_or_key, filename=None, index=0):
        attachment_info = self.get_attachment_data(issue_id_or_key, filename, index)
        if "error" in attachment_info:
            return attachment_info["error"]

        if not attachment_info["mimeType"].endswith("spreadsheetml.sheet"):
            return f"Attachment {attachment_info['filename']} is not an Excel file."

        try:
            excel_bytes = io.BytesIO(attachment_info["content_bytes"])
            df = pd.read_excel(excel_bytes)
            return df
        except Exception as e:
            return f"Failed to parse Excel file: {e}"