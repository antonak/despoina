import streamlit as st
import pandas as pd
import os
from groq import Groq

# --- ΡΥΘΜΙΣΕΙΣ ΣΕΛΙΔΑΣ ---
st.set_page_config(page_title="Greek Legal AI", page_icon="⚖️", layout="centered")

st.title("⚖️ Greek Legal AI Assistant")
st.subheader("Σύμβουλος Νομοθεσίας & Πρακτικών Βουλής")
st.info("Το σύστημα αναλύει τα πρακτικά της περιόδου 2025-2026.")

# --- ΣΥΝΔΕΣΗ ΜΕ GROQ ---
# Βεβαιώσου ότι έχεις βάλει το GROQ_API_KEY στα Secrets του Streamlit
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Λείπει το API Key από τα Secrets! Παρακαλώ πρόσθεσε το GROQ_API_KEY.")
    st.stop()

# --- ΦΟΡΤΩΣΗ ΔΕΔΟΜΕΝΩΝ (CSV) ---
@st.cache_data
def load_legal_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "praktika_2025_2026/laws_articles.csv")
    
    if not os.path.exists(csv_path):
        st.error(f"Το αρχείο δεν βρέθηκε στο: {csv_path}")
        return None
    
    # Διαβάζουμε το CSV (εξ ορισμού UTF-8 στο Streamlit Cloud)
    df = pd.read_csv(csv_path)
    return df

df = load_legal_data()

# --- CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Εμφάνιση ιστορικού συνομιλίας
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Είσοδος χρήστη
user_input = st.chat_input("Πώς μπορώ να σας βοηθήσω με τη νομοθεσία;")

if user_input:
    # 1. Εμφάνιση ερώτησης χρήστη
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Απλή Αναζήτηση στο CSV (Basic RAG Logic)
    # Εδώ βρίσκουμε τις πιο σχετικές γραμμές από το CSV βάσει λέξεων-κλειδιών
    context = ""
    if df is not None:
        keywords = user_input.split()
        # Φιλτράρουμε το DF για να βρούμε σχετικά άρθρα
        relevant_rows = df[df.apply(lambda row: any(k.lower() in str(row).lower() for k in keywords), axis=1)]
        if not relevant_rows.empty:
            context = "Σχετικά αποσπάσματα από τη νομοθεσία:\n" + "\n".join(relevant_rows.iloc[:3]['article_text'].values)

    # 3. Κλήση στην Groq
    try:
        with st.spinner("Η Despoina αναλύει τη νομοθεσία..."):
            # Σύνθεση του Prompt με το Context (RAG)
            system_prompt = f"""
            Είσαι η Despoina, ένας εξειδικευμένος νομικός βοηθός για την Ελληνική νομοθεσία.
            Χρησιμοποίησε το παρακάτω context για να απαντήσεις. 
            Αν δεν υπάρχει σχετική πληροφορία στο context, χρησιμοποίησε τις γενικές σου γνώσεις αλλά ενημέρωσε τον χρήστη.
            Απάντα πάντα στα Ελληνικά με σοβαρό και τεκμηριωμένο ύφος.
            
            CONTEXT:
            {context}
            """

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.3, # Χαμηλό temperature για μεγαλύτερη ακρίβεια
            )
            
            answer = response.choices[0].message.content

        # 4. Εμφάνιση απάντησης
        with st.chat_message("assistant"):
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        st.error(f"Σφάλμα επικοινωνίας με το AI: {e}")

# Κουμπί καθαρισμού
if st.sidebar.button("Καθαρισμός Συνομιλίας"):
    st.session_state.messages = []
    st.rerun()