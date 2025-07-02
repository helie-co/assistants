import streamlit as st
from pages import empathie_tab, definition_tab, ideation_tab, prototype_tab, test_tab

st.set_page_config(page_title="Design Thinking avec IA", layout="wide")
st.title("Assistant IA UX")
st.markdown("Une application basée sur les étapes du Design Thinking enrichies par l'IA.")

tabs = st.tabs(["🧠 Empathie", "🎯 Définition", "💡 Idéation", "🛠️ Prototype", "🧪 Test"])

with tabs[0]:
    empathie_tab.render()

with tabs[1]:
    definition_tab.render()

with tabs[2]:
    ideation_tab.render()

with tabs[3]:
    prototype_tab.render()

with tabs[4]:
    test_tab.render()
