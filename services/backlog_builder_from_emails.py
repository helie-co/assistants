import json
import re
from pathlib import Path
from clients.gpt_client import GPTClient
from clients.github_client import GitHubClient
from data.action import Action


class BacklogBuilderFromEmails:
    def __init__(
        self,
        github: GitHubClient,
        source_dirs: list[str],  # ⬅️ Liste des dossiers (ex: ["MH/emails", "MH/transcriptions"])
        backlog_path: str,
        prompt_path: str = "prompts/extraction_actions.prompt"
    ):
        self.github = github
        self.source_dirs = source_dirs
        self.backlog_path = backlog_path
        self.prompt_path = prompt_path
        self.gpt = GPTClient()
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def _load_all_markdown_emails(self) -> list[tuple[str, str]]:
        markdown_files = []
        for directory in self.source_dirs:
            fichiers = self.github.list_files(directory)
            markdown_files.extend(f for f in fichiers if f.endswith(".md"))

        emails = []
        for path in markdown_files:
            content = self.github.get_file(path)
            emails.append((path, content))
        return emails

    def _build_prompt(self, markdown_content: str) -> str:
        return self.prompt_template.replace("{{markdown}}", markdown_content)

    def extract_all_actions(self) -> list[Action]:
        actions: list[Action] = []
        emails = self._load_all_markdown_emails()

        for path, content in emails:
            prompt = self._build_prompt(content)
            try:
                response = self.gpt.complete(
                    prompt=prompt,
                    system_prompt="Tu es un assistant rigoureux qui extrait des actions dans des emails professionnels, uniquement en JSON.",
                    temperature=0.3,
                    max_tokens=1200,
                    timeout=60
                )
                match = re.search(r"\[\s*{.*?}\s*\]", response, re.DOTALL)
                if match:
                    parsed = json.loads(match.group())
                    for a in parsed:
                        a["source"] = path
                        actions.append(Action(**a))
            except Exception as e:
                print(f"[WARN] Extraction échouée pour {path} : {e}")

        return actions

    def build_backlog_file(self):
        actions = self.extract_all_actions()
        json_content = json.dumps([a.__dict__ for a in actions], indent=2, ensure_ascii=False)
        self.github.upload_file(
            self.backlog_path,
            json_content,
            commit_message="📅 update backlog"
        )
        print(f"✅ Backlog enregistré dans {self.backlog_path} avec {len(actions)} action(s).")
