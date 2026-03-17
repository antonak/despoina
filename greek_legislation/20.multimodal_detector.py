import streamlit as st
import os
import glob
import re
import trafilatura
import base64
import yt_dlp
import subprocess
from youtube_transcript_api import YouTubeTranscriptApi
from groq import Groq

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Parasecurity | AI Lab", page_icon="✨", layout="centered")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1F1F1F; font-family: 'Google Sans', Arial, sans-serif; }
    header { visibility: hidden; }
    .stTextArea textarea, .stTextInput input {
        background-color: #F0F4F9 !important; border: none !important;
        border-radius: 24px !important; padding: 16px !important;
    }
    .stButton>button { 
        border-radius: 24px !important; width: 100%; 
        height: 50px; font-weight: bold;
    }
    div.stButton > button:first-child {
        background-color: #1a73e8 !important; color: white !important; border: none !important;
    }
    .stMetric { background-color: #FFFFFF; padding: 10px; border-radius: 16px; border: 1px solid #E1E5EA; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1a73e8;'>✨ Parasecurity Lab</h1>", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "analysis_report" not in st.session_state: st.session_state.analysis_report = ""
if "selected_lang" not in st.session_state: st.session_state.selected_lang = "Ελληνικά 🇬🇷"

# --- 3. INITIALIZE GROQ ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing API Key in Secrets.")
    st.stop()
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.sidebar.markdown("### ⚙️ Engine Settings")
selected_model_id = st.sidebar.selectbox("Model:", ["llama-3.3-70b-versatile", "llama-3.1-405b-reasoning"])

# --- 4. INPUT INTERFACE ---
source = st.radio("Επιλογή Πηγής:", ["📝 Κείμενο", "🔗 YouTube", "📰 Web", "🖼️ Εικόνα"], horizontal=True)

user_payload = None
image_payload = None

if source == "📝 Κείμενο":
    user_payload = st.text_area("Κείμενο:", placeholder="Επικολλήστε εδώ...", height=200)

elif source == "🔗 YouTube":
    user_payload = st.text_input("YouTube URL:", placeholder="https://youtube.com/watch?v=...")

elif source == "📰 Web":
    user_payload = st.text_input("Link Άρθρου:", placeholder="https://news-site.com/article...")

elif source == "🖼️ Εικόνα":
    up_file = st.file_uploader("Ανεβάστε Εικόνα:", type=["jpg", "png", "jpeg"])
    if up_file:
        st.image(up_file, width=250)
        image_payload = {"mime_type": up_file.type, "data": up_file.read()}

# --- 5. THE MAGIC BUTTON (SCRAPE + ANALYZE) ---
if st.button("🚀 Έναρξη Πλήρους Ανάλυσης"):
    if not user_payload and not image_payload:
        st.warning("Παρακαλώ εισάγετε κάποιο περιεχόμενο πρώτα!")
    else:
        with st.status("Εκτέλεση Διεργασιών...", expanded=True) as status:
            final_text = ""
            
            try:
                # STEP A: SCRAPING LOGIC
                if source == "🔗 YouTube":
                    status.write("🔍 Ανάκτηση δεδομένων από YouTube...")
                    v_id = user_payload.split("v=")[-1].split("&")[0] if "v=" in user_payload else user_payload.split("/")[-1]
                    try:
                        t = YouTubeTranscriptApi.get_transcript(v_id, languages=['el', 'en'])
                        final_text = " ".join([i['text'] for i in t])
                    except:
                        status.write("🎧 Οι υπότιτλοι απέτυχαν. Προσπάθεια μεταγραφής ήχου...")
                        ydl_opts = {'format': 'm4a/best', 'outtmpl': f'tmp_{v_id}.%(ext)s', 'quiet': True}
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([user_payload])
                        audio_path = glob.glob(f"tmp_{v_id}.*")[0]
                        with open(audio_path, "rb") as f:
                            ts = client.audio.transcriptions.create(file=(audio_path, f.read()), model="whisper-large-v3")
                            final_text = ts.text
                        os.remove(audio_path)

                elif source == "📰 Web":
                    status.write("🌐 Ανάγνωση σελίδας...")
                    final_text = trafilatura.extract(trafilatura.fetch_url(user_payload))
                
                elif source == "📝 Κείμενο":
                    final_text = user_payload

                # STEP B: AI ANALYSIS
                status.write("🧠 Ο κινητήρας AI αναλύει το περιεχόμενο...")
                sys_prompt = """Forensic Investigator Mode. 
                STRICT FORMAT: 
                <GREEK> [Analysis in Greek] </GREEK>
                <ENGLISH> [Analysis in English] </ENGLISH>
                SCORE: [0-100]"""

                if source == "🖼️ Εικόνα":
                    b64_img = base64.b64encode(image_payload["data"]).decode('utf-8')
                    response = client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[{"role": "system", "content": sys_prompt},
                                  {"role": "user", "content": [
                                      {"type": "text", "text": "Analyze for propaganda/fake news."},
                                      {"type": "image_url", "image_url": {"url": f"data:{image_payload['mime_type']};base64,{b64_img}"}}
                                  ]}]
                    )
                else:
                    response = client.chat.completions.create(
                        messages=[{"role": "system", "content": sys_prompt},
                                  {"role": "user", "content": final_text}],
                        model=selected_model_id, temperature=0.1
                    )
                
                st.session_state.analysis_report = response.choices[0].message.content
                status.update(label="✅ Η ανάλυση ολοκληρώθηκε!", state="complete", expanded=False)

            except Exception as e:
                st.error(f"Σφάλμα: {str(e)}")

# --- 6. DISPLAY RESULTS (TABS FIXED) ---
if st.session_state.analysis_report:
    report = st.session_state.analysis_report
    
    # Parsing Score
    s_match = re.search(r"SCORE:\s*(\d+)", report)
    score = int(s_match.group(1)) if s_match else 50
    color = "#1E8E3E" if score > 70 else "#F9AB00" if score > 40 else "#D93025"
    
    st.markdown(f"<div class='stMetric'><strong>Αξιοπιστία:</strong> <span style='color:{color}; font-size: 26px; font-weight: bold;'>{score}%</span></div>", unsafe_allow_html=True)

    # Parsing Tags (The Robust Way)
    gr_part = re.search(r'<GREEK>(.*?)</GREEK>', report, re.DOTALL | re.IGNORECASE)
    en_part = re.search(r'<ENGLISH>(.*?)</ENGLISH>', report, re.DOTALL | re.IGNORECASE)

    gr_txt = gr_part.group(1).strip() if gr_part else "Σφάλμα ανάκτησης ελληνικού κειμένου."
    en_txt = en_part.group(1).strip() if en_part else "Error retrieving English text."

    # Language Selector
    c1, c2, _ = st.columns([1, 1, 3])
    if c1.button("Ελληνικά"): st.session_state.selected_lang = "Ελληνικά 🇬🇷"
    if c2.button("English"): st.session_state.selected_lang = "English 🇬🇧"

    st.markdown(f"<div style='background-color: #F0F4F9; padding: 25px; border-radius: 20px; border-left: 8px solid {color};'>{gr_txt if st.session_state.selected_lang == 'Ελληνικά 🇬🇷' else en_txt}</div>", unsafe_allow_html=True)