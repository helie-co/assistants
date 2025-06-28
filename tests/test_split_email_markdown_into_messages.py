import sys
from pathlib import Path
from datetime import datetime

# Ajout du dossier racine au path pour les imports
root_path = Path(__file__).resolve().parents[1]
sys.path.append(str(root_path))

import pytest
from utils.email_splitter import EmailSplitter
from data.email_message import EmailMessage


def test_split_email_markdown_into_messages():
    fichier = Path("tests/samples/email_test_editique.md")
    assert fichier.exists(), f"❌ Fichier introuvable : {fichier}"

    splitter = EmailSplitter()
    messages: list[EmailMessage] = splitter.split_markdown_file(fichier)

    # Vérifie qu'on a bien une liste de messages
    assert isinstance(messages, list), "Le résultat n'est pas une liste"
    assert all(isinstance(msg, EmailMessage) for msg in messages), "Certains éléments ne sont pas des EmailMessage"

    # Vu la structure de l'exemple fourni, on attend au moins 3 messages : original + 2 forwards
    assert len(messages) >= 3, f"❌ Seulement {len(messages)} message(s) trouvé(s), 3 attendus."

    for i, msg in enumerate(messages):
        assert msg.subject, f"Message {i+1} sans sujet"
        assert isinstance(msg.date, datetime), f"Message {i+1} sans date valide"
        assert isinstance(msg.sender, str) and msg.sender, f"Message {i+1} sans expéditeur"
        assert isinstance(msg.recipients, list), f"Message {i+1} a des destinataires invalides"
        assert msg.body.strip(), f"Message {i+1} a un corps vide"

    print(f"[✅ TEST] {len(messages)} messages extraits avec succès.")
    for i, msg in enumerate(messages, 1):
        print(f"\n--- MESSAGE {i} ---")
        print(f"ID     : {msg.id}")
        print(f"Sujet  : {msg.subject}")
        print(f"Date   : {msg.date}")
        print(f"De     : {msg.sender}")
        print(f"À      : {', '.join(msg.recipients)}")
        print(f"Corps  : {msg.body[:300]}...")
