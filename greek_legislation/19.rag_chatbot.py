import streamlit as st
import pandas as pd
import os
import re
from groq import Groq

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Parasecurity Legal AI", page_icon="⚖️", layout="wide")

# --- FORENSIC & CLEANING FUNCTIONS ---
def detect_suspicious_characters(text):
    """Detects Cyrillic characters to protect against obfuscated/fake text."""
    cyrillic_pattern = re.compile(r'[а-яА-ЯёЁ]')
    found = cyrillic_pattern.findall(text)
    return list(set(found))

def sanitize_greek_text(text):
    """Auto-corrects visually similar characters from Cyrillic to Greek."""
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

# --- 2. API & DATA LOADING ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY in Secrets.")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

@st.cache_data
def load_data():
    """Loads the legal dataset from the local CSV file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "praktika_2025_2026/laws_articles.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None

df = load_data()

# --- 3. UI TABS ---
tab1, tab2 = st.tabs(["💬 Νομικός Σύμβουλος (Chat)", "🔍 Fake News Detector"])

# ---------------------------------------------------------
# TAB 1: Chatbot (Legal Consultant)
# ---------------------------------------------------------
with tab1:
    st.header("⚖️ Συζήτηση με τη Νομοθεσία")
    
    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # INPUT SECTION: Using a form to enable 'Enter' key submission and auto-clear
    with st.container():
        with st.form(key="chat_form", clear_on_submit=True):
            user_input = st.text_input("Ρωτήστε για τους νόμους:", key="input_field")
            submit_button = st.form_submit_button("Αποστολή 🚀")

    if submit_button and user_input:
        # Step A: Forensic Check & Text Normalization
        suspicious = detect_suspicious_characters(user_input)
        clean_input = sanitize_greek_text(user_input)
        
        # Prepare text for display (add warning flag if suspicious chars found)
        display_text = user_input
        if suspicious:
            display_text = f"🚩 [Εντοπίστηκαν ύποπτοι χαρακτήρες: {', '.join(suspicious)}]\n\n{user_input}"
        
        # Append user message to history
        st.session_state.messages.append({"role": "user", "content": display_text})

        # Step B: RAG Logic (Retrieval Augmented Generation)
        context = ""
        if df is not None:
            # Identify the column containing the legal text
            text_cols = [c for c in df.columns if any(w in c.lower() for w in ['text', 'content', 'άρθρο'])]
            target_col = text_cols[0] if text_cols else df.columns[-1]
            
            # Escape keywords to prevent Regex PatternErrors (e.g., from '?' or '*')
            keywords = [re.escape(word) for word in clean_input.split() if word]
            if keywords:
                pattern = '|'.join(keywords)
                # Filter CSV for relevant laws/articles
                mask = df[target_col].astype(str).str.contains(pattern, case=False, na=False, regex=True)
                # Limit context to top 2 results and truncate to avoid Token Limit (Error 413)
                context = "\n\n".join(df[mask].head(2)[target_col].astype(str).str[:1500].values)

        # Step C: AI Generation via Groq (Llama 3.3)
        try:
            with st.spinner("Αναζήτηση..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {
                            "role": "system", 
                            "content": (
                                "You are the AI Legal Consultant for Parasecurity. "
                                "Respond strictly in Greek with a professional and neutral tone. "
                                "Do NOT use any names (yours or the user's). "
                                "Provide evidence-based answers using the provided context:\n"
                                f"{context}"
                            )
                        },
                        # Send the last 3 messages for conversational memory
                        *st.session_state.messages[-3:]
                    ]
                )
                answer = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun() # Refresh to show the new message immediately
        except Exception as e:
            st.error(f"AI Service Error: {e}")

    # MESSAGE DISPLAY: Newest messages appear at the top
    st.divider()
    for message in reversed(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ---------------------------------------------------------
# TAB 2: Fake News Detector (Media Fact-Checking)
# ---------------------------------------------------------
with tab2:
    st.header("🔍 Ανίχνευση Ψευδών Ειδήσεων")
    media_file = st.file_uploader("Upload Audio/Video", type=["mp3", "mp4", "wav", "m4a"])
    
    if media_file:
        if st.button("🚀 Έναρξη Ανάλυσης"):
            with st.status("Επεξεργασία...", expanded=True):
                try:
                    # Step 1: Speech-to-Text via Whisper
                    file_bytes = media_file.read()
                    transcription = client.audio.transcriptions.create(
                        file=(media_file.name, file_bytes),
                        model="distil-whisper-large-v3-it",
                        response_format="text", language="el"
                    )
                    
                    # Step 2: Legal Fact-Checking based on the transcript
                    check_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": f"Fact-check this based on Greek legal standards: {transcription[:3000]}"}]
                    )
                    st.success(check_res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Analysis Error: {e}")