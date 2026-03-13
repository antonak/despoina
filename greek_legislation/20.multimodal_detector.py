import streamlit as st
import os
import re
import trafilatura
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Parasecurity | Fake News Detection", page_icon="🛡️", layout="wide")

# --- CUSTOM CSS BRANDING ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #d32f2f; color: white; font-weight: bold; }
    .stAlert { border-radius: 10px; }
    .report-header { color: #d32f2f; font-weight: bold; font-size: 24px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Parasecurity Hybrid Investigator")
st.markdown("### Multimedia & Text Fake News Detection System")
st.caption("Forensic Intelligence Environment | FORTH & TUC Lab")

# --- 2. SESSION STATE (MEMORY) ---
if "content_to_check" not in st.session_state:
    st.session_state.content_to_check = ""
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = ""
if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "Ελληνικά 🇬🇷"

# --- 3. API KEY VALIDATION ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY is missing from Streamlit Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 4. INPUT PANEL ---
source = st.radio("Select Investigation Source:", 
                  ["📝 Text Analysis", "🔗 YouTube Hybrid", "📰 News Scraper", "📁 Manual Upload"], 
                  horizontal=True)

col1, col2 = st.columns([3, 1])

with col1:
    # 1. TEXT INPUT ANALYSIS
    if source == "📝 Text Analysis":
        text_input = st.text_area("Paste text or claims to verify:", height=200)
        if st.button("Load Text for Analysis"):
            st.session_state.content_to_check = text_input
            st.success("Text data successfully loaded.")

    # 2. HYBRID YOUTUBE
    elif source == "🔗 YouTube Hybrid":
        url = st.text_input("YouTube URL:")
        if st.button("Process Video Evidence"):
            if url:
                video_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
                if "&" in video_id: video_id = video_id.split("&")[0]
                
                try:
                    with st.spinner("Retrieving official transcripts..."):
                        data = YouTubeTranscriptApi.get_transcript(video_id, languages=['el', 'en'])
                        st.session_state.content_to_check = " ".join([item['text'] for item in data])
                        st.success("Transcript retrieved successfully.")
                except Exception:
                    st.warning("Subtitles unavailable. Running AI Audio Extraction (Whisper)...")
                    try:
                        ydl_opts = {'format': 'm4a/bestaudio/best', 'outtmpl': 'temp_yt_audio.%(ext)s', 'quiet': True}
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url])
                        with open("temp_yt_audio.m4a", "rb") as audio_file:
                            transcription = client.audio.transcriptions.create(
                                file=("temp_yt_audio.m4a", audio_file.read()),
                                model="distil-whisper-large-v3-it",
                                response_format="text", language="el"
                            )
                        st.session_state.content_to_check = transcription
                        st.success("AI Forensic Transcription Complete.")
                        if os.path.exists("temp_yt_audio.m4a"): os.remove("temp_yt_audio.m4a")
                    except Exception as e:
                        st.error(f"Critical System Failure: {e}")

    # 3. NEWS SCRAPER
    elif source == "📰 News Scraper":
        url = st.text_input("Article Link:")
        if st.button("Scrape Web Content"):
            try:
                downloaded = trafilatura.fetch_url(url)
                st.session_state.content_to_check = trafilatura.extract(downloaded)
                st.success("Web content successfully indexed.")
            except Exception as e:
                st.error(f"Scraper Error: {e}")

    # 4. FILE UPLOAD
    else:
        uploaded_file = st.file_uploader("Upload Audio/Video:", type=["mp3", "mp4", "wav", "m4a"])
        if uploaded_file and st.button("Run AI Forensic Transcription"):
            try:
                transcription = client.audio.transcriptions.create(
                    file=(uploaded_file.name, uploaded_file.read()),
                    model="distil-whisper-large-v3-it",
                    response_format="text", language="el"
                )
                st.session_state.content_to_check = transcription
                st.success("File successfully transcribed.")
            except Exception as e:
                st.error(f"Whisper Error: {e}")

with col2:
    st.info("🔎 **Investigator Mode**: Active")
    if st.button("🗑️ Clear Lab Records"):
        st.session_state.content_to_check = ""
        st.session_state.analysis_report = ""
        st.rerun()

# --- 5. FORENSIC ANALYSIS ENGINE (DUAL LANGUAGE) ---

if st.session_state.content_to_check:
    st.divider()
    if st.button("🚀 EXECUTE FAKE NEWS DETECTION"):
        with st.status("Analyzing claims and detecting propaganda patterns...", expanded=True) as status:
            try:
                prompt = f"""
                SYSTEM: You are the Parasecurity Forensic Truth-Seeker.
                ROLE: Expert in identifying propaganda and misinformation.
                
                CONTENT TO ANALYZE:
                {st.session_state.content_to_check}
                
                INSTRUCTIONS:
                1. Critically evaluate claims.
                2. Provide the report in GREEK, then the exact symbol '|||', then the report in ENGLISH.

                STRUCTURE FOR BOTH LANGUAGES:
                - **ΒΑΣΙΚΟΙ ΙΣΧΥΡΙΣΜΟΙ / KEY CLAIMS**:
                - **ΕΤΥΜΗΓΟΡΙΑ / VERDICT**:
                - **ΚΟΚΚΙΝΕΣ ΣΗΜΑΙΕΣ / RED FLAGS**:
                - **ΒΑΘΜΟΣ ΠΙΣΤΟΤΗΤΑΣ / CREDIBILITY SCORE**:
                """
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0 
                )
                
                st.session_state.analysis_report = response.choices[0].message.content
                status.update(label="Detection Complete!", state="complete")
            except Exception as e:
                st.error(f"AI Engine Error: {e}")

# --- 6. RENDER THE RESULT WITH LANGUAGE TOGGLE ---
if st.session_state.analysis_report:
    st.subheader("📊 Fake News Detection Report")
    
    # Split content logic
    if "|||" in st.session_state.analysis_report:
        parts = st.session_state.analysis_report.split("|||")
        greek_content = parts[0].strip()
        english_content = parts[1].strip()
    else:
        greek_content = st.session_state.analysis_report
        english_content = "English version was not partitioned correctly by AI."

    # Language Switcher Buttons
    l_col1, l_col2, _ = st.columns([1, 1, 4])
    with l_col1:
        if st.button("Ελληνικά 🇬🇷"):
            st.session_state.selected_lang = "Ελληνικά 🇬🇷"
            st.rerun()
    with l_col2:
        if st.button("English 🇬🇧"):
            st.session_state.selected_lang = "English 🇬🇧"
            st.rerun()

    # Display selected language
    st.markdown(f"### {st.session_state.selected_lang}")
    if st.session_state.selected_lang == "Ελληνικά 🇬🇷":
        st.markdown(greek_content)
    else:
        st.markdown(english_content)

st.sidebar.divider()
st.sidebar.caption("© 2026 Parasecurity Labs | FORTH & TUC")