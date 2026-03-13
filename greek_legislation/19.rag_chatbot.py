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
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 1. ΣΤΑΘΕΡΟ INPUT ΣΤΗΝ ΚΟΡΥΦΗ
    with st.form(key="top_input_form", clear_on_submit=True):
        user_input = st.text_input("Ρωτήστε για τους νόμους:", placeholder="π.χ. Τι λέει το άρθρο 5 για το Κτηματολόγιο;")
        submit_button = st.form_submit_button("Αποστολή 🚀")

    # 2. CONTAINER ΓΙΑ ΤΑ ΜΗΝΥΜΑΤΑ
    chat_container = st.container()

    if submit_button and user_input:
        suspicious = detect_suspicious_characters(user_input)
        clean_input = sanitize_greek_text(user_input)
        
        display_text = user_input
        if suspicious:
            display_text = f"🚩 [Εντοπίστηκαν ύποπτοι χαρακτήρες: {', '.join(suspicious)}]\n\n{user_input}"
        
        # Αποθήκευση ερώτησης
        st.session_state.messages.append({"role": "user", "content": display_text})

        # RAG Logic
        context = ""
        if df is not None:
            text_cols = [c for c in df.columns if any(w in c.lower() for w in ['text', 'content', 'άρθρο'])]
            target_col = text_cols[0] if text_cols else df.columns[-1]
            keywords = [re.escape(word) for word in clean_input.split() if word]
            if keywords:
                pattern = '|'.join(keywords)
                mask = df[target_col].astype(str).str.contains(pattern, case=False, na=False, regex=True)
                context = "\n\n".join(df[mask].head(2)[target_col].astype(str).str[:1500].values)

        # AI Generation
        try:
            with st.spinner("Αναζήτηση..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"You are the AI Legal Consultant for Parasecurity. Respond strictly in Greek. Context:\n{context}"},
                        *st.session_state.messages[-5:]
                    ]
                )
                answer = response.choices[0].message.content
                # Αποθήκευση απάντησης
                st.session_state.messages.append({"role": "assistant", "content": answer})
                st.rerun()
        except Exception as e:
            st.error(f"AI Service Error: {e}")

    # 3. ΕΜΦΑΝΙΣΗ: Τελευταίο ζευγάρι πρώτο, αλλά μέσα στο ζευγάρι User -> Assistantthesrhs
    with chat_container:
        st.write("---")
        # Ομαδοποιούμε τα μηνύματα σε ζευγάρια (User, Assistant)
        # και αντιστρέφουμε τη σειρά των ζευγαριών
        msgs = st.session_state.messages
        for i in range(len(msgs) - 1, -1, -2):
            # Αν υπάρχει ζευγάρι (User + Assistant)
            if i > 0 and msgs[i-1]["role"] == "user":
                # Δείχνουμε πρώτα τον User (i-1)
                with st.chat_message("user"):
                    st.markdown(msgs[i-1]["content"])
                # Και μετά τον Assistant (i)
                with st.chat_message("assistant"):
                    st.markdown(msgs[i]["content"])
                st.divider() # Μικρή γραμμή ανάμεσα στα ζευγάρια
            
            # Περίπτωση που υπάρχει μόνο ερώτηση (πριν απαντήσει το AI)
            elif msgs[i]["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msgs[i]["content"])

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
