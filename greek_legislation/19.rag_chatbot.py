import streamlit as st
import pandas as pd
import chromadb
from groq import Groq
import os

# 1. Τίτλος (Κανονικά Ελληνικά!)
st.title("⚖️ Greek Legal AI Assistant")
st.subheader("Σύμβουλος Νομοθεσίας & Πρακτικών Βουλής")

# 2. Σύνδεση με Groq (μέσω Streamlit Secrets)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# 3. Φόρτωση Δεδομένων (RAG Logic)
# Εδώ βάλε το path του CSV σου
 


# Παίρνουμε το path του φακέλου στον οποίο βρίσκεται το script
current_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(current_dir, "praktika_2025_2026/laws_articles.csv")
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
   # Χρησιμοποιούμε το πιο πρόσφατο και σταθερό μοντέλο της Groq
try:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", 
        messages=[
            {"role": "system", "content": "Είσαι ένας έμπειρος Έλληνας νομικός βοηθός. Απάντα βασισμένος αποκλειστικά στα έγγραφα που σου παρέχονται."},
            {"role": "user", "content": user_input}
        ],
    )
    st.chat_message("assistant").write(response.choices[0].message.content)
except Exception as e:
    st.error(f"Κάτι πήγε στραβά με την Groq: {e}")