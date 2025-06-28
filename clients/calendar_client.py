import os
import requests
from datetime import datetime, timedelta, UTC
from utils.auth import get_google_access_token

AGENDA_TOKEN_PATH = 'auth/token/calendar_token.json'
AGENDA_CLIENT_SECRET = 'auth/calendar_credentials.json'
SCOPES_AGENDA = ['https://www.googleapis.com/auth/calendar.readonly']


class CalendarClient:
    def __init__(self):
        self.token = get_google_access_token(AGENDA_TOKEN_PATH, AGENDA_CLIENT_SECRET, SCOPES_AGENDA)
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def get_events_map(self, past_days=7, future_days=30) -> dict:
        time_min = (datetime.now(UTC) - timedelta(days=past_days)).isoformat()
        time_max = (datetime.now(UTC) + timedelta(days=future_days)).isoformat()
        url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
        params = {
            "timeMin": time_min,
            "timeMax": time_max,
            "maxResults": 250,
            "singleEvents": "true",
            "orderBy": "startTime"
        }
        response = requests.get(url, headers=self.headers, params=params, verify=False)
        if response.status_code != 200:
            return {}

        events = response.json().get("items", [])
        agenda_map = {}
        for event in events:
            title = event.get("summary", "").strip()
            start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
            end = event.get("end", {}).get("dateTime") or event.get("end", {}).get("date")
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
