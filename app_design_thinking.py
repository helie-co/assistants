import streamlit as st
from io import StringIO
import docx2txt
import PyPDF2
from clients.gpt_client import GPTClient

st.set_page_config(page_title="Design Thinking avec IA", layout="wide")

# ---------- Utilitaires de lecture de fichiers ----------

def extract_text(file):
    if file.type == "text/plain":
        return file.read().decode("utf-8")
    elif file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return docx2txt.process(file)
    else:
        return ""

# ---------- Appel GPT pour générer les verbatims ----------

def generate_verbatims(transcript_text: str) -> str:
    if not transcript_text.strip():
        return "⛔ Transcription vide. Aucun verbatim généré."

    # Limiter à 15000 caractères pour éviter les timeouts
    transcript_text = transcript_text[:15000]

    gpt = GPTClient()

    prompt = f"""
📌 Ta mission :
Sélectionner 2 à 3 verbatims forts parmi les phrases entendues ou prononcées dans la scène, en te concentrant sur les aspects suivants :
- Émotions exprimées (stress, colère, inquiétude, soulagement…)
- Blocages ou frustrations rencontrés (outils, procédures, incompréhensions…)
- Détournements ou bricolages mis en place par les interlocuteurs pour faire avancer le processus

Pour chaque verbatim sélectionné, indique clairement :
- Le verbatim exact
- Qui parle (Client, Conseiller, autre…)
- À quel moment du parcours cela se situe (accueil, déclaration, suite, etc.)
- Pourquoi ce verbatim est marquant (émotion forte, problème récurrent, solution de contournement, etc.)

📝 Tu ne dois garder que les phrases les plus révélatrices. Évite les généralités ou les reformulations.
👉 Voici la transcription à analyser :
{transcript_text.strip()}
"""

    try:
        return gpt.complete(
            prompt=prompt,
            system_prompt="Tu es un expert en Design Thinking et en analyse d’entretiens utilisateurs.",
            temperature=0.5,
            max_tokens=1000,
            timeout=60.0  # ← timeout augmenté ici
        )
    except Exception as e:
        return f"❌ Erreur lors de la génération des verbatims : {e}"

# ---------- Interface principale ----------

st.title("Assistant IA UX")
st.markdown("Une application basée sur les étapes du Design Thinking enrichies par l'IA.")

tabs = st.tabs(["🧠 Empathie", "🎯 Définition", "💡 Idéation", "🛠️ Prototype", "🧪 Test"])

# ---------- Onglet 1 : Empathie ----------
with tabs[0]:
    st.header("Étape 1 : Empathie")
    st.markdown("Importez une transcription d’entretien utilisateur au format `.txt`, `.pdf`, ou `.docx`.")

    uploaded_file = st.file_uploader("📎 Fichier de transcription", type=["txt", "pdf", "docx"])

    if uploaded_file:
        st.success(f"✅ Fichier reçu : {uploaded_file.name}")
        transcript_text = extract_text(uploaded_file)
        st.text_area("📝 Contenu de la transcription", transcript_text, height=300)

        # Appel GPT pour générer les verbatims
        st.markdown("---")
        st.subheader("🎤 Verbatims générés")

        with st.spinner("Analyse du transcript en cours…"):
            verbatims = generate_verbatims(transcript_text)
        st.markdown(verbatims)

# ---------- Autres onglets (vides pour l’instant) ----------
with tabs[1]:
    st.header("Étape 2 : Définition")
    st.info("Contenu à venir.")

with tabs[2]:
    st.header("Étape 3 : Idéation")
    st.info("Contenu à venir.")

with tabs[3]:
    st.header("Étape 4 : Prototype")
    st.info("Contenu à venir.")

with tabs[4]:
    st.header("Étape 5 : Test")
    st.info("Contenu à venir.")
