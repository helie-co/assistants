import streamlit as st
from clients.gpt_client import GPTClient

def generate_cpn_from_empathy_map(empathy_map: str) -> str:
    gpt = GPTClient()

    prompt = f"""
À partir de la carte d’empathie suivante :

{empathy_map.strip()}

🎯 Ta mission :
Génère une liste de 4 à 6 formulations de CPN (Comment Pourrions-Nous...), qui traduisent les tensions ou besoins croisés des utilisateurs.
Chaque CPN doit être clair, spécifique, et ouvrir des pistes de solution

Exemples de formulation :
- Comment pourrions-nous simplifier…
- Comment pourrions-nous permettre à…
- Comment pourrions-nous éviter que…

Puis sélectionne 2 à 3 CPN à fort potentiel :
- Fort impact (pour les deux parties)
- Faciles à prototyper ou à tester rapidement
- Sources de valeur directe

Termine par une synthèse argumentée expliquant pourquoi ces CPN sont prioritaires pour un atelier d’idéation ou de prototypage rapide.
"""

    try:
        return gpt.complete(
            prompt=prompt,
            system_prompt="Tu es expert en Design Thinking. Structure ta réponse avec des bullets, des sauts de ligne et une synthèse claire.",
            temperature=0.5,
            max_tokens=1000,
            timeout=60.0
        )
    except Exception as e:
        return f"❌ Erreur lors de la génération des CPN : {e}"

def render():
    st.header("Étape 2 : Définition")
    st.markdown("🎯 Reformuler les besoins en opportunités d’innovation via des CPN (Comment Pourrions-Nous...)")

    if "empathy_map" not in st.session_state or not st.session_state.empathy_map.strip():
        st.warning("⚠️ Aucune carte d’empathie trouvée. Veuillez compléter l’étape 1 avant.")
        return

    if "cpn_output" not in st.session_state:
        st.session_state.cpn_output = ""

    st.markdown("## 1️⃣ Carte d’empathie actuelle")
    st.markdown(st.session_state.empathy_map)

    st.markdown("---")
    st.markdown("## 2️⃣ Générer les CPN automatiquement")

    if st.button("💡 Générer des CPN à partir de la carte d’empathie"):
        with st.spinner("Analyse de la carte et génération en cours…"):
            st.session_state.cpn_output = generate_cpn_from_empathy_map(st.session_state.empathy_map)

    if st.session_state.cpn_output:
        st.markdown("### ✨ CPN proposés")
        st.markdown(st.session_state.cpn_output)
