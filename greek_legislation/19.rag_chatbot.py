import streamlit as st
import pandas as pd
import os
from groq import Groq

# 1. Βασικές Ρυθμίσεις
st.set_page_config(page_title="Greek Legal AI", page_icon="⚖️")
st.title("⚖️ Greek Legal AI Assistant")
st.subheader("Σύμβουλος Νομοθεσίας & Πρακτικών Βουλής")

# 2. Σύνδεση με Groq (μέσω Streamlit Secrets)
if "GROQ_API_KEY" not in st.secrets:
    st.error("Παρακαλώ πρόσθεσε το 'GROQ_API_KEY' στα Secrets του Streamlit Cloud.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. Φόρτωση Δεδομένων (CSV) με αυτόματο εντοπισμό στήλης
@st.cache_data
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Προσπαθούμε να βρούμε το CSV στο path που είχαμε ορίσει
    csv_path = os.path.join(current_dir, "praktika_2025_2026/laws_articles.csv")
    
    if not os.path.exists(csv_path):
        st.error(f"Δεν βρέθηκε το αρχείο: {csv_path}")
        return None
    
    df = pd.read_csv(csv_path)
    return df

df = load_data()

# 4. Διαχείριση Ιστορικού Συνομιλίας
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Κύρια Λειτουργία Chat
if prompt := st.chat_input("Ρωτήστε με για τη νομοθεσία (π.χ. 'Επιτρέπονται οι διαδηλώσεις;')"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # --- RAG LOGIC: Αναζήτηση στο Context ---
    context = ""
    if df is not None:
        # Ψάχνουμε ποια στήλη έχει το κείμενο (π.χ. 'text', 'content', 'article')
        potential_cols = [c for c in df.columns if any(word in c.lower() for word in ['text', 'content', 'article', 'άρθρο', 'κειμενο'])]
        text_col = potential_cols[0] if potential_cols else df.columns[-1]
        
        # Απλή αναζήτηση με keywords στο CSV
        keywords = prompt.split()
        mask = df[text_col].astype(str).str.contains('|'.join(keywords), case=False, na=False)
        relevant_df = df[mask].head(3)
        
        if not relevant_df.empty:
            context = "\n".join(relevant_df[text_col].values)

    # --- Κλήση στην Groq ---
    with st.chat_message("assistant"):
        try:
            with st.spinner("Αναζήτηση στη νομοθεσία..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": f"Είσαι νομικός βοηθός. Απάντα στα ελληνικά. Χρησιμοποίησε το παρακάτω context αν είναι σχετικό:\n{context}"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"Σφάλμα Groq: {e}")