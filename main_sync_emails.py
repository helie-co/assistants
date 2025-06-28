import os
import json
from dotenv import load_dotenv

from clients.github_client import GitHubClient
from clients.email_client import EmailClient
from services.email_service import EmailService
from services.email_indexer import EmailIndexer

def main():
    # Chargement des variables d'environnement
    load_dotenv()

    # Instanciation des clients et services
    github = GitHubClient()
    email_client = EmailClient()
    service = EmailService(github=github, email_client=email_client, context="MH")
    service.indexer = EmailIndexer(context="MH", github=github)

    print("[INFO] Synchronisation des derniers emails...")
    paths = service.sync_emails(limit=30)
    #paths = service.sync_emails()

if __name__ == "__main__":
    main()
