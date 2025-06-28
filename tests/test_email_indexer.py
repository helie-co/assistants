import pytest
import json
from services.email_service import EmailService
from clients.github_client import GitHubClient
from clients.email_client import EmailClient


@pytest.fixture(scope="module")
def setup_service():
    github = GitHubClient()
    email_client = EmailClient()
    return EmailService(github=github, email_client=email_client, context="MH")


def test_indexer_integration(setup_service):
    service = setup_service

    # Étape 1 : synchronisation de 2 emails
    emails = service.email_client.fetch_emails(limit=2)
    assert len(emails) == 2
    paths = service.sync_emails(limit=2)

    ids = [email.id for email in emails]

    # Étape 2 : vérification directe de l’index (déjà mis à jour)
    index_path = "MH/index.json"
    try:
        content = service.github.get_file(index_path)
        metadata_list = json.loads(content)
    except Exception as e:
        pytest.fail(f"Erreur de lecture index.json : {e}")

    indexed_ids = [meta["id"] for meta in metadata_list]
    for eid in ids:
        assert eid in indexed_ids

    # Étape 3 : nettoyage
    for path in paths:
        try:
            service.github.delete_file(path, commit_message="Suppression post-test EmailIndexer")
        except Exception as e:
            pytest.fail(f"Erreur suppression {path} : {e}")

    try:
        service.github.delete_file(index_path, commit_message="Suppression index.json post-test")
    except Exception as e:
        pytest.fail(f"Erreur suppression index.json : {e}")
