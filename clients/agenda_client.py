import os
import json
import requests
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TOKEN_PATH = 'token_agenda.json'
CLIENT_SECRET_PATH = os.getenv("CALENDAR_CREDENTIALS_PATH")


def get_google_calendar_token():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            creds = json.load(f)
            if "access_token" in creds and datetime.now(UTC).timestamp() < creds.get("expires_at", 0):
                return creds["access_token"]
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
                    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
                        json.dump(creds, f, indent=2)
                    return creds["access_token"]
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
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
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2)
    return token_data["access_token"]


class AgendaClient:
    def __init__(self):
        self.token = get_google_calendar_token()

    def get_events_map(self) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"}
        now = datetime.now(UTC)
        params = {
            "timeMin": (now - timedelta(days=7)).isoformat(),
            "timeMax": (now + timedelta(days=30)).isoformat(),
            "singleEvents": True,
            "orderBy": "startTime",
            "maxResults": 250
        }
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            return {}

        agenda_map = {}
        for event in r.json().get("items", []):
            title = event.get("summary", "").strip()
            start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
            end = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")
            if not (start and end):
                continue
            try:
                dt_start = datetime.fromisoformat(start.replace("Z", "+00:00"))
                dt_end = datetime.fromisoformat(end.replace("Z", "+00:00"))
                agenda_map[title] = {
                    "date": dt_start.strftime("%d/%m/%Y"),
                    "heure": f"{dt_start.strftime('%Hh%M')}–{dt_end.strftime('%Hh%M')}",
                    "datetime": dt_start,
                    "location": event.get("location", ""),
                    "link": event.get("hangoutLink", "")
                }
            except:
                continue
        return agenda_map

    def get_event_by_name(self, event_name: str) -> dict | None:
        events = self.get_events_map()
        return events.get(event_name)
