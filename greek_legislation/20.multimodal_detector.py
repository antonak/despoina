import streamlit as st
import os
import re
import base64
import trafilatura
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Parasecurity | Hybrid Investigator", page_icon="🛡️", layout="wide")

# --- CUSTOM CSS BRANDING ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #d32f2f; color: white; font-weight: bold; }
    .stAlert { border-radius: 10px; }
    .report-header { color: #d32f2f; font-weight: bold; font-size: 24px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Parasecurity Hybrid Investigator")
st.markdown("### Multimedia, Vision & Text Forensic System")
st.caption("Forensic Intelligence Environment | FORTH & TUC Lab")

# --- 2. SESSION STATE (MEMORY) ---
if "content_to_check" not in st.session_state: st.session_state.content_to_check = ""
if "analysis_report" not in st.session_state: st.session_state.analysis_report = ""
if "selected_lang" not in st.session_state: st.session_state.selected_lang = "Ελληνικά 🇬🇷"
if "image_b64" not in st.session_state: st.session_state.image_b64 = None

# --- 3. API KEY VALIDATION ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY is missing from Streamlit Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def encode_image(image_file):
    """Μετατροπή εικόνας σε Base64 για το Vision API."""
    return base64.b64encode(image_file.read()).decode('utf-8')

# --- 4. INPUT PANEL ---
source = st.radio("Select Investigation Source:", 
                  ["📝 Text Analysis", "🔗 YouTube Hybrid", "📰 News Scraper", "🖼️ Visual Analysis", "📁 Media File"], 
                  horizontal=True)

col1, col2 = st.columns([3, 1])

with col1:
    # 1. TEXT
    if source == "📝 Text Analysis":
        text_input = st.text_area("Paste text or claims:", height=150)
        if st.button("Load Evidence"): st.session_state.content_to_check = text_input

    # 2. YOUTUBE
    elif source == "🔗 YouTube Hybrid":
        url = st.text_input("YouTube URL:")
        if st.button("Process Video"):
            video_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
            if "&" in video_id: video_id = video_id.split("&")[0]
            try:
                with st.spinner("Fetching transcript..."):
                    data = YouTubeTranscriptApi.get_transcript(video_id, languages=['el', 'en'])
                    st.session_state.content_to_check = " ".join([i['text'] for i in data])
            except:
                st.warning("No transcript found. Use 'Media File' to upload and transcribe with Whisper.")

    # 3. NEWS SCRAPER
    elif source == "📰 News Scraper":
        url = st.text_input("Article Link:")
        if st.button("Scrape Content"):
            try:
                downloaded = trafilatura.fetch_url(url)
                st.session_state.content_to_check = trafilatura.extract(downloaded)
            except Exception as e: st.error(f"Scraper Error: {e}")

    # 4. VISUAL ANALYSIS (NEW)
    elif source == "🖼️ Visual Analysis":
        img_file = st.file_uploader("Upload Screenshot or Image:", type=["jpg", "jpeg", "png"])
        if img_file:
            st.session_state.image_b64 = encode_image(img_file)
            st.image(img_file, caption="Visual Evidence Preview", width=500)
            st.info("Image loaded. Click 'EXECUTE' below to analyze visual propaganda.")

    # 5. MEDIA FILE (WHISPER)
    else:
        uploaded_file = st.file_uploader("Upload Audio/Video:", type=["mp3", "mp4", "wav", "m4a"])
        if uploaded_file and st.button("Run AI Transcription"):
            try:
                transcription = client.audio.transcriptions.create(
                    file=(uploaded_file.name, uploaded_file.read()),
                    model="distil-whisper-large-v3-it", language="el"
                )
                st.session_state.content_to_check = transcription.text
            except Exception as e: st.error(f"Whisper Error: {e}")

with col2:
    st.info("🔎 **Investigator Mode**: Active")
    if st.button("🗑️ Clear Lab Records"):
        st.session_state.content_to_check = ""
        st.session_state.analysis_report = ""
        st.session_state.image_b64 = None
        st.rerun()

# --- 5. FORENSIC ANALYSIS ENGINE (MULTIMODAL) ---

if st.session_state.content_to_check or st.session_state.image_b64:
    st.divider()
    if st.button("🚀 EXECUTE FORENSIC DETECTION"):
        with st.status("Performing cross-modal analysis...", expanded=True) as status:
            try:
                if source == "🖼️ Visual Analysis" and st.session_state.image_b64:
                    # VISION PROMPT
                    messages = [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this image for propaganda, fake news context, or digital manipulation. Provide the report in Greek, then '|||', then in English."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{st.session_state.image_b64}"}}
                        ]
                    }]
                    model_to_use = "llama-3.2-11b-vision-preview"
                else:
                    # TEXT PROMPT
                    messages = [{
                        "role": "user",
                        "content": f"Analyze this content for misinformation: {st.session_state.content_to_check}. Return Greek, then '|||', then English."
                    }]
                    model_to_use = "llama-3.3-70b-versatile"

                response = client.chat.completions.create(model=model_to_use, messages=messages, temperature=0)
                st.session_state.analysis_report = response.choices[0].message.content
                status.update(label="Analysis Complete!", state="complete")
            except Exception as e: st.error(f"AI Engine Error: {e}")

# --- 6. RENDER THE RESULT WITH LANGUAGE TOGGLE ---
if st.session_state.analysis_report:
    st.subheader("📊 Forensic Investigation Report")
    
    if "|||" in st.session_state.analysis_report:
        parts = st.session_state.analysis_report.split("|||")
        greek_content, english_content = parts[0].strip(), parts[1].strip()
    else:
        greek_content, english_content = st.session_state.analysis_report, "English version not available."

    l_col1, l_col2, _ = st.columns([1, 1, 4])
    if l_col1.button("Ελληνικά 🇬🇷"): 
        st.session_state.selected_lang = "Ελληνικά 🇬🇷"
        st.rerun()
    if l_col2.button("English 🇬🇧"): 
        st.session_state.selected_lang = "English 🇬🇧"
        st.rerun()

    st.markdown(f"### {st.session_state.selected_lang}")
    st.markdown(greek_content if st.session_state.selected_lang == "Ελληνικά 🇬🇷" else english_content)

st.sidebar.divider()
st.sidebar.caption("© 2026 Parasecurity Labs | FORTH & TUC")