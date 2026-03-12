import streamlit as st
import pandas as pd
import os
import re
from groq import Groq

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Parasecurity Legal AI", page_icon="⚖️", layout="wide")

# --- FORENSIC & SANITIZATION FUNCTIONS ---
def detect_suspicious_characters(text):
    """Detects Cyrillic or non-Greek characters hidden in Greek text."""
    cyrillic_pattern = re.compile(r'[а-яА-ЯёЁ]')
    found = cyrillic_pattern.findall(text)
    return list(set(found))

def sanitize_greek_text(text):
    """Automatically swaps suspicious Cyrillic letters with their Greek equivalents."""
    replacements = {
        'а': 'α', 'е': 'ε', 'і': 'ι', 'о': 'ο', 'р': 'ρ', 
        'с': 'σ', 'у': 'υ', 'х': 'χ', 'д': 'δ', 'т': 'τ', 'н': 'ν'
    }
    for cyr, grk in replacements.items():
        text = text.replace(cyr, grk)
    return text

# --- CUSTOM CSS BRANDING ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #d32f2f; color: white; font-weight: bold; }
    .stTextInput>div>div>input { border: 2px solid #d32f2f; }
    .forensic-alert { color: #d32f2f; font-weight: bold; border: 1px solid #d32f2f; padding: 10px; border-radius: 5px; background: #fff1f1; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR & BRANDING ---
with st.sidebar:
    st.title("🛡️ Parasecurity")
    st.subheader("FORTH & TUC Lab")
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# --- 2. API CONNECTION ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY in Secrets.")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 3. DATA LOADING ---
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "praktika_2025_2026/laws_articles.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None

df = load_data()

# --- 4. TABS ---
tab1, tab2 = st.tabs(["💬 Νομικός Σύμβουλος (Chat)", "🔍 Fake News Detector (Audio/Video)"])

# ---------------------------------------------------------
# TAB 1: Chatbot (RAG) with Forensic Sanitization
# ---------------------------------------------------------
with tab1:
    st.header("⚖️ Συζήτηση με τη Νομοθεσία")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # TOP INPUT UI
    with st.container():
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Ρωτήστε για τους νόμους:", placeholder="π.χ. Τι είναι το νόμος 2103/1993;")
            submit_button = st.form_submit_button("Αποστολή 🚀")

    if submit_button and user_input:
        # Step A: Forensic Detection
        suspicious = detect_suspicious_characters(user_input)
        
        # Step B: Auto-Sanitization (Cleaning the text)
        clean_input = sanitize_greek_text(user_input)
        
        # Add to history (keeping the markers for the user to see)
        display_text = user_input
        if suspicious:
            display_text = f"🚩 [SUSPICIOUS CHARS DETECTED: {', '.join(suspicious)}]\n\n{user_input}"
        
        st.session_state.messages.append({"role": "user", "content": display_text})

        # Step C: Optimized RAG Logic
        context = ""
        if df is not None:
            text_cols = [c for c in df.columns if any(w in c.lower() for w in ['text', 'content', 'άρθρο'])]
            target_col = text_cols[0] if text_cols else df.columns[-1]
            keywords = clean_input.split() # Use clean input for searching
            mask = df[target_col].astype(str).str.contains('|'.join(keywords), case=False, na=False)
            context_list = df[mask].head(2)[target_col].astype(str).str[:1500].values
            context = "\n\n".join(context_list)

        # Step D: AI Processing with Clean Data
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"Είσαι ο AI Νομικός Σύμβουλος της Parasecurity. Χρησιμοποίησε το context:\n{context}"},
                    *st.session_state.messages[-3:], 
                ]
            )
            answer = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
        except Exception as e:
            st.error(f"Σφάλμα AI: {e}")

    # MESSAGE DISPLAY (Reverse order)
    st.divider()
    for message in reversed(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ---------------------------------------------------------
# TAB 2: Fake News Detector with Forensic Audio Check
# ---------------------------------------------------------
with tab2:
    st.header("🔍 Ανίχνευση Ψευδών Ειδήσεων")
    media_file = st.file_uploader("Upload Audio/Video", type=["mp3", "mp4", "wav", "m4a"])
    
    if media_file:
        if st.button("🚀 Έναρξη Ανάλυσης"):
            with st.status("Επεξεργασία...", expanded=True) as status:
                try:
                    file_bytes = media_file.read()
                    transcription = client.audio.transcriptions.create(
                        file=(media_file.name, file_bytes),
                        model="distil-whisper-large-v3-it",
                        response_format="text", language="el"
                    )
                    
                    # Forensic Audit of the Transcription
                    susp_chars = detect_suspicious_characters(transcription)
                    st.info(f"Κείμενο: {transcription[:300]}...")
                    
                    if susp_chars:
                        st.markdown(f"<div class='forensic-alert'>🚩 ALERT: Εντοπίστηκαν κυριλλικοί χαρακτήρες ({', '.join(susp_chars)}) στη μεταγραφή. Υψηλή πιθανότητα παραπληροφόρησης (Bot-generated).</div>", unsafe_allow_html=True)

                    # Final Fact-Check
                    check_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": f"Fact-check this: {transcription[:3000]}"}]
                    )
                    
                    status.update(label="Ολοκληρώθηκε!", state="complete")
                    st.success(check_res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Σφάλμα: {e}")