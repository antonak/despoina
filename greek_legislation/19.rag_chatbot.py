import streamlit as st
import pandas as pd
import os
from groq import Groq

# --- 1. BASIC CONFIGURATION ---
st.set_page_config(page_title="Parasecurity Legal AI", page_icon="⚖️", layout="wide")

# --- SIDEBAR & BRANDING ---
with st.sidebar:
    st.title("🛡️ Parasecurity")
    st.subheader("FORTH & TUC Lab")
    st.markdown("[About Project](https://grelections.parasecurity.edu.gr/about)")
    st.divider()
    # Clear history logic
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
    # Ensure this path matches your GitHub structure
    csv_path = os.path.join(current_dir, "praktika_2025_2026/laws_articles.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None

df = load_data()

# --- 4. TABS CREATION ---
tab1, tab2 = st.tabs(["💬 Νομικός Σύμβουλος (Chat)", "🔍 Fake News Detector (Audio/Video)"])

# ---------------------------------------------------------
# TAB 1: Chatbot (RAG) with TOP INPUT
# ---------------------------------------------------------
with tab1:
    st.header("⚖️ Συζήτηση με τη Νομοθεσία")
    
    # Initialize message history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # UI Fix: Input stays at the top
    with st.container():
        with st.form("chat_form", clear_on_submit=True):
            user_query = st.text_input("Ρωτήστε για τους νόμους:", placeholder="π.χ. Τι προβλέπει το άρθρο 5...")
            submitted = st.form_submit_button("Αποστολή 🚀")

        if submitted and user_query:
            # 1. Add User Message to History
            st.session_state.messages.append({"role": "user", "content": user_query})

            # 2. RAG Logic (Context Retrieval)
            context = ""
            if df is not None:
                # Find the column containing the law text
                text_cols = [c for c in df.columns if any(w in c.lower() for w in ['text', 'content', 'άρθρο'])]
                target_col = text_cols[0] if text_cols else df.columns[-1]
                
                # Simple keyword match
                keywords = user_query.split()
                mask = df[target_col].astype(str).str.contains('|'.join(keywords), case=False, na=False)
                context = "\n".join(df[mask].head(3)[target_col].values)

            # 3. Get AI Response from Groq
            try:
                chat_completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"Είσαι ο AI Νομικός Σύμβουλος της Parasecurity. Χρησιμοποίησε το context για να απαντήσεις τεκμηριωμένα:\n{context}"},
                        *st.session_state.messages[-5:], # Include last 5 messages for conversation memory
                    ]
                )
                assistant_res = chat_completion.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": assistant_res})
                st.rerun() # Refresh to show response
            except Exception as e:
                st.error(f"Σφάλμα AI: {e}")

    # 4. DISPLAY MESSAGES (Newest on Top)
    st.divider()
    for msg in reversed(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ---------------------------------------------------------
# TAB 2: Fake News Detector
# ---------------------------------------------------------
with tab2:
    st.header("🔍 Ανίχνευση Ψευδών Ειδήσεων")
    st.write("Ανεβάστε αρχείο για διασταύρωση με τη νομοθεσία.")
    
    media_file = st.file_uploader("Upload Audio/Video", type=["mp3", "mp4", "wav", "m4a"])
    
    if media_file:
        if st.button("🚀 Έναρξη Ανάλυσης"):
            with st.status("Επεξεργασία...", expanded=True) as status:
                try:
                    # Transcription via Whisper
                    st.write("Μεταγραφή ομιλίας (Whisper)...")
                    # Note: We must reset file pointer if read previously
                    file_content = media_file.read()
                    transcription = client.audio.transcriptions.create(
                        file=(media_file.name, file_content),
                        model="distil-whisper-large-v3-it",
                        response_format="text",
                        language="el"
                    )
                    
                    st.info(f"Κείμενο που εντοπίστηκε: {transcription[:300]}...")

                    # Fact-Check via Llama
                    st.write("Έλεγχος εγκυρότητας...")
                    check_prompt = f"Είσαι Fact-Checker της Parasecurity. Ανάλυσε αν το κείμενο περιέχει παραπληροφόρηση βάσει της νομοθεσίας: {transcription}"
                    
                    check_res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": check_prompt}]
                    )
                    
                    status.update(label="Η ανάλυση ολοκληρώθηκε!", state="complete")
                    st.subheader("📊 Πόρισμα Ελέγχου")
                    st.success(check_res.choices[0].message.content)
                except Exception as e:
                    st.error(f"Σφάλμα κατά την επεξεργασία: {e}")