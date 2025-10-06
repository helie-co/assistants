# app-transcription.py
import os
import tempfile
import sys
from datetime import timedelta

import streamlit as st
from pydub import AudioSegment
from openai import OpenAI

# (Optionnel) compat avec un GPTClient local si présent
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from clients.gpt_client import GPTClient  # noqa: F401
except Exception:
    GPTClient = None

SUPPORTED_FORMATS = [".mp3", ".mp4", ".wav", ".m4a"]  # volontairement sans .mkv

# ---------- Utils ----------
def format_ms(ms: int) -> str:
    """Retourne mm:ss.mmm pour l'UI."""
    return str(timedelta(milliseconds=ms))[:-3]


def transcribe_segment(openai_client: OpenAI, segment_path: str, language: str) -> str:
    with open(segment_path, "rb") as f:
        resp = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language=language,
        )
    return getattr(resp, "text", "")


def split_and_transcribe(openai_client: OpenAI, file_path: str, segment_ms: int, language: str, progress_cb=None):
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Format non supporté: {ext}. Autorisés: {', '.join(SUPPORTED_FORMATS)}")

    # 1) Conversion éventuelle -> mp3
    temp_mp3_path = None
    if ext != ".mp3":
        audio = AudioSegment.from_file(file_path, format=ext[1:])
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_mp3:
            audio.export(tmp_mp3.name, format="mp3")
            mp3_path = tmp_mp3.name
            temp_mp3_path = mp3_path
    else:
        mp3_path = file_path

    # 2) Découpage
    audio_mp3 = AudioSegment.from_mp3(mp3_path)
    total_ms = len(audio_mp3)
    segments_text = []
    n_segments = (total_ms + segment_ms - 1) // segment_ms

    for i, start in enumerate(range(0, total_ms, segment_ms), start=1):
        end = min(start + segment_ms, total_ms)
        seg = audio_mp3[start:end]

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_seg:
            seg.export(tmp_seg.name, format="mp3")
            seg_path = tmp_seg.name

        try:
            text = transcribe_segment(openai_client, seg_path, language=language)
            segments_text.append(text)
        finally:
            try:
                os.unlink(seg_path)
            except Exception:
                pass

        if progress_cb:
            progress_cb(i, n_segments, start, end, total_ms)

    return " ".join(segments_text).strip(), temp_mp3_path


# ---------- Streamlit UI ----------
st.set_page_config(page_title="Transcription audio/vidéo (Whisper)", layout="centered")
st.title("🎙️ Transcription audio/vidéo (OpenAI Whisper)")

# Lecture stricte depuis st.secrets (cloud/local)
API_KEY = st.secrets.get("OPENAI_API_KEY", "")
if not API_KEY:
    st.error(
        "Aucune clé OpenAI détectée. Ajoutez-la dans `.streamlit/secrets.toml` (local) "
        "ou dans **Settings → Secrets** sur streamlit.app :\n\n"
        "```\nOPENAI_API_KEY = \"sk-...\"\n```"
    )
    st.stop()

with st.expander("⚙️ Paramètres", expanded=True):
    language = st.selectbox("Langue à forcer (améliore la précision)", ["fr", "en", "es", "de", "it"], index=0)
    seg_minutes = st.slider("Taille des segments (minutes)", min_value=3, max_value=15, value=10, step=1)

uploaded = st.file_uploader(
    "Déposez un fichier audio/vidéo (mp3, mp4, wav, m4a)", type=["mp3", "mp4", "wav", "m4a"]
)

placeholder_log = st.empty()

if uploaded is not None:
    st.write(f"**Fichier** : `{uploaded.name}` — **Taille** : {uploaded.size/1024/1024:.2f} Mo")
    if st.button("🚀 Lancer la transcription", type="primary"):
        # Sauvegarde du fichier uploadé
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.name)[1]) as tmp_in:
            tmp_in.write(uploaded.getbuffer())
            tmp_in_path = tmp_in.name

        client = OpenAI(api_key=API_KEY)
        seg_ms = seg_minutes * 60 * 1000

        prog = st.progress(0, text="Préparation…")
        log_lines = []

        def on_progress(i, n, start, end, total):
            pct = int(i / n * 100)
            prog.progress(pct, text=f"Segment {i}/{n} — {format_ms(start)} ⟶ {format_ms(end)} / {format_ms(total)}")
            log_lines.append(f"✓ Segment {i}/{n} : {format_ms(start)} - {format_ms(end)}")
            placeholder_log.code("\n".join(log_lines), language="text")

        temp_mp3 = None
        try:
            st.info("Transcription en cours…")
            full_text, temp_mp3 = split_and_transcribe(
                client, tmp_in_path, seg_ms, language=language, progress_cb=on_progress
            )

            prog.progress(100, text="Assemblage du texte…")
            st.success("Transcription terminée ✅")

            st.subheader("📝 Résultat")
            if full_text:
                st.text_area("Transcription (aperçu)", value=full_text, height=300)
                txt_name = f"{os.path.splitext(uploaded.name)[0]}.txt"
                st.download_button(
                    "💾 Télécharger le .txt",
                    data=full_text.encode("utf-8"),
                    file_name=txt_name,
                    mime="text/plain",
                )
            else:
                st.warning("Aucun texte renvoyé par le modèle.")
        except Exception as e:
            st.error(f"Erreur pendant la transcription : {e}")
        finally:
            for p in (tmp_in_path, temp_mp3):
                if p:
                    try:
                        os.unlink(p)
                    except Exception:
                        pass

with st.expander("❓ Notes & conseils"):
    st.markdown(
        """
- **Formats supportés** : `.mp3`, `.mp4`, `.wav`, `.m4a` (les `.mkv` ne sont **pas** gérés ici).
- **Segmentation** : 10 min par défaut (réglable 3–15 min).
- **Audio backend** : `pydub` nécessite **ffmpeg** (sur *streamlit.app*, ajoutez `ffmpeg` dans `packages.txt`).
- **Clé OpenAI** : lue **uniquement** via `st.secrets["OPENAI_API_KEY"]` (local ou cloud).
        """
    )
