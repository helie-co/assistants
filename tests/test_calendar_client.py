import pytest
from datetime import datetime
from clients.calendar_client import CalendarClient  # adapte si besoin

def test_calendar_integration_fetch_events():
    client = CalendarClient()
    agenda = client.get_events_map(past_days=1, future_days=2)

    assert isinstance(agenda, dict), "❌ Le résultat n'est pas un dictionnaire."

    if agenda:
        sample_title, sample_event = next(iter(agenda.items()))
        print(f"\n🎯 Exemple d'événement récupéré : {sample_title}")
        print(f"📅 Date : {sample_event['date']}")
        print(f"🕒 Heure : {sample_event['heure']}")
        print(f"📍 Lieu : {sample_event['location']}")
        print(f"🔗 Lien : {sample_event['link']}")
        
        assert "date" in sample_event
        assert "heure" in sample_event
        assert "datetime" in sample_event
        assert isinstance(sample_event["datetime"], datetime)
        assert isinstance(sample_event["date"], str)
        assert isinstance(sample_event["heure"], str)

def test_get_events_map_avec_gestion_npai():
    client = CalendarClient()
    agenda_map = client.get_events_map(past_days=30, future_days=30)

    assert isinstance(agenda_map, dict), "❌ Le résultat n'est pas un dictionnaire."
    assert agenda_map, "❌ Aucun événement récupéré depuis l'agenda."

    titres_npai = [t for t in agenda_map if "gestion des npai" in t.lower()]

    print("\n📅 Événements contenant 'gestion des npai' :")
    for titre in titres_npai:
        event = agenda_map[titre]
        print(f"✅ {titre}")
        print(f"   📅 Date    : {event['date']}")
        print(f"   🕒 Heure   : {event['heure']}")
        print(f"   📍 Lieu    : {event.get('location', '')}")
        print(f"   🔗 Lien    : {event.get('link', '')}")
        print("")

    assert len(titres_npai) > 0, "❌ Aucun événement contenant 'gestion des npai' n’a été trouvé."
