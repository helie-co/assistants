import streamlit as st
import docx2txt
import PyPDF2
from clients.gpt_client import GPTClient

# ---------- Fonctions utilitaires ----------

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

def generate_verbatims(transcript_text: str) -> str:
    if not transcript_text.strip():
        return "⛔ Transcription vide. Aucun verbatim généré."

    transcript_text = transcript_text[:15000]
    gpt = GPTClient()

    prompt = f"""
📌 Ta mission :
Sélectionner 2 à 3 verbatims forts parmi les phrases entendues ou prononcées dans la scène, en te concentrant sur les aspects suivants :
- Émotions exprimées (stress, colère, inquiétude, soulagement…)
- Blocages ou frustrations rencontrés (outils, procédures, incompréhensions…)
- Détournements ou bricolages mis en place par les interlocuteurs pour faire avancer le processus

Pour chaque verbatim sélectionné, indique :
- Le verbatim exact
- Qui parle
- À quel moment du parcours cela se situe
- Pourquoi ce verbatim est marquant

👉 Voici la transcription à analyser :
{transcript_text.strip()}
"""

    try:
        return gpt.complete(
            prompt=prompt,
            system_prompt="Tu es un expert en Design Thinking et en analyse d’entretiens utilisateurs.",
            temperature=0.5,
            max_tokens=1000,
            timeout=60.0
        )
    except Exception as e:
        return f"❌ Erreur lors de la génération des verbatims : {e}"

def generate_empathy_map(verbatims: str) -> str:
    gpt = GPTClient()

    prompt = f"""
À partir du dialogue ou des notes ci-dessous, remplis la grille d’empathie suivante en identifiant au maximum 3 éléments par catégorie :

🔍 Ce que la personne vit : expériences concrètes, faits, éléments observables dans son quotidien.  
💬 Ce qu’elle exprime : propos directs, citations ou formulations verbales.  
😡 Ce qu’elle ressent : émotions perçues ou exprimées, sentiments implicites.  
🧍‍♀️ Ce qu’elle fait : comportements, habitudes, attitudes.  
😟 Douleurs / Irritants : ce qui la gêne, la freine, l’irrite ou la fatigue.  
💡 Besoins / Aspirations : ce qu’elle cherche à obtenir, ses attentes ou objectifs implicites.

Limite-toi à 3 points maximum par section, choisis les plus représentatifs.

Voici le contenu à analyser :
{verbatims.strip()}
"""

    try:
        return gpt.complete(
            prompt=prompt,
            system_prompt="Tu es un expert UX. Ton format doit être clair, synthétique et bien structuré.",
            temperature=0.5,
            max_tokens=800,
            timeout=60.0
        )
    except Exception as e:
        return f"❌ Erreur lors de la génération de la carte d’empathie : {e}"

# ---------- Vue Empathie ----------

def render():
    st.header("Étape 1 : Empathie")
    st.markdown("Comprendre les utilisateurs grâce à l’écoute, l’observation et l’analyse de leurs vécus.")

    if "transcript_text" not in st.session_state:
        st.session_state.transcript_text = ""
    if "verbatims" not in st.session_state:
        st.session_state.verbatims = ""
    if "empathy_map" not in st.session_state:
        st.session_state.empathy_map = ""

    # 1. Importer le fichier
    st.markdown("## 1️⃣ Importer une transcription")
    uploaded_file = st.file_uploader("📎 Fichier .txt, .pdf ou .docx", type=["txt", "pdf", "docx"])
    if uploaded_file:
        transcript = extract_text(uploaded_file)
        st.session_state.transcript_text = transcript
        st.success(f"✅ Fichier importé : {uploaded_file.name}")
        st.text_area("📝 Aperçu du transcript", transcript, height=300)

    # 2. Générer les verbatims
    st.markdown("---")
    st.markdown("## 2️⃣ Extraire des verbatims avec l’IA")

    if st.session_state.transcript_text:
        if st.button("🔍 Générer les verbatims à partir du transcript"):
            with st.spinner("Analyse en cours…"):
                st.session_state.verbatims = generate_verbatims(st.session_state.transcript_text)
    else:
        st.info("👉 Veuillez importer une transcription avant de lancer l’analyse.")

    if st.session_state.verbatims:
        st.markdown("### 🎤 Verbatims extraits")
        st.markdown(st.session_state.verbatims)

    # 3. Générer la carte d’empathie
    st.markdown("---")
    st.markdown("## 3️⃣ Carte d’empathie générée automatiquement")

    if st.session_state.verbatims:
        if st.button("🧠 Générer la carte d’empathie"):
            with st.spinner("Génération de la carte d’empathie…"):
                st.session_state.empathy_map = generate_empathy_map(st.session_state.verbatims)

    if st.session_state.empathy_map:
        st.markdown(st.session_state.empathy_map)
    else:
        st.info("👉 Générez d’abord les verbatims pour débloquer cette étape.")
