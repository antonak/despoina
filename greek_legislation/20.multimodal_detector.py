import streamlit as st
import os
import trafilatura
from groq import Groq
from yt_dlp import YoutubeDL

st.set_page_config(page_title="Parasecurity | Multimodal Fact-Checker", page_icon="🛡️")

st.title("🛡️ Parasecurity: YouTube & Media Fact-Checker")
st.caption("Powered by Groq Whisper & Llama 3.3 @ FORTH & TUC")

if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing API Key")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

source = st.radio("Επιλέξτε πηγή:", ["🔗 YouTube Link", "📰 News Article Link", "📁 Upload File"])
content_to_check = ""

# --- ΛΕΙΤΟΥΡΓΙΑ YOUTUBE ---
if source == "🔗 YouTube Link":
    url = st.text_input("YouTube URL (π.χ. ομιλίες, ειδήσεις):")
    if url:
        if st.button("Ανάλυση Βίντεο"):
            with st.status("Επεξεργασία YouTube Video...", expanded=True) as status:
                try:
                    # Ρυθμίσεις για κατέβασμα μόνο του ήχου (πολύ ελαφρύ)
                    ydl_opts = {
                        'format': 'm4a/bestaudio/best',
                        'outtmpl': 'temp_audio.%(ext)s',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'm4a',
                        }],
                    }
                    
                    st.write("1. Λήψη ήχου από το YouTube...")
                    with YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    
                    st.write("2. Μεταγραφή ομιλίας (Whisper)...")
                    with open("temp_audio.m4a", "rb") as audio_file:
                        transcription = client.audio.transcriptions.create(
                            file=("temp_audio.m4a", audio_file.read()),
                            model="distil-whisper-large-v3-it",
                            response_format="text",
                            language="el"
                        )
                    
                    content_to_check = transcription
                    status.update(label="Η μεταγραφή ολοκληρώθηκε!", state="complete")
                    st.info(f"Τι ειπώθηκε: {content_to_check[:300]}...")
                    
                    # Καθαρισμός αρχείου
                    if os.path.exists("temp_audio.m4a"):
                        os.remove("temp_audio.m4a")
                except Exception as e:
                    st.error(f"Σφάλμα YouTube: {e}")

# --- ΛΕΙΤΟΥΡΓΙΑ NEWS ARTICLES ---
elif source == "📰 News Article Link":
    url = st.text_input("Link εφημερίδας/site:")
    if url:
        downloaded = trafilatura.fetch_url(url)
        content_to_check = trafilatura.extract(downloaded)
        if content_to_check:
            st.success("Το άρθρο ανακτήθηκε!")

# --- ΛΕΙΤΟΥΡΓΙΑ UPLOAD ---
else:
    uploaded_file = st.file_uploader("Ανεβάστε MP3/MP4:", type=["mp3", "mp4", "wav"])
    if uploaded_file:
        with st.spinner("Μεταγραφή..."):
            transcription = client.audio.transcriptions.create(
                file=(uploaded_file.name, uploaded_file.read()),
                model="distil-whisper-large-v3-it",
                response_format="text",
                language="el"
            )
            content_to_check = transcription

# --- ΚΟΙΝΟ FACT CHECKING ---
if content_to_check:
    if st.button("🚀 Έναρξη Fact-Checking"):
        with st.spinner("Διασταύρωση ισχυρισμών..."):
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Είσαι Fact-Checker της Parasecurity. Ανάλυσε το κείμενο για ανακρίβειες βάσει της ελληνικής πραγματικότητας."},
                    {"role": "user", "content": content_to_check}
                ]
            )
            st.subheader("📊 Πόρισμα Ελέγχου")
            st.markdown(res.choices[0].message.content)