import streamlit as st
import pandas as pd
import os
import re
from groq import Groq

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Parasecurity Legal AI", page_icon="⚖️", layout="wide")

# --- FUNCTIONS ---
def detect_suspicious_characters(text):
    cyrillic_pattern = re.compile(r'[а-яА-ЯёЁ]')
    found = cyrillic_pattern.findall(text)
    return list(set(found))

def sanitize_greek_text(text):
    replacements = {
        'а': 'α', 'е': 'ε', 'і': 'ι', 'ο': 'ο', 'р': 'ρ', 
        'с': 'σ', 'у': 'υ', 'х': 'χ', 'д': 'δ', 'т': 'τ', 'н': 'ν'
    }
    for cyr, grk in replacements.items():
        text = text.replace(cyr, grk)
    return text

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Parasecurity")
    st.subheader("FORTH & TUC Lab")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 2. API & DATA ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY in Secrets.")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "praktika_2025_2026/laws_articles.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None

df = load_data()

# --- 3. TABS ---
tab1, tab2 = st.tabs(["💬 Νομικός Σύμβουλος (Chat)", "🔍 Fake News Detector"])

# ---------------------------------------------------------
# TAB 1: Chatbot (Fixed Flow)
# ---------------------------------------------------------
with tab1:
    st.header("⚖️ Συζήτηση με τη Νομοθεσία")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # TOP INPUT
    with st.container():
        # Αφαιρέσαμε το st.form για πιο άμεση ανταπόκριση χωρίς σφάλματα ανανέωσης
        user_input = st.text_input("Ρωτήστε για τους νόμους:", key="user_query", on_change=None)
        send_btn = st.button("Αποστολή 🚀")

    if send_btn and user_input:
        # 1. Forensic Check & Sanitize
        suspicious = detect_suspicious_characters(user_input)
        clean_input = sanitize_greek_text(user_input)
        
        display_text = user_input
        if suspicious:
            display_text = f"🚩 [SUSPICIOUS CHARS: {', '.join(suspicious)}]\n\n{user_input}"
        
        # Save user message
        st.session_state.messages.append({"role": "user", "content": display_text})

        # 2. RAG Logic
        context = ""
        if df is not None:
            text_cols = [c for c in df.columns if any(w in c.lower() for w in ['text', 'content', 'άρθρο'])]
            target_col = text_cols[0] if text_cols else df.columns[-1]
            keywords = clean_input.split()
            mask = df[target_col].astype(str).str.contains('|'.join(keywords), case=False, na=False)
            context = "\n\n".join(df[mask].head(2)[target_col].astype(str).str[:1500].values)

        # 3. AI Response
        try:
            with st.spinner("Η Δέσποινα αναλύει το ερώτημα..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"Είσαι ο AI Νομικός Σύμβουλος της Parasecurity. Απάντησε τεκμηριωμένα:\n{context}"},
                        *st.session_state.messages[-3:], 
                    ]
                )
                answer = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"Σφάλμα AI: {e}")

    # 4. DISPLAY MESSAGES
    st.divider()
    for message in reversed(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ---------------------------------------------------------
# TAB 2: Fake News Detector
# ---------------------------------------------------------
with tab2:
    st.header("🔍 Ανίχνευση Ψευδών Ειδήσεων")
    media_file = st.file_uploader("Upload Audio/Video", type=["mp3", "mp4", "wav", "m4a"])
    
    if media_file:
        if st.button("🚀 Έναρξη Ανάλυσης"):
            with st.status("Επεξεργασία...", expanded=True):
                file_bytes = media_file.read()
                transcription = client.audio.transcriptions.create(
                    file=(media_file.name, file_bytes),
                    model="distil-whisper-large-v3-it",
                    response_format="text", language="el"
                )
                
                check_res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": f"Fact-check this: {transcription[:3000]}"}]
                )
                st.success(check_res.choices[0].message.content)