import streamlit as st
import pandas as pd
import os
from openai import OpenAI

# Page Configuration
st.set_page_config(page_title="Greek Legal Labyrinth AI", layout="wide")

# API Settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "YOUR_GROQ_API_KEY_HERE")
client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

CSV_FILE = "praktika_2025_2026/laws_articles.csv"

@st.cache_data
def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame()

def analyze_with_ai(text):
    # Prompt is now instructing the AI to read Greek but respond in English
    prompt = f"""
    You are a legal analyst. Read the following Greek legal article and identify:
    1. Legal ambiguities or 'loopholes'.
    2. A comprehensibility score (1-10) for the average citizen.
    Respond in English, keeping it brief and concise with bullet points.
    Text: {text[:2500]}
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# --- UI ---
st.title("🏛️ Greek LegalTech AI Auditor")
st.markdown("Analysis of complexity and interconnections within Greek Legislation using Llama 3.3.")

df = load_data()

if df.empty:
    st.error("Law database not found! Please check the CSV path.")
else:
    # Creating Tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Law Analysis (Live AI)", "🕸️ Legal Labyrinth", "📊 Illusion of Simplicity"])

    with tab1:
        st.header("Select and Analyze Article")
        laws_list = df['Law'].unique()
        selected_law = st.selectbox("Select Law to analyze:", laws_list)
        
        # Filter articles for the selected law
        articles = df[df['Law'] == selected_law]
        selected_article_row = st.selectbox("Select Article:", articles['Article'].tolist())
        
        # Display text
        article_text = articles[articles['Article'] == selected_article_row]['Text'].values[0]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Original Text (Official Greek Law)")
            st.text_area("", article_text, height=400)
            
        with col2:
            st.subheader("🤖 AI Audit (Groq / Llama 3.3)")
            if st.button("Analyze Article Now!"):
                with st.spinner("The model is reading the text..."):
                    try:
                        ai_result = analyze_with_ai(article_text)
                        st.success("Analysis complete!")
                        st.markdown(ai_result)
                    except Exception as e:
                        st.error(f"API Error: {e}")

    with tab2:
        st.header("Network of Interdependencies (Cross-References)")
        st.markdown("Each line represents a citation from one law to another, creating a chaotic web of legislation.")
        img_path = "praktika_2025_2026/legal_network.png"
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
        else:
            st.warning("Graph not found. Please run the network generation script first.")

    with tab3:
        st.header("Political Rhetoric vs. Legal Reality")
        st.markdown("How often are laws advertised as 'simplifications' actually labyrinthine?")
        img_path_2 = "praktika_2025_2026/illusion_of_simplicity.png"
        if os.path.exists(img_path_2):
            st.image(img_path_2, use_container_width=True)
        else:
            st.warning("Graph not found. Please run the systemic analysis script first.")