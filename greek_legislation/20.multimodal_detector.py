import streamlit as st
import os
import trafilatura
from groq import Groq
# Explicit import to avoid attribute errors
from youtube_transcript_api import YouTubeTranscriptApi 

# --- APP CONFIGURATION ---
# Set the page title and professional layout
st.set_page_config(page_title="Parasecurity | Forensic Investigator", page_icon="🛡️", layout="wide")

# --- CUSTOM INTERFACE STYLING ---
# Professional Parasecurity branding with red/dark theme
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #d32f2f; color: white; font-weight: bold; }
    .stExpander { border: 1px solid #444; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Parasecurity Investigator")
st.markdown("### Forensic Intelligence: Multimedia Fact-Checking & Bias Analysis")
st.caption("Lab Environment | FORTH & Technical University of Crete (TUC)")

# --- SESSION STATE INITIALIZATION ---
# Session state handles 'Memory'. It ensures extracted data isn't lost during UI refreshes.
if "content_to_check" not in st.session_state:
    st.session_state.content_to_check = ""
if "analysis_report" not in st.session_state:
    st.session_state.analysis_report = ""

# --- SECURITY & API CHECK ---
# Verify Groq API Key existence in Streamlit Secrets
if "GROQ_API_KEY" not in st.secrets:
    st.error("GROQ_API_KEY is missing from Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- INPUT MODULES ---
# Navigation for data sources
source = st.radio("Select Evidence Source:", 
                  ["🔗 YouTube Video", "📰 News Link", "📁 Local Media"], 
                  horizontal=True)

col1, col2 = st.columns([3, 1])

with col1:
    # 1. YOUTUBE TRANSCRIPTION (Fixed Logic)
    if source == "🔗 YouTube Video":
        url = st.text_input("YouTube URL (e.g., Political Speech, Interview):")
        if st.button("Extract Transcript"):
            if url:
                try:
                    # Parse the Video ID from the URL string
                    video_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
                    if "&" in video_id: video_id = video_id.split("&")[0]
                    
                    # Correct method call to YouTubeTranscriptApi class
                    data = YouTubeTranscriptApi.get_transcript(video_id, languages=['el', 'en'])
                    
                    # Join transcript fragments into a single text block
                    st.session_state.content_to_check = " ".join([item['text'] for item in data])
                    st.success("Transcript successfully retrieved.")
                except Exception as e:
                    st.error(f"YouTube Transcript Error: {e}")

    # 2. NEWS ARTICLE SCRAPING
    elif source == "📰 News Link":
        url = st.text_input("News Article URL:")
        if st.button("Scrape Web Content"):
            if url:
                try:
                    # Fetch and clean the article text
                    downloaded = trafilatura.fetch_url(url)
                    st.session_state.content_to_check = trafilatura.extract(downloaded)
                    if st.session_state.content_to_check:
                        st.success("Article content successfully parsed.")
                except Exception as e:
                    st.error(f"Scraping error: {e}")

    # 3. AUDIO/VIDEO FILE TRANSCRIPTION
    else:
        uploaded_file = st.file_uploader("Upload Audio/Video:", type=["mp3", "mp4", "wav", "m4a"])
        if uploaded_file and st.button("Transcribe via Groq Whisper"):
            try:
                with st.spinner("Whisper AI is processing the stream..."):
                    transcription = client.audio.transcriptions.create(
                        file=(uploaded_file.name, uploaded_file.read()),
                        model="distil-whisper-large-v3-it",
                        response_format="text",
                        language="el"
                    )
                    st.session_state.content_to_check = transcription
                    st.success("Transcription complete.")
            except Exception as e:
                st.error(f"Whisper Error: {e}")

with col2:
    st.info("💡 **Security Tip**: Clear the memory between different investigations to ensure clean results.")
    if st.button("Reset Lab Memory"):
        st.session_state.content_to_check = ""
        st.session_state.analysis_report = ""
        st.rerun()

# --- FORENSIC ANALYSIS ENGINE ---
# This part triggers only if content exists in the memory
if st.session_state.content_to_check:
    st.divider()
    with st.expander("📋 View Extracted Evidence (Raw Text)"):
        st.write(st.session_state.content_to_check)

    if st.button("🚀 EXECUTE FORENSIC ANALYSIS"):
        with st.status("Detecting propaganda and analyzing claims...", expanded=True) as status:
            try:
                # SKEPTICAL INVESTIGATOR PROMPT
                # Forces the model to look for fallacies, bias, and legal contradictions
                prompt = f"""
                ΣΥΣΤΗΜΑ: Είσαι ο Ψηφιακός Ανακριτής της Parasecurity.
                ΡΟΛΟΣ: Ειδικός στη γλωσσολογική ανάλυση και την ανίχνευση παραπληροφόρησης.
                
                ΠΡΟΣ ΑΝΑΛΥΣΗ:
                {st.session_state.content_to_check}
                
                ΟΔΗΓΙΕΣ:
                1. Μην αποδέχεσαι το κείμενο ως αληθές. Αναζήτησε αντιφάσεις και 'Red Flags'.
                2. Εντόπισε τεχνικές χειραγώγησης (π.χ. επίκληση στο συναίσθημα, επιλεκτική χρήση στοιχείων).
                3. Έλεγξε αν οι ισχυρισμοί είναι νομικά βάσιμοι βάσει της Ελληνικής Νομοθεσίας.
                4. Αξιολόγησε την αντικειμενικότητα της πηγής.

                ΔΟΜΗ ΑΠΑΝΤΗΣΗΣ:
                - **ΒΑΣΙΚΟΙ ΙΣΧΥΡΙΣΜΟΙ**: (Λίστα με τους κύριους ισχυρισμούς)
                - **ΑΞΙΟΛΟΓΗΣΗ ΕΓΚΥΡΟΤΗΤΑΣ**: (Αληθές / Ψευδές / Παραπλανητικό / Ανεπιβεβαίωτο)
                - **ΣΗΜΑΤΑ ΚΙΝΔΥΝΟΥ (Red Flags)**: (Εντοπισμός τεχνικών προπαγάνδας)
                - **ΒΑΘΜΟΣ ΠΙΣΤΟΤΗΤΑΣ**: (0-100%)
                
                Απάντησε στα Ελληνικά με αυστηρά επαγγελματικό ύφος.
                """
                
                # Temperature 0 for maximum factual accuracy
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0 
                )
                
                st.session_state.analysis_report = response.choices[0].message.content
                status.update(label="Forensic Analysis Finished!", state="complete")
            except Exception as e:
                st.error(f"AI Engine Error: {e}")

# Render the final report
if st.session_state.analysis_report:
    st.subheader("📊 Forensic Investigative Report")
    st.markdown(st.session_state.analysis_report)

st.sidebar.divider()
st.sidebar.caption("Parasecurity Labs 2026 | FORTH & TUC")