import streamlit as st
import os
import glob
import re
import trafilatura
import base64
import yt_dlp
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Parasecurity | AI Lab", page_icon="✨", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1F1F1F; font-family: 'Google Sans', Arial, sans-serif; }
    header { visibility: hidden; }
    .stTextArea textarea, .stTextInput input {
        background-color: #F0F4F9 !important; border: none !important;
        border-radius: 24px !important; padding: 16px !important;
    }
    .stButton>button { 
        border-radius: 24px !important; width: 100%; 
        height: 50px; font-weight: bold;
    }
    div.stButton > button:first-child {
        background-color: #1a73e8 !important; color: white !important; border: none !important;
    }
    .stMetric { background-color: #FFFFFF; padding: 10px; border-radius: 16px; border: 1px solid #E1E5EA; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1a73e8;'>✨ Parasecurity Lab</h1>", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "analysis_report" not in st.session_state: st.session_state.analysis_report = ""
if "selected_lang" not in st.session_state: st.session_state.selected_lang = "Ελληνικά 🇬🇷"

# --- 3. INITIALIZE GROQ ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing API Key in Secrets.")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.sidebar.markdown("### ⚙️ Engine Settings")
selected_model_id = st.sidebar.selectbox("Model:", ["llama-3.3-70b-versatile", "llama-3.1-405b-reasoning"])

# --- 4. INPUT INTERFACE ---
source = st.radio("Επιλογή Πηγής:", ["📝 Κείμενο", "🔗 YouTube", "📰 Web", "🖼️ Εικόνα"], horizontal=True)

user_payload = None
image_payload = None

if source == "📝 Κείμενο":
    user_payload = st.text_area("Κείμενο:", placeholder="Επικολλήστε εδώ...", height=200)

elif source == "🔗 YouTube":
    user_payload = st.text_input("YouTube URL:", placeholder="https://youtube.com/watch?v=...")

elif source == "📰 Web":
    user_payload = st.text_input("Link Άρθρου:", placeholder="https://news-site.com/article...")

elif source == "🖼️ Εικόνα":
    up_file = st.file_uploader("Ανεβάστε Εικόνα:", type=["jpg", "png", "jpeg"])
    if up_file:
        st.image(up_file, width=250)
        image_payload = {"mime_type": up_file.type, "data": up_file.read()}


# ─────────────────────────────────────────────────────────────
# HELPER: extract video_id from any YouTube URL format
# ─────────────────────────────────────────────────────────────
def extract_video_id(url: str) -> str:
    if "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("youtu.be/")[-1].split("?")[0]
    if "shorts/" in url:
        return url.split("shorts/")[-1].split("?")[0]
    return url.split("/")[-1]


# ─────────────────────────────────────────────────────────────
# HELPER: transcribe one audio file via Groq Whisper,
#         splitting with ffmpeg if it exceeds 24 MB
# ─────────────────────────────────────────────────────────────
import time
import urllib.request
import json as _json

# ─────────────────────────────────────────────────────────────
# AssemblyAI fallback transcription
# Free tier: $50 credits (~300+ hours). Get key at assemblyai.com
# ─────────────────────────────────────────────────────────────
ASSEMBLYAI_KEY = st.secrets.get("ASSEMBLYAI_API_KEY", "")
ASSEMBLYAI_BASE = "https://api.assemblyai.com/v2"

def _assemblyai_transcribe(file_path: str, status_obj) -> str:
    """Upload file to AssemblyAI and poll until transcript is ready."""
    if not ASSEMBLYAI_KEY:
        raise RuntimeError(
            "AssemblyAI fallback is not configured. "
            "Add ASSEMBLYAI_API_KEY to your Streamlit secrets. "
            "Get a free key at https://www.assemblyai.com"
        )

    headers = {"authorization": ASSEMBLYAI_KEY, "content-type": "application/json"}

    # Step 1 — upload the audio file
    status_obj.write("☁️ Uploading audio to AssemblyAI…")
    with open(file_path, "rb") as f:
        audio_data = f.read()

    upload_req = urllib.request.Request(
        f"{ASSEMBLYAI_BASE}/upload",
        data=audio_data,
        headers={"authorization": ASSEMBLYAI_KEY, "content-type": "application/octet-stream"},
        method="POST"
    )
    with urllib.request.urlopen(upload_req) as resp:
        upload_url = _json.loads(resp.read())["upload_url"]

    # Step 2 — request transcription (enable language detection for Greek support)
    transcript_req = urllib.request.Request(
        f"{ASSEMBLYAI_BASE}/transcript",
        data=_json.dumps({
            "audio_url": upload_url,
            "language_detection": True   # auto-detects Greek, English, etc.
        }).encode(),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(transcript_req) as resp:
        transcript_id = _json.loads(resp.read())["id"]

    # Step 3 — poll until done
    status_obj.write("🧠 AssemblyAI is transcribing…")
    poll_url = f"{ASSEMBLYAI_BASE}/transcript/{transcript_id}"
    poll_headers = {"authorization": ASSEMBLYAI_KEY}

    for _ in range(120):   # max ~4 minutes of polling
        time.sleep(2)
        poll_req = urllib.request.Request(poll_url, headers=poll_headers)
        with urllib.request.urlopen(poll_req) as resp:
            result = _json.loads(resp.read())

        if result["status"] == "completed":
            return result["text"]
        if result["status"] == "error":
            raise RuntimeError(f"AssemblyAI error: {result.get('error', 'unknown')}")

    raise RuntimeError("AssemblyAI transcription timed out after 4 minutes.")


# ─────────────────────────────────────────────────────────────
# Primary transcription via Groq Whisper, with automatic
# AssemblyAI fallback on 429 rate-limit errors
# ─────────────────────────────────────────────────────────────
def _transcribe_one_file(file_path: str, label: str, status_obj) -> str:
    """Try Groq Whisper first; fall back to AssemblyAI on 429."""
    try:
        with open(file_path, "rb") as f:
            ts = client.audio.transcriptions.create(
                file=(os.path.basename(file_path), f.read()),
                model="whisper-large-v3"
            )
        return ts.text

    except Exception as e:
        err_str = str(e)
        if "429" not in err_str and "rate_limit" not in err_str.lower():
            raise  # not a rate-limit — propagate immediately

        status_obj.write(
            f"⚠️ Groq Whisper rate limit hit on {label}. "
            "Switching to AssemblyAI fallback (no wait needed)…"
        )
        return _assemblyai_transcribe(file_path, status_obj)


def transcribe_audio(audio_path: str, video_id: str, status_obj) -> str:
    # ── Step 1: compress to 32 kbps mono MP3 ──────────────────
    compressed_path = f"compressed_{video_id}.mp3"
    status_obj.write("🔧 Compressing audio to 32 kbps mono MP3…")
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", audio_path,
         "-ar", "16000", "-ac", "1", "-b:a", "32k",
         compressed_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg compression failed: {result.stderr.decode()}")

    file_size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
    status_obj.write(f"📦 Compressed size: {file_size_mb:.1f} MB")

    # ── Step 2: single file if small enough ───────────────────
    if file_size_mb <= 24:
        status_obj.write("🧠 Transcribing with Whisper AI…")
        try:
            return _transcribe_one_file(compressed_path, "full audio", status_obj)
        finally:
            if os.path.exists(compressed_path):
                os.remove(compressed_path)

    # ── Step 3: split into 5-min chunks ───────────────────────
    status_obj.write(f"✂️ File is {file_size_mb:.1f} MB — splitting into 5-min chunks…")
    chunk_pattern = f"chunk_{video_id}_%03d.mp3"
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", compressed_path,
         "-f", "segment", "-segment_time", "300",
         "-c", "copy", chunk_pattern],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
    )
    if os.path.exists(compressed_path):
        os.remove(compressed_path)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg chunking failed: {result.stderr.decode()}")

    chunks = sorted(glob.glob(f"chunk_{video_id}_*"))
    if not chunks:
        raise RuntimeError("ffmpeg produced no chunk files.")

    full_transcript = ""
    progress_bar = st.progress(0)
    for i, chunk in enumerate(chunks):
        chunk_mb = os.path.getsize(chunk) / (1024 * 1024)
        label = f"part {i+1}/{len(chunks)}"
        status_obj.write(f"🧠 Transcribing {label} ({chunk_mb:.1f} MB)…")
        try:
            full_transcript += _transcribe_one_file(chunk, label, status_obj) + " "
        finally:
            if os.path.exists(chunk):
                os.remove(chunk)
        progress_bar.progress((i + 1) / len(chunks))

    return full_transcript.strip()


# ─────────────────────────────────────────────────────────────
# HELPER: download audio from YouTube using yt-dlp with
#         multiple client disguises to beat bot-detection
# ─────────────────────────────────────────────────────────────
def download_youtube_audio(url: str, video_id: str) -> str:
    ydl_opts = {
        # Prefer small m4a; fall back to best available
        "format": "worstaudio[ext=m4a]/m4a/worstaudio/bestaudio/best",
        "outtmpl": f"tmp_audio_{video_id}.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "nocheckcertificate": True,
        # Rotate through client disguises: TV → Android → iOS → mobile web
        "extractor_args": {
            "youtube": {"player_client": ["tv", "android", "ios", "mweb"]}
        },
        # Force IPv4 — helps on datacentres where IPv6 is blocked
        "source_address": "0.0.0.0",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    files = glob.glob(f"tmp_audio_{video_id}.*")
    if not files:
        raise RuntimeError("No audio file was downloaded.")
    return files[0]


# ─────────────────────────────────────────────────────────────
# HELPER: full YouTube pipeline
#   1. Try subtitle API  →  instant, no download
#   2. Try yt-dlp audio download + Whisper transcription
# ─────────────────────────────────────────────────────────────
def process_youtube(url: str, status_obj) -> str:
    video_id = extract_video_id(url)

    # ── Step 1: subtitles ──
    status_obj.write("🔍 Checking for subtitles…")
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            t_obj = transcript_list.find_transcript(["el", "en"])
        except Exception:
            # Fall back to whatever language is available
            t_obj = next(iter(transcript_list))
        transcript = t_obj.fetch()
        text = " ".join(item["text"] for item in transcript)
        status_obj.write("✅ Subtitles loaded successfully.")
        return text
    except Exception:
        pass  # No subtitles — continue to audio extraction

    # ── Step 2: audio download + Whisper ──
    status_obj.write("🎧 No subtitles found — downloading audio track…")
    audio_path = None
    try:
        audio_path = download_youtube_audio(url, video_id)
        text = transcribe_audio(audio_path, video_id, status_obj)
        status_obj.write("✅ Audio transcribed successfully.")
        return text
    except Exception as e:
        err = str(e)
        if "DRM" in err:
            raise RuntimeError(
                "🔒 DRM-protected video — the owner has encrypted this content. "
                "Record the audio manually and upload it as text."
            )
        if "403" in err or "Sign in" in err or "bot" in err.lower():
            raise RuntimeError(
                "⚠️ YouTube blocked the server from downloading this video. "
                "Try a different video, or paste the transcript manually in the Text tab."
            )
        raise RuntimeError(f"Audio extraction failed: {err}")
    finally:
        # Always clean up temp files
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)


# ─────────────────────────────────────────────────────────────
# 5. THE SINGLE MAGIC BUTTON
# ─────────────────────────────────────────────────────────────
if st.button("🚀 Έναρξη Πλήρους Ανάλυσης"):
    if not user_payload and not image_payload:
        st.warning("Παρακαλώ εισάγετε κάποιο περιεχόμενο πρώτα!")
    else:
        with st.status("Εκτέλεση Διεργασιών…", expanded=True) as status:
            final_text = ""
            try:
                # ── STEP A: SCRAPING ──────────────────────────────────
                if source == "🔗 YouTube":
                    # Validate URL
                    if not any(k in user_payload for k in ["youtube.com", "youtu.be", "shorts/"]):
                        st.error("⚠️ Δεν φαίνεται να είναι έγκυρο YouTube URL.")
                        st.stop()
                    final_text = process_youtube(user_payload, status)

                elif source == "📰 Web":
                    status.write("🌐 Ανάγνωση σελίδας…")
                    downloaded = trafilatura.fetch_url(user_payload)
                    final_text = trafilatura.extract(downloaded) or ""
                    if not final_text:
                        raise RuntimeError("Αποτυχία εξαγωγής περιεχομένου από τη σελίδα.")
                    status.write("✅ Άρθρο ανακτήθηκε.")

                elif source == "📝 Κείμενο":
                    final_text = user_payload

                # ── STEP B: AI ANALYSIS ───────────────────────────────
                status.write("🧠 Ο κινητήρας AI αναλύει το περιεχόμενο…")

                sys_prompt = """You are a professional Forensic Investigator AI.

STRICT OUTPUT FORMAT — follow exactly, no exceptions:
<GREEK> [Full analysis in Greek] </GREEK>
<ENGLISH> [Full analysis in English] </ENGLISH>
SCORE: [integer 0-100]

Do NOT add any other headers, labels, or text outside these tags."""

                if source == "🖼️ Εικόνα":
                    b64_img = base64.b64encode(image_payload["data"]).decode("utf-8")
                    response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": [
                                {"type": "text", "text": "Analyze this image for propaganda, manipulation, or misinformation."},
                                {"type": "image_url", "image_url": {"url": f"data:{image_payload['mime_type']};base64,{b64_img}"}}
                            ]}
                        ],
                        temperature=0.1
                    )
                else:
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": (
                                "Analyze the following content for propaganda, factual accuracy, "
                                f"and manipulation techniques:\n\n{final_text}"
                            )}
                        ],
                        model=selected_model_id,
                        temperature=0.1
                    )

                st.session_state.analysis_report = response.choices[0].message.content
                status.update(label="✅ Η ανάλυση ολοκληρώθηκε!", state="complete", expanded=False)

            except Exception as e:
                st.error(str(e))

# ─────────────────────────────────────────────────────────────
# 6. DISPLAY RESULTS
# ─────────────────────────────────────────────────────────────
if st.session_state.analysis_report:
    report = st.session_state.analysis_report

    # Score
    s_match = re.search(r"SCORE:\s*(\d+)", report)
    score = int(s_match.group(1)) if s_match else 50
    color = "#1E8E3E" if score > 70 else "#F9AB00" if score > 40 else "#D93025"

    st.markdown(
        f"<div class='stMetric'><strong>Αξιοπιστία:</strong> "
        f"<span style='color:{color}; font-size:26px; font-weight:bold;'>{score}%</span></div>",
        unsafe_allow_html=True
    )

    # Parse language sections
    gr_match = re.search(r"<GREEK>(.*?)</GREEK>", report, re.DOTALL | re.IGNORECASE)
    en_match = re.search(r"<ENGLISH>(.*?)</ENGLISH>", report, re.DOTALL | re.IGNORECASE)
    gr_txt = gr_match.group(1).strip() if gr_match else "Σφάλμα ανάκτησης ελληνικού κειμένου."
    en_txt = en_match.group(1).strip() if en_match else "Error retrieving English analysis."

    c1, c2, _ = st.columns([1, 1, 3])
    if c1.button("Ελληνικά"): st.session_state.selected_lang = "Ελληνικά 🇬🇷"
    if c2.button("English"):  st.session_state.selected_lang = "English 🇬🇧"

    st.markdown(
        f"<div style='background-color:#F0F4F9; padding:25px; border-radius:20px; "
        f"border-left:8px solid {color};'>"
        f"{gr_txt if st.session_state.selected_lang == 'Ελληνικά 🇬🇷' else en_txt}</div>",
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────────────────────
# SIDEBAR FOOTER
# ─────────────────────────────────────────────────────────────
st.sidebar.divider()
if st.sidebar.button("🗑️ Reset"):
    st.session_state.analysis_report = ""
    st.rerun()
st.sidebar.caption("© 2026 Parasecurity Labs")