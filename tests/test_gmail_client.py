import pytest
from clients.gmail_client import GmailClient

@pytest.mark.integration
def test_rechercher_par_expediteur_fathom():
    client = GmailClient()

    # Recherche tous les mails envoyés par Fathom
    query = 'from:no-reply@fathom.video'
    resultats = client.rechercher_par_sujet(query, max_results=5)

    assert isinstance(resultats, list)
    for email in resultats:
        assert "id" in email
        assert "sujet" in email
        assert "snippet" in email
        print(f"Sujet: {email['sujet']}\nSnippet: {email['snippet']}\n")
