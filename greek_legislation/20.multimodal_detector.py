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
        background-color: #F0F4F9 !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 16px !important;
        color: #1F1F1F !important;
    }
    .stButton>button { border-radius: 24px !important; background-color: #F0F4F9 !important; color: #1F1F1F !important; border: none !important; }
    div.stButton > button:first-child[kind="primary"] { background-color: #1a73e8 !important; color: white !important; }
    .stMetric { background-color: #FFFFFF; padding: 10px; border-radius: 16px; border: 1px solid #E1E5EA; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1a73e8;'>✨ Parasecurity Lab</h1>", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "analysis_report" not in st.session_state: st.session_state.analysis_report = ""
if "selected_lang" not in st.session_state: st.session_state.selected_lang = "Ελληνικά 🇬🇷"
if "evidence_locked" not in st.session_state: st.session_state.evidence_locked = None

# --- 3. INITIALIZE GROQ ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Add GROQ_API_KEY to secrets.")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.sidebar.markdown("### ⚙️ Engine")
groq_models = {
    "Llama 3.3 70B": "llama-3.3-70b-versatile",
    "Llama 3.1 405B": "llama-3.1-405b-reasoning"
}
selected_model_id = groq_models[st.sidebar.selectbox("Model:", list(groq_models.keys()))]

# --- 4. DATA INPUT ---
source = st.radio("Source:", ["📝 Text", "🔗 YouTube", "📰 Web", "🖼️ Image"], horizontal=True, label_visibility="collapsed")

if source == "📝 Text":
    user_text = st.text_area("Paste text:", height=150, label_visibility="collapsed")
    if st.button("Confirm Text"):
        st.session_state.evidence_locked = user_text
        st.toast("Locked!", icon="✅")

elif source == "🔗 YouTube":
    url = st.text_input("YouTube URL:", placeholder="Paste link...")
    if st.button("Extract"):
        video_id = url.split("v=")[-1].split("&")[0] if "v=" in url else url.split("/")[-1]
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['el', 'en'])
            st.session_state.evidence_locked = " ".join([i['text'] for i in transcript])
            st.success("Transcript loaded!")
        except:
            st.error("Could not extract subtitles.")

elif source == "📰 Web":
    url = st.text_input("Article Link:")
    if st.button("Scrape"):
        downloaded = trafilatura.fetch_url(url)
        st.session_state.evidence_locked = trafilatura.extract(downloaded)
        st.success("Article scraped!")

elif source == "🖼️ Image":
    up_file = st.file_uploader("Upload Image:", type=["jpg", "png"])
    if up_file:
        st.image(up_file, width=300)
        if st.button("Confirm Image"):
            st.session_state.evidence_locked = [{"mime_type": up_file.type, "data": up_file.read()}]

# --- 5. FORENSIC ENGINE ---
if st.session_state.evidence_locked:
    if st.button("✨ Start Investigation", type="primary", use_container_width=True):
        with st.spinner("Analyzing..."):
            try:
                # ΝΕΟ ΠΑΝΙΣΧΥΡΟ PROMPT ΜΕ TAGS
                sys_prompt = """You are a Forensic Investigator. 
                STRICT OUTPUT FORMAT:
                <GREEK> [Full analysis in Greek here] </GREEK>
                <ENGLISH> [Full analysis in English here] </ENGLISH>
                SCORE: [0-100]
                
                MANDATORY: Do not use any other labels or headers. Everything must be inside the tags."""
                
                if isinstance(st.session_state.evidence_locked, str):
                    response = client.chat.completions.create(
                        messages=[{"role": "system", "content": sys_prompt},
                                  {"role": "user", "content": st.session_state.evidence_locked}],
                        model=selected_model_id, temperature=0.1
                    )
                else:
                    b64_img = base64.b64encode(st.session_state.evidence_locked[0]["data"]).decode('utf-8')
                    response = client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[{"role": "system", "content": sys_prompt},
                                  {"role": "user", "content": [
                                      {"type": "text", "text": "Analyze for propaganda."},
                                      {"type": "image_url", "image_url": {"url": f"data:{st.session_state.evidence_locked[0]['mime_type']};base64,{b64_img}"}}
                                  ]}]
                    )
                st.session_state.analysis_report = response.choices[0].message.content
            except Exception as e:
                st.error(f"Error: {e}")

# --- 6. REPORT RENDERING (PARSING) ---
if st.session_state.analysis_report:
    st.divider()
    report = st.session_state.analysis_report

    # Εξαγωγή Score
    score_match = re.search(r"SCORE:\s*(\d+)", report)
    score = int(score_match.group(1)) if score_match else 50
    color = "#1E8E3E" if score > 70 else "#F9AB00" if score > 40 else "#D93025"
    st.markdown(f"<div class='stMetric'><strong>Credibility:</strong> <span style='color:{color}; font-size: 24px;'>{score}%</span></div>", unsafe_allow_html=True)

    # ΕΞΥΠΝΟ PARSING ΜΕ REGEX ΓΙΑ ΤΑ TAGS
    gr_match = re.search(r'<GREEK>(.*?)</GREEK>', report, re.DOTALL | re.IGNORECASE)
    en_match = re.search(r'<ENGLISH>(.*?)</ENGLISH>', report, re.DOTALL | re.IGNORECASE)

    gr_text = gr_match.group(1).strip() if gr_match else "Η ελληνική ανάλυση δεν βρέθηκε."
    en_text = en_match.group(1).strip() if en_match else "English analysis not found."

    # Tabs
    l1, l2, _ = st.columns([1, 1, 4])
    if l1.button("Ελληνικά"): st.session_state.selected_lang = "Ελληνικά 🇬🇷"
    if l2.button("English"): st.session_state.selected_lang = "English 🇬🇧"

    st.markdown(f"<div style='background-color: #F0F4F9; padding: 25px; border-radius: 20px;'>{gr_text if st.session_state.selected_lang == 'Ελληνικά 🇬🇷' else en_text}</div>", unsafe_allow_html=True)

st.sidebar.divider()
if st.sidebar.button("🗑️ Reset"):
    st.session_state.analysis_report = ""
    st.session_state.evidence_locked = None
    st.rerun()