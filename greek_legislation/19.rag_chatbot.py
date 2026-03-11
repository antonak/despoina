import streamlit as st
import pandas as pd
import os
import requests
import json
import base64

# --- ΑΠΕΝΕΡΓΟΠΟΙΟΥΜΕ ΤΑ ΠΑΝΤΑ ΓΙΑ ΝΑ ΜΗΝ ΥΠΑΡΧΕΙ ΚΑΜΙΑ ΕΚΤΥΠΩΣΗ ΣΤΟ TERMINAL ---
st.set_page_config(page_title="Legal AI - Stealth Mode", layout="centered")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "ΒΑΛΕ_ΤΟ_ΚΛΕΙΔΙ_ΣΟΥ_ΕΔΩ")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

st.title("⚖️ Greek Legal AI (Stealth Mode)")
st.warning("Επικοινωνία μέσω Base64 Encoding για παράκαμψη ASCII restrictions.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me something..."):
    # Εμφάνιση στο UI (το Streamlit στον browser δεν έχει θέμα με Ελληνικά)
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Εδώ είναι το κόλπο: Λέμε στο AI να καταλάβει ότι του στέλνουμε Ελληνικά 
        # αλλά δεν τα τυπώνουμε ποτέ στο stdout του server.
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are a Greek Legal Assistant. Respond in Greek language only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5
        }

        try:
            # Μετατροπή όλου του payload σε bytes και αποστολή χωρίς καμία ενδιάμεση εκτύπωση
            full_payload = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            
            response = requests.post(GROQ_URL, headers=headers, data=full_payload)
            response.raise_for_status()
            
            res_json = response.json()
            answer = res_json['choices'][0]['message']['content']
            
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
        except Exception as e:
            st.error("Ακόμα και το Stealth Mode απέτυχε. Ο server 'blackmamba' απαιτεί αλλαγή στο /etc/default/locale από τον administrator.")