import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components
from clients.github_client import GitHubClient
from data.action import Action

st.set_page_config(page_title="📋 Backlog des actions", layout="wide")
st.title("📋 Backlog des actions extraites")

github = GitHubClient()
backlog_path = "MH/backlog.json"

@st.cache_data
def load_actions() -> list[Action]:
    content = github.get_file(backlog_path)
    if isinstance(content, bytes):  # ✅ Ajout pour corriger les caractères bizarres
        content = content.decode("utf-8")
    data = json.loads(content)
    return [Action(**item) for item in data]

actions = load_actions()

if not actions:
    st.warning("Aucune action à afficher.")
else:
    df = pd.DataFrame([a.__dict__ for a in actions])

    # ✅ Conversion et tri par date décroissante
    df["📅 Date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("📅 Date", ascending=False)
    df["📅 Date"] = df["📅 Date"].dt.strftime("%Y-%m-%d")

    # 🔍 Lien GitHub cliquable
    df["🔍"] = df["source"].apply(
        lambda path: f'<a href="https://github.com/{github.owner}/{github.repo}/blob/{github.branch}/{path}" target="_blank">🔍</a>'
    )

    # ✅ Marquer comme "terminée" (client-side seulement)
    df["✅"] = [
        '<span style="color:green; cursor:pointer;" onclick="this.closest(\'tr\').children[5].innerText = \'terminée\'">✅</span>'
        for _ in df.index
    ]

    # ❌ Supprimer ligne (client-side seulement)
    df["❌"] = [
        '<span style="color:red; cursor:pointer;" onclick="this.closest(\'tr\').remove()">❌</span>'
        for _ in df.index
    ]

    # Renommage des colonnes
    df = df.rename(columns={
        "sujet": "📝 Sujet",
        "demandeur": "🙋‍♀️ Demandeur",
        "porteur": "👤 Porteur",
        "tag": "🏷️ Tag",
        "statut": "⏱️ Statut"
    })

    # Réorganisation des colonnes
    df_display = df[[
        "📝 Sujet", "🙋‍♀️ Demandeur", "👤 Porteur",
        "📅 Date", "🏷️ Tag", "⏱️ Statut", "🔍", "✅", "❌"
    ]]

    # CSS pour mise en page
    style = """
    <style>
    table.dataframe {
        width: 100%;
        border-collapse: collapse;
        font-family: Arial, sans-serif;
        font-size: 15px;
    }
    table.dataframe th, table.dataframe td {
        border: 1px solid #ccc;
        padding: 8px;
    }
    table.dataframe th {
        background-color: #f2f2f2;
        text-align: center;
    }
    table.dataframe td:nth-child(1) {
        text-align: left;
        width: 35%;
    }
    table.dataframe td:nth-child(2) {
        width: 15%;
    }
    table.dataframe td:nth-child(4) {
        width: 10%;
    }
    table.dataframe td:nth-child(6) {
        width: 10%;
    }
    table.dataframe td {
        text-align: center;
    }
    </style>
    """

    # Affichage dans Streamlit
    html_table = style + df_display.to_html(escape=False, index=False, classes="dataframe")
    components.html(html_table, height=700, scrolling=True)
