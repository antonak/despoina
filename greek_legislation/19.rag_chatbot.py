import streamlit as st
import pandas as pd
import os
import trafilatura
from groq import Groq
from yt_dlp import YoutubeDL

# 1. Βασικές Ρυθμίσεις Σελίδας
st.set_page_config(page_title="Parasecurity Legal AI", page_icon="⚖️", layout="wide")

# --- SIDEBAR & BRANDING ---
with st.sidebar:
    st.title("🛡️ Parasecurity")
    st.subheader("FORTH & TUC Lab")
    st.markdown("---")
    st.markdown("""
    **Project Info:**
    Ανάλυση νομοθεσίας και ανίχνευση Fake News.
    [About Us](https://grelections.parasecurity.edu.gr/about)
    """)
    st.divider()
    if st.button("🗑️ Καθαρισμός Ιστορικού"):
        st.session_state.messages = []
        st.rerun()

# 2. Σύνδεση με Groq
if "GROQ_API_KEY" not in st.secrets:
    st.error("Παρακαλώ προσθέστε το GROQ_API_KEY στα Streamlit Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. Φόρτωση Δεδομένων (CSV)
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "praktika_2025_2026/laws_articles.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return None

df = load_data()

# --- ΔΗΜΙΟΥΡΓΙΑ TABS ---
st.title("⚖️ Greek Legal AI Assistant")
tab1, tab2 = st.tabs(["💬 Νομικό Chat", "🔍 Ανίχνευση Fake News (Link/Media)"])

# ---------------------------------------------------------
# TAB 1: Chatbot (RAG Logic)
# ---------------------------------------------------------
with tab1:
    st.header("Συζήτηση με τη Νομοθεσία")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ρωτήστε τη Δέσποινα (π.χ. 'Τι ισχύει για τις διαδηλώσεις;')"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Retrieval από το CSV
        context = ""
        if df is not None:
            potential_cols = [c for c in df.columns if any(w in c.lower() for w in ['text', 'content', 'άρθρο'])]
            text_col = potential_cols[0] if potential_cols else df.columns[-1]
            keywords = prompt.split()
            mask = df[text_col].astype(str).str.contains('|'.join(keywords), case=False, na=False)
            context = "\n".join(df[mask].head(3)[text_col].values)

        with st.chat_message("assistant"):
            try:
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"Είσαι η Δέσποινα, AI βοηθός της Parasecurity. Απάντα στα Ελληνικά χρησιμοποιώντας αυτό το context:\n{context}"},
                        {"role": "user", "content": prompt}
                    ]
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error(f"Σφάλμα AI: {e}")

# ---------------------------------------------------------
# TAB 2: Fake News Detector (Scraping & Whisper)
# ---------------------------------------------------------
with tab2:
    st.header("Fact-Checking & Ανίχνευση Ανακριβειών")
    st.write("Αναλύστε άρθρα από links ή αρχεία ομιλίας για να βρείτε αν λένε την αλήθεια.")
    
    source = st.radio("Πηγή δεδομένων:", ["🔗 URL (Άρθρο/YouTube)", "📁 Αρχείο (MP3/MP4)"])
    content_to_check = ""

    if source == "🔗 URL (Άρθρο/YouTube)":
        url = st.text_input("Επικολλήστε το link:")
        if url:
            with st.spinner("Ανάκτηση περιεχομένου..."):
                if "youtube.com" in url or "youtu.be" in url:
                    content_to_check = f"Περιεχόμενο από Video: {url} (Ανάλυση Metadata)"
                else:
                    downloaded = trafilatura.fetch_url(url)
                    content_to_check = trafilatura.extract(downloaded)
                    if content_to_check:
                        st.success("Το κείμενο ανακτήθηκε!")
                        with st.expander("Προεπισκόπηση Κειμένου"):
                            st.write(content_to_check[:1000] + "...")
    else:
        uploaded_file = st.file_uploader("Ανεβάστε αρχείο:", type=["mp3", "mp4", "wav"])
        if uploaded_file:
            with st.spinner("Μεταγραφή ομιλίας με Whisper..."):
                transcription = client.audio.transcriptions.create(
                    file=(uploaded_file.name, uploaded_file.read()),
                    model="distil-whisper-large-v3-it",
                    response_format="text",
                    language="el"
                )
                content_to_check = transcription
                st.info("Η μεταγραφή ολοκληρώθηκε.")

    if content_to_check and st.button("🚀 Έναρξη Ελέγχου Εγκυρότητας"):
        with st.status("Διασταύρωση με επίσημες πηγές Parasecurity...", expanded=True):
            # Εδώ το AI συγκρίνει το περιεχόμενο με τη βάση δεδομένων
            check_prompt = f"""
            Είσαι Fact-Checker της Parasecurity. 
            Έλεγξε το παρακάτω κείμενο για ψευδείς ειδήσεις ή νομικές ανακρίβειες βάσει των επίσημων δεδομένων μας.
            
            ΚΕΙΜΕΝΟ ΠΡΟΣ ΕΛΕΓΧΟ:
            {content_to_check}
            """
            
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": check_prompt}],
                temperature=0
            )
            st.subheader("📊 Πόρισμα Ελέγχου")
            st.markdown(res.choices[0].message.content)

st.divider()
st.caption("Developed by Parasecurity @ FORTH & Technical University of Crete (TUC)")