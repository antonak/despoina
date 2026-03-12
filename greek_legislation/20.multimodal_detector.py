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

# --- API KEY VALIDATION ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

# Initialize Groq Client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- SOURCE SELECTION ---
source = st.radio("Select data source for analysis:", 
                  ["🔗 YouTube Link", "📰 News Article Link", "📁 Upload Media File (MP3/MP4)"], 
                  horizontal=True)

content_to_check = ""

# --- 1. YOUTUBE TRANSCRIPT LOGIC ---
if source == "🔗 YouTube Link":
    url = st.text_input("Paste YouTube URL:")
    if url:
        # Extract Video ID from various URL formats
        if "v=" in url or "youtu.be/" in url:
            video_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
            if "&" in video_id: video_id = video_id.split("&")[0]
            
            if st.button("Extract Video Speech"):
                with st.spinner("Fetching subtitles from YouTube..."):
                    try:
                        # Attempt to fetch Greek first, fallback to English
                        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['el', 'en'])
                        content_to_check = " ".join([t['text'] for t in transcript_list])
                        st.success("Speech successfully retrieved!")
                        with st.expander("View Extracted Text"):
                            st.write(content_to_check)
                    except Exception as e:
                        st.error(f"Could not find subtitles for this video. Note: Video must have captions enabled. Error: {e}")
        else:
            st.warning("Please provide a valid YouTube Link.")

# --- 2. ARTICLE SCRAPING LOGIC ---
elif source == "📰 News Article Link":
    url = st.text_input("Paste article URL:")
    if url:
        if st.button("Extract Article Content"):
            with st.spinner("Scraping content..."):
                try:
                    # Download and extract the main text from the webpage
                    downloaded = trafilatura.fetch_url(url)
                    content_to_check = trafilatura.extract(downloaded)
                    if content_to_check:
                        st.success("Article successfully read!")
                        with st.expander("View Scraped Content"):
                            st.write(content_to_check)
                except Exception as e:
                    st.error(f"Error reading the link: {e}")

# --- 3. FILE UPLOAD LOGIC (WHISPER AI) ---
else:
    uploaded_file = st.file_uploader("Upload audio or video file:", type=["mp3", "mp4", "wav", "m4a"])
    if uploaded_file:
        if st.button("Transcribe with Whisper"):
            with st.spinner("AI is listening to your file..."):
                try:
                    # Send audio data to Groq Whisper for high-accuracy transcription
                    transcription = client.audio.transcriptions.create(
                        file=(uploaded_file.name, uploaded_file.read()),
                        model="distil-whisper-large-v3-it",
                        response_format="text",
                        language="el"
                    )
                    content_to_check = transcription
                    st.success("Transcription complete!")
                    st.text_area("Transcribed Text:", content_to_check, height=200)
                except Exception as e:
                    st.error(f"Whisper Transcription Error: {e}")

# --- FINAL FACT-CHECKING ENGINE ---
if content_to_check:
    st.divider()
    if st.button("🚀 Launch Parasecurity Fact-Check"):
        with st.status("Cross-referencing claims with official data...", expanded=True) as status:
            try:
                # Prompt Engineering: Assigning the LLM a Fact-Checker persona
                prompt = f"""
                You are the Parasecurity Fact-Checker. Analyze the following text retrieved from {source}.
                
                CONTENT:
                {content_to_check}
                
                INSTRUCTIONS:
                1. Identify the 3 most significant factual claims.
                2. Evaluate each as True, False, or Misleading.
                3. Compare them with the spirit of Greek legislation and parliamentary proceedings where applicable.
                4. Provide a final Credibility Score (0-100%).
                
                Respond in GREEK with a professional, academic tone.
                """
                
                # Use Llama 3.3 70B for high-reasoning fact checking
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

st.divider()
st.caption("© 2026 Parasecurity Project | FORTH & Technical University of Crete")