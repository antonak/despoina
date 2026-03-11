import streamlit as st
import pandas as pd
import chromadb
from groq import Groq

# 1. Τίτλος (Κανονικά Ελληνικά!)
st.title("⚖️ Greek Legal AI Assistant")
st.subheader("Σύμβουλος Νομοθεσίας & Πρακτικών Βουλής")

# 2. Σύνδεση με Groq (μέσω Streamlit Secrets)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. Φόρτωση Δεδομένων (RAG Logic)
# Εδώ βάλε το path του CSV σου
csv_path = "praktika_2025_2026/laws_articles.csv"

@st.cache_resource
def load_data():
    # Εδώ το Streamlit διαβάζει UTF-8 χωρίς πρόβλημα
    df = pd.read_csv(csv_path)
    return df

df = load_data()

# 4. Chat Interface
user_input = st.chat_input("Ρωτήστε με για τη νομοθεσία...")

if user_input:
    st.chat_message("user").write(user_input)
    
    # Εδώ μπαίνει το RAG Retrieval (ChromaDB)
    # ... (ο κώδικας που βρίσκει τα σχετικά άρθρα) ...
    
    # Απάντηση από το AI
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": user_input}]
    )
    
    st.chat_message("assistant").write(response.choices[0].message.content)