import streamlit as st
import pandas as pd
import os
from groq import Groq

# 1. Βασικές Ρυθμίσεις
st.set_page_config(page_title="Parasecurity Legal AI", page_icon="⚖️", layout="wide")

# --- SIDEBAR & BRANDING ---
with st.sidebar:
    st.title("🛡️ Parasecurity")
    st.subheader("FORTH & TUC Lab")
    st.markdown("[About Project](https://grelections.parasecurity.edu.gr/about)")
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# 2. Σύνδεση με Groq
if "GROQ_API_KEY" not in st.secrets:
    st.error("Προσθέστε το GROQ_API_KEY στα Secrets.")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. Φόρτωση Δεδομένων
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "praktika_2025_2026/laws_articles.csv")
    return pd.read_csv(csv_path) if os.path.exists(csv_path) else None

df = load_data()

# --- ΔΗΜΙΟΥΡΓΙΑ TABS ---
tab1, tab2 = st.tabs(["💬 Νομικός Σύμβουλος (Chat)", "🔍 Fake News Detector (Audio/Video)"])
# ---------------------------------------------------------
# TAB 1: Chatbot (RAG) - Top Input Version
# ---------------------------------------------------------
with tab1:
    st.header("⚖️ Συζήτηση με τη Νομοθεσία")
    
    # Initialize session state for messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 1. TOP INPUT FIELD
    # Using a form helps handle the 'Enter' key properly for a top-mounted input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input("Ρωτήστε για τους νόμους...", placeholder="Πληκτρολογήστε εδώ και πατήστε Enter")
        submit_button = st.form_submit_button("Αποστολή 🚀")

    # 2. CHAT LOGIC
    if (submit_button or user_input) and user_input:
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Basic RAG Logic
        context = ""
        if df is not None:
            potential_cols = [c for c in df.columns if any(w in c.lower() for w in ['text', 'content', 'άρθρο'])]
            text_col = potential_cols[0] if potential_cols else df.columns[-1]
            keywords = user_input.split()
            mask = df[text_col].astype(str).str.contains('|'.join(keywords), case=False, na=False)
            context = "\n".join(df[mask].head(3)[text_col].values)

        # Get AI Response
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"Είσαι AI βοηθός της Parasecurity. Χρησιμοποίησε το context:\n{context}"},
                {"role": "user", "content": user_input}
            ]
        )
        answer = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": answer})
        
        # Rerun to show new messages immediately
        st.rerun()

    # 3. MESSAGE DISPLAY (Bottom section)
    # We display them in REVERSE order if you want the newest on top, 
    # or normal order to keep it like a standard chat.
    st.divider()
    for message in reversed(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
# ---------------------------------------------------------
# TAB 2: Fake News Detector (Whisper + Fact-Check)
# ---------------------------------------------------------
with tab2:
    st.header("🔍 Ανίχνευση Ψευδών Ειδήσεων")
    st.write("Ανεβάστε ένα αρχείο ήχου ή βίντεο για να ελέγξουμε αν οι ισχυρισμοί συμβαδίζουν με τη νομοθεσία.")
    
    media_file = st.file_uploader("Upload Audio/Video", type=["mp3", "mp4", "wav", "m4a"])
    
    if media_file:
        with st.status("Ανάλυση πολυμέσων...", expanded=True) as status:
            # 1. Μεταγραφή
            st.write("Μετατροπή ομιλίας σε κείμενο (Groq Whisper)...")
            transcription = client.audio.transcriptions.create(
                file=(media_file.name, media_file.read()),
                model="distil-whisper-large-v3-it",
                response_format="text",
                language="el"
            )
            st.info(f"Κείμενο: {transcription[:200]}...")

            # 2. Fact-Checking
            st.write("Διασταύρωση με επίσημα πρακτικά...")
            check_prompt = f"Είσαι Fact-Checker της Parasecurity. Έλεγξε αν το παρακάτω κείμενο περιέχει Fake News βάσει της νομοθεσίας: {transcription}"
            
            check_res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": check_prompt}]
            )
            
            status.update(label="Η ανάλυση ολοκληρώθηκε!", state="complete")
            st.subheader("📊 Αποτέλεσμα Ελέγχου")
            st.success(check_res.choices[0].message.content)