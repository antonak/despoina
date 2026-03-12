import streamlit as st
import os
import trafilatura
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Parasecurity | Hybrid Investigator", page_icon="🛡️", layout="wide")

# --- CUSTOM CSS BRANDING ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #d32f2f; color: white; font-weight: bold; }
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Parasecurity Hybrid Investigator")
st.markdown("### Multimedia Fact-Checking & Audio Forensics")
st.caption("Advanced Lab Tool | FORTH & TUC")

# --- INITIALIZE SESSION MEMORY ---
# Ensures data persists during UI refreshes and button clicks
if "content_to_check" not in st.session_state:
    st.session_state.content_to_check = ""
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = ""

# --- API KEY SECURITY CHECK ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY is missing from Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- DATA SOURCE SELECTION ---
source = st.radio("Select Investigation Source:", 
                  ["🔗 YouTube Hybrid", "📰 News Scraper", "📁 Manual Upload"], 
                  horizontal=True)

col1, col2 = st.columns([3, 1])

with col1:
    # 1. HYBRID YOUTUBE LOGIC (Transcript API + Whisper Fallback)
    if source == "🔗 YouTube Hybrid":
        url = st.text_input("Paste YouTube URL:")
        if st.button("Process Video Evidence"):
            if url:
                video_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
                if "&" in video_id: video_id = video_id.split("&")[0]
                
                # Attempt 1: Fetching existing transcripts
                try:
                    with st.spinner("Step 1: Fetching official transcripts..."):
                        data = YouTubeTranscriptApi.get_transcript(video_id, languages=['el', 'en'])
                        st.session_state.content_to_check = " ".join([item['text'] for item in data])
                        st.success("Transcript retrieved successfully.")
                
                # Attempt 2: Fallback to AI Audio Analysis (Whisper)
                except Exception:
                    st.warning("No subtitles found. Initializing AI Audio Extraction (Whisper)...")
                    try:
                        ydl_opts = {
                            'format': 'm4a/bestaudio/best',
                            'outtmpl': 'temp_yt_audio.%(ext)s',
                            'quiet': True,
                            'no_warnings': True
                        }
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.download([url])
                        
                        with open("temp_yt_audio.m4a", "rb") as audio_file:
                            transcription = client.audio.transcriptions.create(
                                file=("temp_yt_audio.m4a", audio_file.read()),
                                model="distil-whisper-large-v3-it",
                                response_format="text",
                                language="el"
                            )
                        st.session_state.content_to_check = transcription
                        st.success("AI successfully transcribed video audio.")
                        if os.path.exists("temp_yt_audio.m4a"): os.remove("temp_yt_audio.m4a")
                    except Exception as e:
                        st.error(f"Critical System Failure: {e}")

    # 2. WEB CONTENT SCRAPER
    elif source == "📰 News Scraper":
        url = st.text_input("Article Link:")
        if st.button("Scrape Data"):
            try:
                downloaded = trafilatura.fetch_url(url)
                st.session_state.content_to_check = trafilatura.extract(downloaded)
                st.success("Web content successfully indexed.")
            except Exception as e:
                st.error(f"Scraper Error: {e}")

    # 3. LOCAL FILE FORENSICS
    else:
        uploaded_file = st.file_uploader("Upload Evidence (MP3/MP4/WAV):", type=["mp3", "mp4", "wav", "m4a"])
        if uploaded_file and st.button("Run AI Transcription"):
            try:
                with st.spinner("Analyzing audio stream..."):
                    transcription = client.audio.transcriptions.create(
                        file=(uploaded_file.name, uploaded_file.read()),
                        model="distil-whisper-large-v3-it",
                        response_format="text",
                        language="el"
                    )
                    st.session_state.content_to_check = transcription
                    st.success("Forensic transcription complete.")
            except Exception as e:
                st.error(f"Whisper Error: {e}")

with col2:
    st.info("🔎 **Investigator Mode**: Active")
    if st.button("Clear Lab Records"):
        st.session_state.content_to_check = ""
        st.session_state.analysis_report = ""
        st.rerun()

# --- FORENSIC ANALYSIS ENGINE ---


if st.session_state.content_to_check:
    st.divider()
    with st.expander("📝 View Raw Evidence"):
        st.write(st.session_state.content_to_check)

    if st.button("🚀 EXECUTE FACT-CHECKING REPORT"):
        with st.status("Analyzing content for misinformation & bias...", expanded=True) as status:
            try:
                # SKEPTICAL PROMPT: Forces AI to identify manipulation techniques
                prompt = f"""
                ΣΥΣΤΗΜΑ: Είσαι ο Ψηφιακός Ανακριτής της Parasecurity.
                ΡΟΛΟΣ: Forensic Fact-Checker. 
                
                ΠΡΟΣ ΑΝΑΛΥΣΗ:
                {st.session_state.content_to_check}
                
                ΟΔΗΓΙΕΣ:
                1. Εντόπισε ψευδείς ισχυρισμούς και λογικές πλάνες.
                2. Ανίχνευσε τεχνικές προπαγάνδας (clickbait, επίκληση στο συναίσθημα).
                3. Σύγκρινε με την Ελληνική πραγματικότητα και νομοθεσία.
                4. Δώσε 'Red Flags' αν η πηγή δεν είναι αξιόπιστη.

                ΔΟΜΗ ΑΠΑΝΤΗΣΗΣ:
                - **ΒΑΣΙΚΟΙ ΙΣΧΥΡΙΣΜΟΙ**: (Λίστα)
                - **ΑΞΙΟΛΟΓΗΣΗ**: (Αληθές / Ψευδές / Παραπλανητικό / Ανεπιβεβαίωτο)
                - **RED FLAGS**: (Τεχνικές χειραγώγησης)
                - **ΒΑΘΜΟΣ ΠΙΣΤΟΤΗΤΑΣ**: (0-100%)
                
                Απάντησε στα Ελληνικά με επαγγελματικό ύφος.
                """
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0 # Absolute factual precision
                )
                
                st.session_state.analysis_report = response.choices[0].message.content
                status.update(label="Forensic Audit Completed!", state="complete")
            except Exception as e:
                st.error(f"AI Engine Error: {e}")

if st.session_state.analysis_report:
    st.subheader("📊 Forensic Audit Report")
    st.markdown(st.session_state.analysis_report)

st.sidebar.caption("© 2026 Parasecurity Labs | FORTH & TUC")