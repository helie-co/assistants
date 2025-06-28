import os
import traceback
import yaml
from data.email_message import EmailMessage
from clients.github_client import GitHubClient
from clients.email_client import EmailClient
from services.email_indexer import EmailIndexer
from clients.gpt_client import GPTClient


class EmailService:
    def __init__(self, github: GitHubClient, email_client: EmailClient, context="MH"):
        self.github = github
        self.email_client = email_client
        self.context = context
        self.indexer = EmailIndexer(github=github, context=context)
        self.gpt = GPTClient()

    def get_index(self):
        return self.indexer.get_index()

    def sync_emails(self, limit=None):
        try:
            print("[INFO] Récupération de l'index existant...")
            index = self.get_index()
            existing_ids = set(item.get("id") for item in index)
        except Exception as e:
            print(f"[WARN] Index introuvable ou corrompu : {e}")
            existing_ids = set()

        emails = self.email_client.fetch_emails(limit=limit)
        new_emails = [email for email in emails if email.id not in existing_ids]

        print(f"[INFO] Emails déjà indexés : {len(existing_ids)}")
        print(f"[INFO] Nouveaux emails à traiter : {len(new_emails)}")

        paths = []
        for email in new_emails:
            try:
                path = self._push_email(email)
                self.indexer.update_index_with_email(email, path)
                paths.append(path)
            except Exception as e:
                print(f"[ERREUR] Erreur lors du traitement de l’email : {email.subject}")
                traceback.print_exc()
        return paths

    def _push_email(self, email: EmailMessage) -> str:
        try:
            summary = self.gpt.summarize_email(email.body)
        except Exception as e:
            print(f"[WARN] Échec du résumé pour {email.subject}, résumé vide.")
            summary = ""

        md_content = self._generate_markdown(email, summary)
        filename = f"{self.context}/emails/{email.date.strftime('%Y-%m-%d')}_{email.id}.md"
        self.github.upload_file(filename, md_content, commit_message=f"Ajout email {email.subject}")
        return filename

    def _generate_markdown(self, email: EmailMessage, summary: str) -> str:
        metadata = {
            "id": email.id,
            "subject": email.subject,
            "date": email.date.strftime('%Y-%m-%d %H:%M:%S'),
            "author": email.sender,
            "recipients": email.recipients,
            "source": email.source,
            "status": "en_cours",
            "summary": summary,
            "tags": [],
        }

        frontmatter = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)
        return f"---\n{frontmatter}---\n\n{email.body.strip()}"

    def archive_email_by_id(self, entry_id: str):
        archived = self.email_client.archive_email_by_id(entry_id)
        path = self._push_email(archived)
        self.indexer.update_index_with_email(archived, path)
        return path

    def archive_emails_by_ids(self, ids: list[str]):
        archived_emails = self.email_client.archive_emails_by_ids(ids)
        paths = []
        for email in archived_emails:
            path = self._push_email(email)
            self.indexer.update_index_with_email(email, path)
            paths.append(path)
        return paths
