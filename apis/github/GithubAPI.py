import os
import requests
from dotenv import load_dotenv

class GithubAPI:
    def __init__(self, token=None, owner=None, repo=None):
        load_dotenv()

        self.token = token or os.getenv("GITHUB_API_TOKEN")
        self.owner = owner or os.getenv("GITHUB_REPO_OWNER")
        self.repo = repo or os.getenv("GITHUB_REPO_NAME")

        self.base_url = f"https://api.github.com/repos/{self.owner}/{self.repo}"

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def get_pull_request_body(self, pr_number):
        url = f"{self.base_url}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("body", "No body found")
        else:
            return f'Error: {response.status_code} - {response.text}'
        
    def get_pull_request_title(self, pr_number):
        url = f"{self.base_url}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("title", "No title found")
        else:
            return f'Error: {response.status_code} - {response.text}'

    def get_control_plan_metrics_from_pr_comment(self, pr_number):
        url = f"{self.base_url}/pulls/{pr_number}/comments"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            comments = response.json()
            for comment in comments:
                body = comment.get("body", "")
                if "Control Plan Report" in body:
                    return body
            return "No Control Plan Report found in comments"
        else:
            return f'Error: {response.status_code} - {response.text}'
