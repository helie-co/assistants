import pytest
import os
import sys

# Ajoute le chemin vers le dossier contenant EmailClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clients.email_client import EmailClient


@pytest.fixture(scope="module")
def email_client():
    return EmailClient()


def test_connect_inbox(email_client):
    inbox, archive = email_client.connect_inbox()
    assert inbox.Name.lower() == "boîte de réception"
    assert archive is not None


def test_count_total_emails(email_client):
    count = email_client.count_total_emails()
    assert isinstance(count, int)
    assert count >= 0


def test_fetch_emails(email_client):
    emails = email_client.fetch_emails(limit=2)
    assert isinstance(emails, list)
    if emails:
        assert hasattr(emails[0], "subject")
        assert hasattr(emails[0], "sender")
        assert hasattr(emails[0], "body")


def test_fetch_email_by_id(email_client):
    ids = email_client.list_all_email_ids(limit=1)
    if ids:
        email = email_client.fetch_email_by_id(ids[0])
        assert email is not None
        assert hasattr(email, "subject")


@pytest.mark.skip(reason="Test d'archivage individuel désactivé temporairement")
def test_archive_email_by_id(email_client):
    ids = email_client.list_all_email_ids(limit=1)
    if not ids:
        pytest.skip("Aucun email à archiver.")

    initial_count = email_client.count_total_emails(source_folder="inbox")
    archived_email = email_client.archive_email_by_id(ids[0])
    assert archived_email.source == "archive"

    new_count = email_client.count_total_emails(source_folder="inbox")
    assert new_count == initial_count - 1


@pytest.mark.skip(reason="Test d'archivage multiple désactivé temporairement")
def test_archive_multiple_emails(email_client):
    ids = email_client.list_all_email_ids(limit=2)
    if len(ids) < 2:
        pytest.skip("Pas assez d'emails pour tester l’archivage multiple.")

    initial_count = email_client.count_total_emails(source_folder="inbox")
    archived = email_client.archive_emails_by_ids(ids)

    assert isinstance(archived, list)
    assert all(e.source == "archive" for e in archived)

    new_count = email_client.count_total_emails(source_folder="inbox")
    assert new_count == initial_count - len(ids)


@pytest.mark.skip(reason="Test d'envoi de mail désactivé temporairement")
def test_send_email(email_client):
    to = ["jf@helie-co.fr", "jean-francois.helie@soprasterianext.com"]
    subject = "Test automatique de l'EmailClient"
    body = "Ce message a été envoyé automatiquement par le test_send_email()."

    try:
        email_client.send_email(to=to, subject=subject, body=body)
    except Exception as e:
        pytest.fail(f"Échec de l'envoi de l'email : {e}")


@pytest.mark.skip(reason="Test d'envoi de mail désactivé temporairement")
def test_reply_and_forward(email_client):
    keyword = "Test Reply To"
    results = email_client.search_emails_by_subject(keyword=keyword, limit=1)

    if not results:
        pytest.skip(f"Aucun email trouvé avec le sujet contenant : '{keyword}'")

    email = results[0]
    print(f"Email trouvé : {email.subject} | De : {email.sender}")

    # Test reply_to_all
    try:
        result_reply = email_client.reply_to_all(
            entry_id=email.id,
            message="Ceci est une réponse automatique à tous les destinataires."
        )
        assert result_reply is True
    except Exception as e:
        pytest.fail(f"Échec lors du reply_to_all : {e}")

    # Test forward_email
    try:
        result_forward = email_client.forward_email(
            entry_id=email.id,
            to=["jfn.shilov@gmail.com"],
            message="Transfert automatique de l'email trouvé pour test."
        )
        assert result_forward is True
    except Exception as e:
        pytest.fail(f"Échec lors du forward_email : {e}")
