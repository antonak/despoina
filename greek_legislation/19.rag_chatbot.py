import streamlit as st
import pandas as pd
import os
import re
from groq import Groq

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Parasecurity Legal AI", page_icon="⚖️", layout="wide")

# --- SUSPICIOUS CHARACTER DETECTION FUNCTION ---
def detect_suspicious_characters(text):
    # Εντοπίζει κυριλλικούς χαρακτήρες (π.χ. д, л, π, κτλ) μέσα σε ελληνικό κείμενο
    cyrillic_pattern = re.compile(r'[а-яА-ЯёЁ]')
    found = cyrillic_pattern.findall(text)
    return list(set(found)) # Επιστρέφει μοναδικούς ύποπτους χαρακτήρες

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #d32f2f; color: white; font-weight: bold; }
    .warning-box { padding: 10px; border: 2px solid #ff4b4b; border-radius: 5px; background-color: #ffeaea; color: #b22222; }
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

# --- 4. TABS CREATION ---
tab1, tab2 = st.tabs(["💬 Νομικός Σύμβουλος (Chat)", "🔍 Fake News Detector (Audio/Video)"])

# ---------------------------------------------------------
# TAB 1: Chatbot (RAG) with Forensic Check
# ---------------------------------------------------------
with tab1:
    st.header("⚖️ Συζήτηση με τη Νομοθεσία")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # TOP INPUT UI
    with st.container():
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Ρωτήστε για τους νόμους...", placeholder="π.χ. Τι είναι τα докумένττα;")
            submit_button = st.form_submit_button("Αποστολή 🚀")

    if submit_button and user_input:
        # Check for suspicious characters before processing
        suspicious = detect_suspicious_characters(user_input)
        if suspicious:
            st.warning(f"⚠️ **ΠΡΟΣΟΧΗ**: Εντοπίστηκαν ξένοι/ύποπτοι χαρακτήρες στο ερώτημά σας: {', '.join(suspicious)}. Αυτό μπορεί να επηρεάσει την ποιότητα της απάντησης.")

        st.session_state.messages.append({"role": "user", "content": user_input})

        # Optimized RAG Logic
        context = ""
        if df is not None:
            text_cols = [c for c in df.columns if any(w in c.lower() for w in ['text', 'content', 'άρθρο'])]
            target_col = text_cols[0] if text_cols else df.columns[-1]
            keywords = user_input.split()
            mask = df[target_col].astype(str).str.contains('|'.join(keywords), case=False, na=False)
            context_list = df[mask].head(2)[target_col].astype(str).str[:1500].values
            context = "\n\n".join(context_list)

        # AI Processing
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"Είσαι AI βοηθός της Parasecurity. Αν το context περιέχει περίεργους χαρακτήρες, επισήμανέ το στον χρήστη. Context:\n{context}"},
                    *st.session_state.messages[-3:], 
                ]
            )
            answer = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()
        except Exception as e:
            st.error(f"Σφάλμα AI: {e}")

    # MESSAGE DISPLAY
    st.divider()
    for message in reversed(st.session_state.messages):
        # UI Check: If message contains Cyrillic, mark it in the chat
        is_suspicious = detect_suspicious_characters(message["content"])
        with st.chat_message(message["role"]):
            if is_suspicious:
                st.markdown(f"🚩 *[Εντοπίστηκαν ύποπτοι χαρακτήρες: {', '.join(is_suspicious)}]*")
            st.markdown(message["content"])

# ---------------------------------------------------------
# TAB 2: Fake News Detector
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
                    
                    # Check transcription for foreign letters
                    suspicious_trans = detect_suspicious_characters(transcription)
                    if suspicious_trans:
                        st.error(f"🚩 **Alert**: Η μεταγραφή περιέχει μη-ελληνικούς χαρακτήρες ({', '.join(suspicious_trans)}). Πιθανή ένδειξη κακόβουλης πηγής.")

                    check_prompt = f"Είσαι Fact-Checker. Έλεγξε για παραπληροφόρηση και περίεργους χαρακτήρες: {transcription[:3000]}"
                    check_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": check_prompt}]
                    )
                    
                    status.update(label="Ολοκληρώθηκε!", state="complete")
                    st.success(check_res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Σφάλμα: {e}")