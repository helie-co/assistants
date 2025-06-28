import os
import json
import requests
from datetime import datetime, UTC
from google_auth_oauthlib.flow import InstalledAppFlow


def get_google_access_token(token_path, client_secret, scopes):
    if os.path.exists(token_path):
        with open(token_path, "r", encoding="utf-8") as f:
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
                    with open(token_path, "w", encoding="utf-8") as f:
                        json.dump(creds, f, indent=2)
                    return creds["access_token"]
    flow = InstalledAppFlow.from_client_secrets_file(client_secret, scopes)
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
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2)
    return token_data["access_token"]
