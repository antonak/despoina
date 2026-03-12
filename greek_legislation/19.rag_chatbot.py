import streamlit as st
import pandas as pd
import os
from groq import Groq

# 1. Βασικές Ρυθμίσεις Σελίδας
st.set_page_config(page_title="Greek Legal AI | Parasecurity", page_icon="⚖️", layout="wide")

# --- SIDEBAR: Πληροφορίες Ανάπτυξης ---
with st.sidebar:
    st.image("https://grelections.parasecurity.edu.gr/static/images/logo.png", width=100) # Αν υπάρχει logo, αλλιώς παρέλειψέ το
    st.title("About Project")
    st.markdown("""
    ### 🛠️ Development
    Developed by **[Parasecurity](https://grelections.parasecurity.edu.gr/)**
    
    ### 🏛️ Institutions
    * **FORTH** (Institute of Computer Science)
    * **Technical University of Crete**
    
    ### ℹ️ Info
    Αυτό το εργαλείο χρησιμοποιεί τεχνολογία **RAG** για την ανάλυση της Ελληνικής Νομοθεσίας και των Πρακτικών της Βουλής.
    
    [Περισσότερες πληροφορίες](https://grelections.parasecurity.edu.gr/about)
    """)
    st.divider()
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# --- ΚΥΡΙΟ ΜΕΡΟΣ ΕΦΑΡΜΟΓΗΣ ---
st.title("⚖️ Greek Legal AI Assistant")
st.caption("Powered by Parasecurity @ FORTH & TUC")

# 2. Σύνδεση με Groq
if "GROQ_API_KEY" not in st.secrets:
    st.error("Παρακαλώ πρόσθεσε το 'GROQ_API_KEY' στα Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. Φόρτωση Δεδομένων
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "praktika_2025_2026/laws_articles.csv")
    if not os.path.exists(csv_path):
        return None
    return pd.read_csv(csv_path)

df = load_data()

# 4. Διαχείριση Ιστορικού
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Chat Input & RAG
if prompt := st.chat_input("Ρωτήστε τη Δέσποινα..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    context = ""
    if df is not None:
        potential_cols = [c for c in df.columns if any(w in c.lower() for w in ['text', 'content', 'article', 'άρθρο'])]
        text_col = potential_cols[0] if potential_cols else df.columns[-1]
        
        keywords = prompt.split()
        mask = df[text_col].astype(str).str.contains('|'.join(keywords), case=False, na=False)
        relevant_df = df[mask].head(3)
        if not relevant_df.empty:
            context = "\n".join(relevant_df[text_col].values)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Αναζήτηση στη βάση δεδομένων της Parasecurity..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"Είσαι η Δέσποινα, AI βοηθός της Parasecurity. Απάντα στα ελληνικά χρησιμοποιώντας αυτό το context:\n{context}"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"Σφάλμα: {e}")