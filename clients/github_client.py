import os
import base64
import requests
import json
from dotenv import load_dotenv


class GitHubClient:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("GITHUB_TOKEN")
        self.owner = os.getenv("GITHUB_OWNER")
        self.repo = os.getenv("GITHUB_REPO")
        self.branch = os.getenv("GITHUB_BRANCH", "main")
        self.api_base = "https://api.github.com"
        self.base_url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }
        self._staging_area = {}

    def upload_file(self, path, content, commit_message):
        url = f"{self.base_url}/{path}"
        response = requests.get(url, headers=self.headers, params={"ref": self.branch})
        sha = response.json()["sha"] if response.status_code == 200 else None

        data = {
            "message": commit_message,
            "branch": self.branch,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        }
        if sha:
            data["sha"] = sha

        put_response = requests.put(url, headers=self.headers, json=data)
        put_response.raise_for_status()
        return put_response.json()

    def get_file(self, path):
        url = f"{self.base_url}/{path}"
        response = requests.get(url, headers=self.headers, params={"ref": self.branch})
        response.raise_for_status()
        content_encoded = response.json()["content"]
        return base64.b64decode(content_encoded).decode("utf-8")

    def delete_file(self, path, commit_message):
        url = f"{self.base_url}/{path}"
        response = requests.get(url, headers=self.headers, params={"ref": self.branch})
        response.raise_for_status()
        sha = response.json()["sha"]

        data = {
            "message": commit_message,
            "branch": self.branch,
            "sha": sha
        }
        del_response = requests.delete(url, headers=self.headers, json=data)
        del_response.raise_for_status()
        return del_response.json()

    def list_files(self, path: str) -> list[str]:
        url = f"{self.api_base}/repos/{self.owner}/{self.repo}/contents/{path}"
        files = []

        response = requests.get(url, headers=self.headers, params={"ref": self.branch})
        if response.status_code != 200:
            raise RuntimeError(f"Erreur lors de la récupération du dossier {path} : {response.text}")

        for item in response.json():
            if item["type"] == "file":
                files.append(item["path"])
            elif item["type"] == "dir":
                files.extend(self.list_files(item["path"]))

        return files

    def stage_file(self, path, content):
        self._staging_area[path] = content

    def commit_staged_files(self, commit_message="Commit multiple files"):
        if not self._staging_area:
            raise ValueError("Aucun fichier à committer")
        for path, content in self._staging_area.items():
            self.upload_file(path, content, commit_message)
        self._staging_area = {}

    def upload_files(self, files: dict, commit_message="Commit multiple files"):
        for path, content in files.items():
            self.stage_file(path, content)
        self.commit_staged_files(commit_message)
