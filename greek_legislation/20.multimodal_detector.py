import streamlit as st
import os
import trafilatura
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Parasecurity | Fact-Checker", page_icon="🛡️", layout="wide")

st.title("🛡️ Parasecurity: Truth Seeker")
st.markdown("### Credibility Analysis: YouTube, Articles & Media")
st.caption("Autonomous Misinformation Detection Tool | FORTH & TUC Lab")

# --- INITIALIZE SESSION STATE (MEMORY) ---
# This prevents data loss when buttons are clicked
if "content_to_check" not in st.session_state:
    st.session_state.content_to_check = ""

# --- API KEY VALIDATION ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SOURCE SELECTION ---
source = st.radio("Select data source for analysis:", 
                  ["🔗 YouTube Link", "📰 News Article Link", "📁 Upload Media File"], 
                  horizontal=True)

# --- 1. YOUTUBE TRANSCRIPT LOGIC ---
if source == "🔗 YouTube Link":
    url = st.text_input("Paste YouTube URL:")
    if url:
        if "v=" in url or "youtu.be/" in url:
            video_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
            if "&" in video_id: video_id = video_id.split("&")[0]
            
            if st.button("Extract Video Speech"):
                with st.spinner("Fetching subtitles from YouTube..."):
                    try:
                        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['el', 'en'])
                        st.session_state.content_to_check = " ".join([t['text'] for t in transcript_list])
                        st.success("Speech successfully retrieved!")
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.warning("Please provide a valid YouTube Link.")

# --- 2. ARTICLE SCRAPING LOGIC ---
elif source == "📰 News Article Link":
    url = st.text_input("Paste article URL:")
    if url:
        if st.button("Extract Article Content"):
            with st.spinner("Scraping content..."):
                try:
                    downloaded = trafilatura.fetch_url(url)
                    extracted_text = trafilatura.extract(downloaded)
                    if extracted_text:
                        st.session_state.content_to_check = extracted_text
                        st.success("Article successfully read!")
                    else:
                        st.error("Could not extract text from this link.")
                except Exception as e:
                    st.error(f"Scraping Error: {e}")

# --- 3. FILE UPLOAD LOGIC (WHISPER AI) ---
else:
    uploaded_file = st.file_uploader("Upload audio or video file:", type=["mp3", "mp4", "wav", "m4a"])
    if uploaded_file:
        if st.button("Transcribe with Whisper"):
            with st.spinner("AI is listening..."):
                try:
                    transcription = client.audio.transcriptions.create(
                        file=(uploaded_file.name, uploaded_file.read()),
                        model="distil-whisper-large-v3-it",
                        response_format="text",
                        language="el"
                    )
                    st.session_state.content_to_check = transcription
                    st.success("Transcription complete!")
                except Exception as e:
                    st.error(f"Whisper Error: {e}")

# --- PREVIEW & ANALYSIS SECTION ---
# This part only shows up if there is text in the memory
if st.session_state.content_to_check:
    st.divider()
    with st.expander("🔍 Preview Extracted Content", expanded=False):
        st.write(st.session_state.content_to_check)

    if st.button("🚀 Launch Parasecurity Fact-Check"):
        with st.status("Analyzing claims with Llama 3.3...", expanded=True) as status:
            try:
                prompt = f"""
                You are the Parasecurity Fact-Checker. Analyze the following text retrieved from {source}.
                
                CONTENT:
                {st.session_state.content_to_check}
                
                INSTRUCTIONS:
                1. Identify the 3 most significant factual claims.
                2. Evaluate each as True, False, or Misleading based on Greek law and general facts.
                3. Provide a final Credibility Score (0-100%).
                
                Respond in GREEK with a professional, academic tone.
                """
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                
                status.update(label="Analysis Complete!", state="complete")
                st.subheader("📊 Fact-Checking Report")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"AI Analysis Error: {e}")

# --- CLEANUP OPTION ---
if st.session_state.content_to_check:
    if st.sidebar.button("Clear Data Memory"):
        st.session_state.content_to_check = ""
        st.rerun()

st.sidebar.divider()
st.sidebar.caption("© 2026 Parasecurity Project | FORTH & TUC")