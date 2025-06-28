import os
import json
import yaml
from clients.github_client import GitHubClient
from data.email_message import EmailMessage
from datetime import datetime

class EmailIndexer:
    def __init__(self, github: GitHubClient, context: str = "MH"):
        self.github = github
        self.context = context
        self.emails_dir = f"{context}/emails"
        self.index_path = f"{context}/index.json"

    def get_index(self) -> list:
        try:
            raw = self.github.get_file(self.index_path)
            return json.loads(raw)
        except Exception as e:
            if "404" in str(e):
                print(f"[INFO] Aucun index trouvé. Création d’un nouveau fichier {self.index_path}.")
                self.create_empty_index()
                return []
            print(f"[WARN] Index introuvable ou corrompu : {e}")
            return []

    def create_empty_index(self):
        empty_index = []
        content = json.dumps(empty_index, indent=2, ensure_ascii=False)
        self.github.upload_file(
            self.index_path,
            content,
            commit_message=f"Création initiale de l’index pour le contexte {self.context}"
        )
        print(f"[INDEX] Fichier {self.index_path} créé avec succès.")

    def update_index_with_email(self, email: EmailMessage, path: str):
        try:
            current_index = self.get_index()

            if any(meta.get("id") == email.id for meta in current_index):
                print(f"[SKIP] Email déjà présent dans l’index : {email.subject}")
                return

            try:
                content = self.github.get_file(path)
                parts = content.split("---")
                if len(parts) >= 3:
                    metadata = yaml.safe_load(parts[1])
                    summary = metadata.get("summary", "")
                else:
                    summary = ""
            except Exception:
                summary = ""

            metadata = {
                "id": email.id,
                "type": "email",
                "title": email.subject,
                "source": email.source or "Outlook",
                "date": email.date.strftime('%Y-%m-%d %H:%M:%S'),  # ✅ Convertir datetime en string
                "author": email.sender,
                "recipients": email.recipients,
                "context": self.context,
                "tags": [],
                "status": "en_cours",
                "file": path,
                "summary": summary
            }

            current_index.append(metadata)
            content = json.dumps(current_index, indent=2, ensure_ascii=False)
            self.github.upload_file(self.index_path, content, commit_message=f"Ajout {email.subject} dans index")
            print(f"[INDEX] Ajouté : {email.subject}")

        except Exception as e:
            print(f"[ERREUR INDEX] Mise à jour échouée pour {email.subject} : {e}")

    def run(self):
        print(f"[INFO] Reconstruction complète de l'index à partir de {self.emails_dir}")
        try:
            paths = self.github.list_files(self.emails_dir)
            entries = []
            for path in paths:
                try:
                    content = self.github.get_file(path)
                    parts = content.split("---")
                    if len(parts) >= 3:
                        metadata = yaml.safe_load(parts[1])
                        # S’assurer que la date est une chaîne bien formatée
                        date_str = metadata.get("date")
                        if isinstance(date_str, datetime):
                            date_str = date_str.strftime('%Y-%m-%d %H:%M:%S')

                        entries.append({
                            "id": metadata.get("id"),
                            "type": metadata.get("type", "email"),
                            "title": metadata.get("title"),
                            "source": metadata.get("source"),
                            "date": date_str,
                            "author": metadata.get("author"),
                            "recipients": metadata.get("recipients", []),
                            "context": metadata.get("context", self.context),
                            "tags": metadata.get("tags", []),
                            "status": metadata.get("status", "en_cours"),
                            "file": path,
                            "summary": metadata.get("summary", "")
                        })
                except Exception as e:
                    print(f"[WARN] Erreur de lecture fichier {path} : {e}")

            content = json.dumps(entries, indent=2, ensure_ascii=False)
            self.github.upload_file(self.index_path, content, commit_message=f"Reconstruction complète de l’index")
            print(f"[INDEX] {len(entries)} fichiers indexés avec succès.")
        except Exception as e:
            print(f"[ERREUR] Impossible de reconstruire l’index : {e}")
