import os
import json
import streamlit as st
from datetime import datetime, timedelta
import locale
from streamlit import cache_data

from services.email_service import EmailService
from clients.github_client import GitHubClient
from clients.email_client import EmailClient
from services.email_indexer import EmailIndexer

# Chargement de la locale française
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except:
    pass

# Initialisation des services
github = GitHubClient()
email_client = EmailClient()
service = EmailService(github=github, email_client=email_client, context="MH")
indexer = EmailIndexer(github=github, context="MH")

st.set_page_config(page_title="Recherche Emails", layout="wide")
st.title("📬 Recherche dans les Emails (Index GitHub)")

# Rafraîchissement manuel
if st.button("🔄 Rafraîchir l’index"):
    indexer.run()
    cache_data.clear()
    st.success("Index mis à jour à partir des fichiers Markdown.")
    st.rerun()

@st.cache_data
def load_index():
    try:
        return service.get_index()
    except Exception as e:
        st.error(f"Erreur lors du chargement de l’index : {e}")
        return []

def format_date_humaine(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    if dt.date() == now.date():
        return f"Aujourd’hui à {dt.strftime('%Hh%M')}"
    elif dt.date() == (now - timedelta(days=1)).date():
        return f"Hier à {dt.strftime('%Hh%M')}"
    elif dt > now - timedelta(days=7):
        jour = dt.strftime('%A')
        return f"{jour.capitalize()} à {dt.strftime('%Hh%M')}"
    else:
        return dt.strftime('%A %d %B à %Hh%M').capitalize()

def search_emails(query, index):
    terms = query.lower().split()
    results = []
    for item in index:
        searchable = " ".join([
            item.get("title", ""),
            item.get("author", ""),
            item.get("date", ""),
            item.get("summary", ""),
            " ".join(item.get("recipients", [])),
            item.get("file", "")
        ]).lower()
        if all(term in searchable for term in terms):
            results.append(item)
    return results

# Chargement de l'index
index = load_index()
query = st.text_input("💡 Posez une question ou entrez un mot-clé", "")
afficher_archives = st.checkbox("Inclure les emails archivés", value=False)

# Filtrage
if query:
    results = search_emails(query, index)
    if not afficher_archives:
        results = [r for r in results if r.get("status") != "archive"]
    st.markdown(f"### 🔎 {len(results)} résultat(s) trouvé(s)")
else:
    results = [r for r in index if r.get("status") != "archive" or afficher_archives]
    st.markdown(f"### 📁 {len(results)} email(s) affiché(s)")

# Tri
def parse_date_safe(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min

results = sorted(results, key=lambda r: parse_date_safe(r.get("date", "")), reverse=True)

# Affichage par mail
for r in results:
    with st.container():
        c1, c2, c3, c4 = st.columns([1.3, 2.5, 6, 1.2])

        # Date
        c1.markdown(f"🕒 {format_date_humaine(r['date'])}")

        # Auteur + destinataires condensés
        destinataires = r.get("recipients", [])
        max_disp = 3
        if destinataires:
            visible = ", ".join(destinataires[:max_disp])
            hidden = destinataires[max_disp:]
            if hidden:
                destinataires_line = f"{visible} +{len(hidden)}"
            else:
                destinataires_line = visible
        else:
            destinataires_line = "_Aucun destinataire_"
        c2.markdown(f"👤 {r['author']}")
        c2.markdown(f"✉️ _{destinataires_line}_")

        # Sujet + résumé complet ou avec expander
        titre = r.get("title", "(Sans titre)")
        resume = r.get("summary", "*Résumé non disponible*")
        if len(resume) > 300:
            c3.markdown(f"**{titre}**")
            with c3.expander("Voir le résumé complet"):
                st.markdown(resume)
        else:
            c3.markdown(f"**{titre}** · {resume}")

        # Actions : lien et archive
        mail_url = f"https://github.com/helie-co/content/blob/main/{r['file']}"
        c4.markdown(f"[📨 Voir le mail]({mail_url})")

        if r.get("status") != "archive":
            if c4.button("📦 Archiver", key=f"archiver-{r['id']}"):
                try:
                    service.archive_email_by_id(r["id"])
                    cache_data.clear()
                    st.success(f"Email archivé avec succès : {r['title']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l’archivage : {e}")

        st.divider()
