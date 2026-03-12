import streamlit as st
import os
import trafilatura
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# --- APP CONFIGURATION ---
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

# --- SESSION STATE (MEMORY) ---
# Persists extracted data across UI interactions
if "content_to_check" not in st.session_state:
    st.session_state.content_to_check = ""
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = ""

# --- API KEY VALIDATION ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY is missing from Streamlit Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- INPUT PANEL ---
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
            st.success("Text data successfully loaded into memory.")

    # 2. HYBRID YOUTUBE (API + WHISPER FALLBACK)
    elif source == "🔗 YouTube Hybrid":
        url = st.text_input("YouTube URL:")
        if st.button("Process Video Evidence"):
            if url:
                video_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
                if "&" in video_id: video_id = video_id.split("&")[0]
                
                # Attempt Fast Transcript Retrieval
                try:
                    with st.spinner("Retrieving official transcripts..."):
                        data = YouTubeTranscriptApi.get_transcript(video_id, languages=['el', 'en'])
                        st.session_state.content_to_check = " ".join([item['text'] for item in data])
                        st.success("Transcript retrieved successfully.")
                # Fallback to Whisper Audio Transcription
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

    # 3. NEWS SCRAPER (WEB ARTICLES)
    elif source == "📰 News Scraper":
        url = st.text_input("Article Link:")
        if st.button("Scrape Web Content"):
            try:
                downloaded = trafilatura.fetch_url(url)
                st.session_state.content_to_check = trafilatura.extract(downloaded)
                st.success("Web content successfully indexed.")
            except Exception as e:
                st.error(f"Scraper Error: {e}")

    # 4. FILE UPLOAD (MP3/MP4)
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
    # THE PERSISTENT CLEAR BUTTON
    if st.button("🗑️ Clear Lab Records"):
        st.session_state.content_to_check = ""
        st.session_state.analysis_report = ""
        st.rerun()

# --- FORENSIC ANALYSIS ENGINE (DUAL LANGUAGE) ---


if st.session_state.content_to_check:
    st.divider()
    # Updated Button Label as requested
    if st.button("🚀 EXECUTE FAKE NEWS DETECTION"):
        with st.status("Analyzing claims and detecting propaganda patterns...", expanded=True) as status:
            try:
                # DUAL-LANGUAGE SKEPTICAL PROMPT
                prompt = f"""
                SYSTEM: You are the Parasecurity Forensic Truth-Seeker. 
                ROLE: Expert in identifying propaganda, logical fallacies, and misinformation.
                
                CONTENT TO ANALYZE:
                {st.session_state.content_to_check}
                
                INSTRUCTIONS:
                1. Critically evaluate all claims. Look for emotional manipulation or lack of sourcing.
                2. Check if the narrative conflicts with official Greek Law or factual records.
                3. PROVIDE THE REPORT IN TWO SECTIONS: GREEK AND THEN ENGLISH.

                STRUCTURE:
                --- ΕΛΛΗΝΙΚΗ ΕΚΘΕΣΗ (GREEK REPORT) ---
                - **ΒΑΣΙΚΟΙ ΙΣΧΥΡΙΣΜΟΙ**:
                - **ΕΤΥΜΗΓΟΡΙΑ**: (Αληθές / Ψευδές / Παραπλανητικό / Ανεπιβεβαίωτο)
                - **ΚΟΚΚΙΝΕΣ ΣΗΜΑΙΕΣ**: (Τεχνικές χειραγώγησης ή προπαγάνδας)
                - **ΒΑΘΜΟΣ ΠΙΣΤΟΤΗΤΑΣ**: (0-100%)

                --- ENGLISH FORENSIC REPORT ---
                - **KEY CLAIMS**:
                - **VERDICT**:
                - **RED FLAGS**:
                - **CREDIBILITY SCORE**:
                """
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0 # Factual precision mode
                )
                
                st.session_state.analysis_report = response.choices[0].message.content
                status.update(label="Detection Complete!", state="complete")
            except Exception as e:
                st.error(f"AI Engine Error: {e}")

# Render the result
if st.session_state.analysis_report:
    st.subheader("📊 Fake News Detection Report (EL/EN)")
    st.markdown(st.session_state.analysis_report)

st.sidebar.divider()
st.sidebar.caption("© 2026 Parasecurity Labs | FORTH & TUC")