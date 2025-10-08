# app-transcription.py
import os
import io
import time
from pathlib import Path
from datetime import timedelta

import streamlit as st
from openai import OpenAI
from openai import APIConnectionError, RateLimitError, APITimeoutError, BadRequestError, APIStatusError

# ---------------------- Config UI ----------------------
st.set_page_config(page_title="Transcription (Whisper) — Sans FFmpeg", layout="centered")
st.title("🎙️ Transcription audio/vidéo (OpenAI Whisper) — mode sans FFmpeg")

API_KEY = st.secrets.get("OPENAI_API_KEY", "")
if not API_KEY:
    st.error(
        "Aucune clé OpenAI détectée. Ajoutez-la dans `.streamlit/secrets.toml` (local) "
        "ou dans **Manage app → Settings → Secrets** sur streamlit.app :\n\n"
        "```\nOPENAI_API_KEY = \"sk-...\"\n```"
    )
    st.stop()

SUPPORTED_EXT = [".mp3", ".mp4", ".wav", ".m4a"]  # pas de conversion/découpage côté serveur

# ---------------------- Utils ----------------------
def fmt_bytes(num: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if num < 1024.0:
            return f"{num:.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} TB"

def fmt_time_ms(ms: float) -> str:
    return str(timedelta(milliseconds=int(ms)))

def safe_name(name: str) -> str:
    try:
        return name.encode("utf-8", "ignore").decode("utf-8")
    except Exception:
        return "fichier"

# Buffer de logs
if "log_text" not in st.session_state:
    st.session_state["log_text"] = ""

# Un seul placeholder pour les logs (pas de widget à état)
log_placeholder = st.empty()

def append_log(msg: str):
    """Ajoute une ligne au journal d'exécution et rafraîchit l'affichage."""
    st.session_state["log_text"] += (("\n" if st.session_state["log_text"] else "") + msg)
    # Affichage via st.code: pas de gestion d'état de widget, pas d'ID dupliqués
    log_placeholder.code(st.session_state["log_text"], language="text")

# ---------------------- UI paramètres ----------------------
with st.expander("⚙️ Paramètres", expanded=True):
    language = st.selectbox("Langue à forcer (meilleure précision)", ["fr", "en", "es", "de", "it"], index=0)
    request_timeout = st.slider("Timeout requête (secondes)", min_value=30, max_value=300, value=90, step=10)
    verbose_debug = st.toggle("Mode verbeux (debug)", value=False, help="Affiche la trace complète des erreurs")

uploaded = st.file_uploader(
    "Déposez un fichier audio/vidéo (mp3, mp4, wav, m4a) — 200 Mo max sur streamlit.app",
    type=[ext[1:] for ext in SUPPORTED_EXT]
)

# Affiche le journal initial (vide ou existant)
log_placeholder.code(st.session_state["log_text"] or "Journal d’exécution…", language="text")

# ---------------------- Action ----------------------
if uploaded is not None:
    fname = safe_name(uploaded.name)
    fsize = len(uploaded.getbuffer())
    fext = Path(fname).suffix.lower()

    st.write(f"**Fichier** : `{fname}` — **Taille** : {fmt_bytes(fsize)}")
    if fext not in SUPPORTED_EXT:
        st.error(f"Format non supporté : {fext}. Formats acceptés : {', '.join(SUPPORTED_EXT)}")
        st.stop()

    if st.button("🚀 Lancer la transcription", type="primary"):
        client = OpenAI(api_key=API_KEY, timeout=request_timeout)  # timeout global

        start_ts = time.time()
        append_log("Démarrage de la transcription (mode direct, sans conversion ni découpage)…")

        # On lit en BytesIO pour passer un file-like au client
        file_like = io.BytesIO(uploaded.getbuffer())
        file_like.name = fname  # utile pour l'API côté serveur

        with st.status("Transcription en cours…", expanded=True) as status:
            try:
                st.write("➡️ Envoi du fichier à Whisper (appel API)…")
                t0 = time.time()
                resp = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=file_like,
                    language=language,
                    # prompt=None,
                    # temperature=0,
                )
                t_api = time.time() - t0
                append_log(f"Appel API terminé en {t_api:.1f}s.")

                text = getattr(resp, "text", "").strip() if resp else ""
                if not text:
                    append_log("⚠️ Whisper a renvoyé une réponse vide.")
                    st.warning("Aucun texte renvoyé par le modèle.")
                else:
                    append_log(f"✅ Transcription reçue ({len(text)} caractères).")

                status.update(label="Fini", state="complete")

            except (APITimeoutError, APIConnectionError) as net_err:
                append_log("❌ Erreur de réseau / timeout avec l’API OpenAI.")
                if verbose_debug:
                    st.exception(net_err)
                else:
                    st.error(f"Erreur réseau/timeout : {net_err}")
                text = ""
            except RateLimitError as rle:
                append_log("❌ Rate limit atteint (trop de requêtes).")
                if verbose_debug:
                    st.exception(rle)
                else:
                    st.error("Rate limit atteint. Réessaie dans quelques instants.")
                text = ""
            except BadRequestError as bre:
                append_log("❌ Requête invalide (BadRequestError) — souvent un problème de taille/format.")
                if verbose_debug:
                    st.exception(bre)
                else:
                    st.error(f"BadRequest : {bre}")
                text = ""
            except APIStatusError as ase:
                append_log(f"❌ Erreur serveur OpenAI (status {ase.status_code}).")
                if verbose_debug:
                    st.exception(ase)
                else:
                    st.error(f"Erreur OpenAI : status {ase.status_code}")
                text = ""
            except Exception as e:
                append_log("❌ Exception non gérée pendant la transcription.")
                if verbose_debug:
                    st.exception(e)
                else:
                    st.error(f"Erreur : {e}")
                text = ""

        total_s = time.time() - start_ts
        append_log(f"Durée totale du traitement : {fmt_time_ms(total_s * 1000)}")

        st.subheader("📝 Résultat")
        if text:
            st.text_area("Transcription (aperçu)", value=text, height=300, key="result_area", disabled=False)
            out_name = f"{Path(fname).stem}.txt"
            st.download_button("💾 Télécharger le .txt", data=text.encode("utf-8"), file_name=out_name, mime="text/plain")
        else:
            st.info(
                "Pas de transcription.\n\n"
                "💡 Pistes sans FFmpeg :\n"
                "- Réduire la taille/durée du fichier (couper localement en parties < 20–30 min).\n"
                "- Essayer un format **WAV mono 16 kHz** (si ton outil d’enregistrement le permet).\n"
                "- Exécuter l’application **en local** (aucune limite d’upload Streamlit Cloud) puis pousser le .txt."
            )
