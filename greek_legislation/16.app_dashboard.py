import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# Ρύθμιση Σελίδας
st.set_page_config(page_title="Greek Legal Labyrinth AI", layout="wide")

# Ρυθμίσεις API
# Αντικατάστησε με το κλειδί σου ή άστο να το διαβάζει από το περιβάλλον
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "ΒΑΛΕ_ΤΟ_ΚΛΕΙΔΙ_ΣΟΥ_ΕΔΩ_ΑΝ_ΧΡΕΙΑΖΕΤΑΙ")
client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

CSV_FILE = "praktika_2025_2026/laws_articles.csv"

@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame()

def analyze_with_ai(text):
    prompt = f"""
    Είσαι νομικός αναλυτής. Διάβασε το παρακάτω άρθρο και εντόπισε:
    1. Νομικές ασάφειες ή 'παραθυράκια'.
    2. Βαθμολογία κατανοησιμότητας (1-10) για τον απλό πολίτη.
    Απάντησε στα Ελληνικά, σύντομα και περιεκτικά με bullet points.
    Κείμενο: {text[:2500]}
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# --- UI ---
st.title("🏛️ Greek LegalTech AI Auditor")
st.markdown("Ανάλυση πολυπλοκότητας και διασυνδέσεων της Ελληνικής Νομοθεσίας με χρήση Llama 3.3.")

df = load_data()

if df.empty:
    st.error("Δεν βρέθηκε η βάση δεδομένων των νόμων!")
else:
    # Δημιουργία Tabs για οργάνωση
    tab1, tab2, tab3 = st.tabs(["🔍 Ανάλυση Νόμου (Live AI)", "🕸️ Νομικός Λαβύρινθος", "📊 Illusion of Simplicity"])

    with tab1:
        st.header("Επιλογή και Ανάλυση Άρθρου")
        laws_list = df['Law'].unique()
        selected_law = st.selectbox("Επίλεξε Νόμο προς ανάλυση:", laws_list)
        
        # Φιλτράρισμα άρθρων για τον επιλεγμένο νόμο
        articles = df[df['Law'] == selected_law]
        selected_article_row = st.selectbox("Επίλεξε Άρθρο:", articles['Article'].tolist())
        
        # Εμφάνιση κειμένου
        article_text = articles[articles['Article'] == selected_article_row]['Text'].values[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Αυθεντικό Κείμενο (ΦΕΚ)")
            st.text_area("", article_text, height=400)
            
        with col2:
            st.subheader("🤖 AI Audit (Groq / Llama 3.3)")
            if st.button("Ανάλυση Άρθρου τώρα!"):
                with st.spinner("Το μοντέλο διαβάζει το κείμενο..."):
                    try:
                        ai_result = analyze_with_ai(article_text)
                        st.success("Η ανάλυση ολοκληρώθηκε!")
                        st.markdown(ai_result)
                    except Exception as e:
                        st.error(f"Σφάλμα API: {e}")

    with tab2:
        st.header("Δίκτυο Αλληλεξαρτήσεων (Cross-References)")
        st.markdown("Κάθε γραμμή αντιπροσωπεύει μια παραπομπή από έναν νόμο σε κάποιον άλλον, δημιουργώντας έναν χαοτικό ιστό.")
        img_path = "praktika_2025_2026/legal_network.png"
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.warning("Το γράφημα δεν βρέθηκε. Τρέξε το script 14 πρώτα.")

    with tab3:
        st.header("Πολιτική Ρητορεία vs Νομική Πραγματικότητα")
        st.markdown("Πόσο συχνά νόμοι που διαφημίζονται ως 'απλοποιήσεις' είναι στην πραγματικότητα δαιδαλώδεις;")
        img_path_2 = "praktika_2025_2026/illusion_of_simplicity.png"
        if os.path.exists(img_path_2):
            st.image(img_path_2, use_container_width=True)
        else:
            st.warning("Το γράφημα δεν βρέθηκε. Τρέξε το script 15 πρώτα.")