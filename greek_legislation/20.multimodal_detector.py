import streamlit as st
import pandas as pd
import os
import trafilatura
from groq import Groq

# Ρυθμίσεις Σελίδας
st.set_page_config(page_title="Parasecurity | Lab Mode", page_icon="🧪")

st.title("🧪 Parasecurity Lab: Multimodal Fact-Checking")
st.info("Αυτή η σελίδα είναι σε δοκιμαστική φάση (Beta).")

# Σύνδεση με Groq
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing API Key")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Επιλογή Πηγής
source = st.selectbox("Επιλέξτε πηγή ανάλυσης:", ["Link Ιστοσελίδας", "Αρχείο Ήχου/Βίντεο"])

content_to_check = ""

if source == "Link Ιστοσελίδας":
    url = st.text_input("URL Άρθρου:")
    if url:
        try:
            downloaded = trafilatura.fetch_url(url)
            content_to_check = trafilatura.extract(downloaded)
            if content_to_check:
                st.success("Το κείμενο ανακτήθηκε!")
                st.text_area("Προεπισκόπηση:", content_to_check[:500], height=150)
        except Exception as e:
            st.error(f"Σφάλμα Scraping: {e}")

else:
    media_file = st.file_uploader("Upload Media:", type=["mp3", "mp4", "wav"])
    if media_file:
        try:
            with st.spinner("Μεταγραφή με Whisper..."):
                transcription = client.audio.transcriptions.create(
                    file=(media_file.name, media_file.read()),
                    model="distil-whisper-large-v3-it",
                    response_format="text",
                    language="el"
                )
                content_to_check = transcription
                st.success("Η μεταγραφή ολοκληρώθηκε.")
        except Exception as e:
            st.error(f"Σφάλμα Whisper: {e}")

# Fact Checking Logic
if content_to_check and st.button("🚀 Έλεγχος Εγκυρότητας"):
    with st.spinner("Ανάλυση από το Llama 3.3..."):
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Είσαι Fact-Checker της Parasecurity. Ανάλυσε το κείμενο για ψευδείς ειδήσεις."},
                {"role": "user", "content": content_to_check}
            ]
        )
        st.subheader("📊 Πόρισμα")
        st.markdown(res.choices[0].message.content)

st.divider()
st.caption("Parasecurity @ FORTH & TUC - Lab Environment")