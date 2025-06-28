import os
import sys
import pytest
import json
from dotenv import load_dotenv

# Ajouter le chemin vers les modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clients.github_client import GitHubClient
from clients.email_client import EmailClient
from services.email_service import EmailService


@pytest.fixture(scope="module")
def setup_service():
    load_dotenv()
    github = GitHubClient()
    email_client = EmailClient()
    return EmailService(github=github, email_client=email_client, context="MH")


def test_sync_and_indexation_cleanup(setup_service):
    service = setup_service

    # Lire 2 emails
    emails = service.email_client.fetch_emails(limit=2)
    if len(emails) < 2:
        pytest.skip("Pas assez d'emails dans la boîte de réception pour exécuter le test.")

    # Compter les fichiers déjà présents sur GitHub
    initial_paths = []
    for email in emails:
        try:
            path = service.email_to_path(email)
            service.github.get_file(path)
            initial_paths.append(path)
        except Exception:
            pass

    # Sync : essaie de push jusqu'à 2
    paths_md = service.sync_emails(limit=2)
    assert len(paths_md) + len(initial_paths) == 2 or len(initial_paths) == 2

    # Vérifie que les emails sont bien indexés dans index.json
    try:
        index_raw = service.github.get_file(f"{service.context}/index.json")
        index = json.loads(index_raw)
        indexed_ids = [entry["id"] for entry in index]
        for email in emails:
            assert email.id in indexed_ids
    except Exception as e:
        pytest.fail(f"Erreur lors de la lecture ou de la vérification de l’index : {e}")

    # Nettoyage : uniquement ceux qui ont été créés par sync_emails()
    for path in paths_md:
        try:
            service.github.delete_file(path, commit_message="Nettoyage test .md")
        except Exception as e:
            pytest.fail(f"Erreur suppression {path} : {e}")

    try:
        service.github.delete_file(f"{service.context}/index.json", commit_message="Nettoyage index.json")
    except Exception as e:
        pytest.fail(f"Erreur suppression index.json : {e}")
