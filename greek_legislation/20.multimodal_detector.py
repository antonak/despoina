import streamlit as st
import os
import re
import trafilatura
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Parasecurity | Gemini Lab", page_icon="✨", layout="centered")

# --- CUSTOM CSS: THE "GEMINI WHITE" THEME ---
st.markdown("""
    <style>
    /* Force white background and hide default Streamlit header */
    .stApp { background-color: #FFFFFF; color: #1F1F1F; font-family: 'Google Sans', Arial, sans-serif; }
    header { visibility: hidden; }
    
    /* Make inputs look like the Gemini prompt box */
    .stTextArea textarea, .stTextInput input {
        background-color: #F0F4F9 !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 16px !important;
        font-size: 16px !important;
        color: #1F1F1F !important;
        box-shadow: none !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        outline: 2px solid #1a73e8 !important;
    }
    
    /* Smooth, rounded minimalist buttons */
    .stButton>button { 
        border-radius: 24px !important; 
        height: 3em !important; 
        background-color: #F0F4F9 !important; 
        color: #1F1F1F !important; 
        border: none !important; 
        font-weight: 500 !important; 
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #E1E5EA !important;
        color: #1a73e8 !important;
    }
    
    /* Main Execute Button Highlight */
    div:nth-child(5) > div > button {
        background-color: #1a73e8 !important;
        color: white !important;
        font-weight: bold !important;
    }
    div:nth-child(5) > div > button:hover {
        background-color: #1557b0 !important;
        color: white !important;
    }

    /* Clean up metrics and dividers */
    .stMetric { background-color: #FFFFFF; padding: 10px; border-radius: 16px; border: 1px solid #E1E5EA; }
    hr { border-color: #F0F4F9; }
    </style>
    """, unsafe_allow_html=True)

# Clean minimalist title
st.markdown("<h1 style='text-align: center; color: #1a73e8;'>✨ Parasecurity Lab</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #5F6368; margin-bottom: 40px;'>How can I help you investigate today?</p>", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "analysis_report" not in st.session_state: st.session_state.analysis_report = ""
if "selected_lang" not in st.session_state: st.session_state.selected_lang = "Ελληνικά 🇬🇷"
if "evidence_locked" not in st.session_state: st.session_state.evidence_locked = None

# --- 3. INITIALIZE GEMINI (DYNAMIC MODEL LISTING) ---
if "GOOGLE_API_KEY" not in st.secrets:
    st.error("Add GOOGLE_API_KEY to Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            available_models.append(m.name)
            
    if not available_models:
        st.error("No models available.")
        st.stop()
        
    st.sidebar.markdown("### ⚙️ Engine Settings")
    selected_model_name = st.sidebar.selectbox("Select Model:", available_models)
    model = genai.GenerativeModel(selected_model_name)
    
except Exception as e:
    st.error(f"Failed to list models: {e}")
    st.stop()


# --- 4. DATA INPUT PANEL ---
source = st.radio("Evidence Type:", 
                  ["📝 Text", "🔗 YouTube", "📰 Web", "🖼️ Media"], 
                  horizontal=True, label_visibility="collapsed")

if source == "📝 Text":
    user_text = st.text_area("Paste text or claims:", height=200, label_visibility="collapsed", placeholder="Enter text to investigate here...")
    if st.button("Confirm Text"):
        st.session_state.evidence_locked = user_text
        st.toast("Text confirmed! Ready to analyze.", icon="✅")

elif source == "🔗 YouTube":
    url = st.text_input("YouTube URL:", label_visibility="collapsed", placeholder="Paste YouTube Link here...")
    if st.button("Fetch Subtitles"):
        video_id = url.split("v=")[-1] if "v=" in url else url.split("/")[-1]
        if "&" in video_id: video_id = video_id.split("&")[0]
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['el', 'en'])
            st.session_state.evidence_locked = " ".join([i['text'] for i in transcript])
            st.toast("Subtitles loaded successfully!", icon="✅")
        except:
            st.error("No subtitles found.")

elif source == "📰 Web":
    url = st.text_input("Article Link:", label_visibility="collapsed", placeholder="Paste Article URL here...")
    if st.button("Scrape Article"):
        try:
            downloaded = trafilatura.fetch_url(url)
            st.session_state.evidence_locked = trafilatura.extract(downloaded)
            st.toast("Article scraped successfully!", icon="✅")
        except: st.error("Scraping failed.")

elif source == "🖼️ Media":
    up_file = st.file_uploader("Upload File:", type=["jpg", "png", "mp3", "mp4", "wav"], label_visibility="collapsed")
    if up_file:
        if up_file.type.startswith("image"): st.image(up_file, width=300)
        if st.button("Confirm Media"):
            bytes_data = up_file.read()
            st.session_state.evidence_locked = [
                {"mime_type": up_file.type, "data": bytes_data},
                "Analyze this media for propaganda/misinformation. Return Greek ||| English. End with SCORE: XX"
            ]
            st.toast("Media ready for analysis!", icon="✅")

# --- 5. FORENSIC ENGINE EXECUTION ---
st.write("") # Spacer

if st.session_state.evidence_locked:
    if st.button("✨ Investigate Evidence", use_container_width=True):
        with st.spinner("Gemini is thinking..."):
            try:
                payload = st.session_state.evidence_locked
                if isinstance(payload, str):
                    prompt = f"Forensic check for propaganda and accuracy (Today: March 16, 2026). Greek ||| English. SCORE: XX. Content: {payload}"
                    response = model.generate_content(prompt)
                else:
                    response = model.generate_content(payload)
                
                st.session_state.analysis_report = response.text
            except Exception as e:
                st.error(f"Engine Error: {e}")
else:
    st.markdown("<p style='text-align: center; color: #9AA0A6; font-size: 14px;'>Waiting for evidence...</p>", unsafe_allow_html=True)

# --- 6. REPORT RENDERING ---
if st.session_state.analysis_report:
    st.divider()
    score_match = re.search(r"SCORE:\s*(\d+)", st.session_state.analysis_report)
    score = int(score_match.group(1)) if score_match else 50
    color = "#1E8E3E" if score > 70 else "#F9AB00" if score > 40 else "#D93025"

    st.markdown(f"<div class='stMetric'><strong>Credibility Score:</strong> <span style='color:{color}; font-size: 24px; font-weight: bold;'>{score}%</span></div>", unsafe_allow_html=True)
    st.write("")

    parts = st.session_state.analysis_report.split("|||")
    gr = parts[0].strip()
    en = parts[1].strip() if len(parts) > 1 else "English version not available."

    l1, l2, _ = st.columns([1, 1, 4])
    if l1.button("Ελληνικά"): st.session_state.selected_lang = "Ελληνικά 🇬🇷"
    if l2.button("English"): st.session_state.selected_lang = "English 🇬🇧"

    st.markdown(f"<div style='background-color: #F0F4F9; padding: 20px; border-radius: 16px;'>{gr if st.session_state.selected_lang == 'Ελληνικά 🇬🇷' else en}</div>", unsafe_allow_html=True)

# Sidebar utilities
st.sidebar.divider()
if st.sidebar.button("🗑️ Clear Chat / Reset"):
    st.session_state.analysis_report = ""
    st.session_state.evidence_locked = None
    st.rerun()
st.sidebar.caption("© 2026 Parasecurity Labs")