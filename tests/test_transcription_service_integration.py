import pytest
from services.transcription_service import TranscriptionService

def test_lire_emails_fathom_direct():
    service = TranscriptionService()
    agenda_map = service.calendar.get_events_map()

    print("\n🗓️ Titre des événements du calendrier :")
    for k in agenda_map:
        print(f"- {k}")

    reunions = service.lire_emails_fathom(agenda_map, limit=5)

    assert isinstance(reunions, list), "❌ Le résultat n'est pas une liste."
    assert reunions, "❌ La liste des réunions est vide."

    print(f"\n✅ {len(reunions)} transcription(s) analysée(s) :")

    for r in reunions:
        print("\n==================== TRANSCRIPTION ====================")
        print(f"📝 Titre              : {r['titre']}")
        print(f"📅 Date               : {r['date']}")
        print(f"🕒 Heure              : {r['heure']}")
        print(f"🧠 Conclusions        :\n{r['conclusions']}\n")
        print(f"📌 Sujets abordés     :\n{r['sujets']}\n")
        print(f"🧭 Prochaines étapes  :\n{r['prochaines étapes']}\n")

        if "texte_complet" in r:
            print(f"📄 Texte brut complet :\n{r['texte_complet'][:500]}...\n")

        assert isinstance(r["titre"], str), "❌ Le titre n'est pas une chaîne."
        assert r["titre"] != "(Titre non trouvé)", "❌ Titre non extrait correctement"

        if r["date"] == "(Date inconnue)":
            print("⚠️ Aucune correspondance trouvée dans agenda_map pour :", r["titre"])

        assert r["date"] != "(Date inconnue)", "❌ Date non extraite correctement"
        assert r["conclusions"] != "(Non renseigné)", "❌ Conclusions manquantes"
        assert r["sujets"] != "(Non renseigné)", "❌ Sujets manquants"
        assert r["prochaines étapes"] != "(Non renseigné)", "❌ Prochaines étapes manquantes"

def test_sync_transcriptions_limit_1():
    service = TranscriptionService()
    paths = service.sync_transcriptions(limit=1)

    print("\n✅ Transcriptions synchronisées (1 attendue) :")
    for path in paths:
        print(f"📄 {path}")

    assert isinstance(paths, list), "❌ Le résultat n'est pas une liste de fichiers."
    assert len(paths) == 1, f"❌ Une seule transcription était attendue, mais {len(paths)} ont été générées."
    assert paths[0].endswith(".md"), "❌ Le fichier généré n'est pas un fichier .md."
