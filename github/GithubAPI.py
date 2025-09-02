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
            "Accept": "application/vnd.github.v3+json"
        }

    def get_pull_request_body(self, pr_number):
        url = f"{self.base_url}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("body", "No body found")
        else:
            return f'Error: {response.status_code} - {response.text}'