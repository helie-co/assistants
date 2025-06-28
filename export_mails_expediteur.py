from transformers import pipeline
from dotenv import load_dotenv
import os
from clients.gmail_client import GmailClient  # Assure-toi d’avoir ta classe ici

# Chargement des variables d'environnement
load_dotenv()

# Initialisation du classifieur (spam vs ham)
classifier = pipeline("text-classification", model="mrm8488/bert-tiny-finetuned-sms-spam-detection")

# Connexion Gmail
client = GmailClient()

# Nombre total d’emails à traiter
total_to_fetch = 100
batch_size = 10

print(f"📥 Lecture des {total_to_fetch} derniers mails Gmail...")

# Liste des IDs déjà traités (évite les doublons éventuels)
traites = set()

# Lecture et analyse des mails par batch
processed_count = 0
next_page_token = None

while processed_count < total_to_fetch:
    messages = client.rechercher_metadata_batch(
        requete="",
        max_results=batch_size,
        page_token=next_page_token
    )

    if not messages:
        break

    # Ne traiter que les nouveaux messages
    messages = [m for m in messages if m["id"] not in traites]
    traites.update(m["id"] for m in messages)

    # Préparation des textes à classifier
    textes = [f"{m.get('sujet', '')} {m.get('snippet', '')}" for m in messages]

    try:
        results = classifier(textes)
    except Exception as e:
        print(f"[ERREUR] Erreur de classification : {e}")
        continue

    # Affichage des résultats
    for i, (msg, result) in enumerate(zip(messages, results)):
        label = result['label'].upper()
        score = result['score']
        sujet = msg.get('sujet', '')[:80]
        print(f"{processed_count + i + 1}/{total_to_fetch} ▶ [{label} - {score:.2f}] {sujet}")

    processed_count += len(messages)

    # Si on atteint le total ou pas de nouvelle page
    if processed_count >= total_to_fetch:
        break
