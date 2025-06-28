# ✅ gmail_client.py

import os
import json
import requests
from datetime import datetime, UTC
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

load_dotenv()

class GmailClient:
    SCOPES = ['https://mail.google.com/']
    TOKEN_PATH = 'auth/token_gmail.json'

    def __init__(self):
        self.client_secret_path = os.getenv("GMAIL_CREDENTIALS_PATH")
        if not self.client_secret_path or not os.path.exists(self.client_secret_path):
            raise FileNotFoundError("Le fichier client secret est introuvable ou non défini dans .env")

        self.token = self._get_access_token()

    def _get_access_token(self):
        if os.path.exists(self.TOKEN_PATH):
            with open(self.TOKEN_PATH, "r", encoding="utf-8") as f:
                creds = json.load(f)
                access_token = creds.get("access_token")
                expires_at = creds.get("expires_at")
                if access_token and expires_at and datetime.now(UTC).timestamp() < expires_at:
                    return access_token
                if "refresh_token" in creds:
                    data = {
                        "client_id": creds["client_id"],
                        "client_secret": creds["client_secret"],
                        "refresh_token": creds["refresh_token"],
                        "grant_type": "refresh_token"
                    }
                    r = requests.post("https://oauth2.googleapis.com/token", data=data)
                    if r.status_code == 200:
                        new_creds = r.json()
                        creds["access_token"] = new_creds["access_token"]
                        creds["expires_at"] = datetime.now(UTC).timestamp() + new_creds.get("expires_in", 3600)
                        with open(self.TOKEN_PATH, "w", encoding="utf-8") as f:
                            json.dump(creds, f, indent=2)
                        return creds["access_token"]

        flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_path, self.SCOPES)
        creds = flow.run_local_server(port=0)
        token_data = {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
            "expires_at": datetime.now(UTC).timestamp() + creds.expiry.timestamp() - datetime.now(UTC).timestamp()
        }
        with open(self.TOKEN_PATH, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)
        return token_data["access_token"]

    def rechercher_metadata_batch(self, requete="", max_results=100):
        headers = {"Authorization": f"Bearer {self.token}"}
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
        params = {"q": requete, "maxResults": max_results}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print("[ERREUR] Recherche échouée :", response.text)
            return []

        messages = response.json().get("messages", [])
        results = []

        for msg in messages:
            msg_id = msg["id"]
            metadata_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
            metadata_params = {
                "format": "metadata",
                "metadataHeaders": ["From", "Date", "Subject"]
            }
            r = requests.get(metadata_url, headers=headers, params=metadata_params)
            if r.status_code != 200:
                continue

            metadata = r.json()
            headers_list = metadata.get("payload", {}).get("headers", [])
            info = {"id": msg_id, "snippet": metadata.get("snippet", "")}

            for h in headers_list:
                name = h.get("name", "").lower()
                if name == "from":
                    info["expediteur"] = h.get("value")
                elif name == "date":
                    info["date"] = h.get("value")
                elif name == "subject":
                    info["sujet"] = h.get("value")

            results.append(info)

        return results

    def compter_messages_inbox(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        url = "https://gmail.googleapis.com/gmail/v1/users/me/labels/INBOX"

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            label_data = response.json()
            return label_data.get("messagesTotal", 0)
        else:
            print("[ERREUR] Impossible de récupérer le nombre de messages :", response.text)
            return -1

    def get_or_create_label(self, label_name):
        """
        Récupère l'ID d'un label existant ou le crée s'il n'existe pas.
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        url = "https://gmail.googleapis.com/gmail/v1/users/me/labels"

        # Récupération des labels existants
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("[ERREUR] Impossible de récupérer les labels :", response.text)
            return None

        labels = response.json().get("labels", [])
        for label in labels:
            if label["name"].lower() == label_name.lower():
                return label["id"]

        # Création si non trouvé
        payload = {"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
        create_response = requests.post(url, headers=headers, json=payload)
        if create_response.status_code == 200:
            label_id = create_response.json().get("id")
            print(f"[INFO] Label '{label_name}' créé.")
            return label_id
        else:
            print("[ERREUR] Création du label échouée :", create_response.text)
            return None

    def ajouter_label(self, message_id, label_name):
        """
        Applique un label à un message donné.
        """
        label_id = self.get_or_create_label(label_name)
        if not label_id:
            print(f"[ERREUR] Impossible d'appliquer le label '{label_name}'")
            return False

        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify"
        payload = {
            "addLabelIds": [label_id]
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"[✔] Label '{label_name}' appliqué au message {message_id}")
            return True
        else:
            print(f"[ERREUR] Échec de l'ajout du label '{label_name}' :", response.text)
            return False
