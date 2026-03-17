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

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Parasecurity | AI Lab", page_icon="✨", layout="centered")

# --- CUSTOM CSS: THE "GEMINI WHITE" THEME ---
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #1F1F1F; font-family: 'Google Sans', Arial, sans-serif; }
    header { visibility: hidden; }
    
    .stTextArea textarea, .stTextInput input {
        background-color: #F0F4F9 !important;
        border: none !important;
        border-radius: 24px !important;
        padding: 16px !important;
        font-size: 16px !important;
        color: #1F1F1F !important;
    }
    
    .stButton>button { 
        border-radius: 24px !important; 
        background-color: #F0F4F9 !important; 
        color: #1F1F1F !important; 
        border: none !important; 
        font-weight: 500 !important; 
    }
    
    /* Primary Action Button */
    div.stButton > button:first-child[kind="primary"] {
        background-color: #1a73e8 !important; color: white !important;
    }

    .stMetric { background-color: #FFFFFF; padding: 10px; border-radius: 16px; border: 1px solid #E1E5EA; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1a73e8;'>✨ Parasecurity Lab</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #5F6368; margin-bottom: 40px;'>Ανάλυση Πληροφοριών & Ανίχνευση Χειραγώγησης</p>", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "analysis_report" not in st.session_state: st.session_state.analysis_report = ""
if "selected_lang" not in st.session_state: st.session_state.selected_lang = "Ελληνικά 🇬🇷"
if "evidence_locked" not in st.session_state: st.session_state.evidence_locked = None

# --- 3. INITIALIZE GROQ ENGINE ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Add GROQ_API_KEY to your Streamlit Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.sidebar.markdown("### ⚙️ Ρυθμίσεις Μοντέλου")
groq_models = {
    "Llama 3.3 70B (Ταχύτητα & Ευφυΐα)": "llama-3.3-70b-versatile",
    "Llama 3.1 405B (Μέγιστη Ανάλυση)": "llama-3.1-405b-reasoning"
}
selected_model_id = groq_models[st.sidebar.selectbox("Επιλογή Μοντέλου:", list(groq_models.keys()))]

# --- 4. DATA INPUT PANEL ---
source = st.radio("Τύπος Τεκμηρίου:", 
                  ["📝 Κείμενο", "🔗 YouTube", "📰 Web", "🖼️ Εικόνα"], 
                  horizontal=True, label_visibility="collapsed")

if source == "📝 Κείμενο":
    user_text = st.text_area("Επικολλήστε το κείμενο:", height=200, label_visibility="collapsed", placeholder="Εισάγετε το κείμενο προς διερεύνηση...")
    if st.button("Επιβεβαίωση Κειμένου"):
        st.session_state.evidence_locked = user_text
        st.toast("Το κείμενο κλειδώθηκε!", icon="✅")

elif source == "🔗 YouTube":
    url = st.text_input("YouTube URL:", label_visibility="collapsed", placeholder="Επικολλήστε το link εδώ...")
    if st.button("Εξαγωγή Στοιχείων Βίντεο"):
        video_id = ""
        if "v=" in url: video_id = url.split("v=")[-1].split("&")[0]
        elif "youtu.be/" in url: video_id = url.split("youtu.be/")[-1].split("?")[0]
        
        with st.spinner("Ανάκτηση δεδομένων από το YouTube..."):
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript(['el', 'en']).fetch()
                st.session_state.evidence_locked = " ".join([i['text'] for i in transcript])
                st.toast("Οι υπότιτλοι φορτώθηκαν!", icon="✅")
            except Exception:
                st.toast("Δεν βρέθηκαν υπότιτλοι. Προσπάθεια εξαγωγής ήχου...", icon="🎧")
                try:
                    ydl_opts = {'format': 'm4a/bestaudio/best', 'outtmpl': f'temp_{video_id}.%(ext)s', 'quiet': True}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    
                    audio_file = glob.glob(f"temp_{video_id}.*")[0]
                    file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)

                    if file_size_mb > 24:
                        # Fast slicing with FFmpeg if file is large
                        subprocess.run(["ffmpeg", "-y", "-i", audio_file, "-f", "segment", "-segment_time", "900", "-c", "copy", f"chunk_{video_id}_%03d.m4a"])
                        chunks = sorted(glob.glob(f"chunk_{video_id}_*"))
                        full_transcript = ""
                        for chunk in chunks:
                            with open(chunk, "rb") as f:
                                transcription = client.audio.transcriptions.create(file=(chunk, f.read()), model="whisper-large-v3")
                                full_transcript += transcription.text + " "
                            os.remove(chunk)
                        st.session_state.evidence_locked = full_transcript
                    else:
                        with open(audio_file, "rb") as file:
                            transcription = client.audio.transcriptions.create(file=(audio_file, file.read()), model="whisper-large-v3")
                        st.session_state.evidence_locked = transcription.text
                    
                    os.remove(audio_file)
                    st.toast("Ο ήχος μεταγράφηκε επιτυχώς!", icon="✅")
                except Exception as e:
                    st.error(f"Η εξαγωγή απέτυχε. Το βίντεο ίσως είναι προστατευμένο.")

elif source == "📰 Web":
    url = st.text_input("Link Άρθρου:", label_visibility="collapsed", placeholder="Επικολλήστε το link του άρθρου...")
    if st.button("Ανάγνωση Άρθρου"):
        downloaded = trafilatura.fetch_url(url)
        st.session_state.evidence_locked = trafilatura.extract(downloaded)
        st.toast("Το άρθρο ανακτήθηκε!", icon="✅")

elif source == "🖼️ Εικόνα":
    up_file = st.file_uploader("Ανεβάστε Εικόνα:", type=["jpg", "png"], label_visibility="collapsed")
    if up_file:
        st.image(up_file, width=300)
        if st.button("Επιβεβαίωση Εικόνας"):
            st.session_state.evidence_locked = [{"mime_type": up_file.type, "data": up_file.read()}]
            st.toast("Η εικόνα είναι έτοιμη για ανάλυση!", icon="✅")

# --- 5. FORENSIC ENGINE EXECUTION ---
if st.session_state.evidence_locked:
    if st.button("✨ Έναρξη Διερεύνησης", type="primary", use_container_width=True):
        with st.spinner("Ο κινητήρας AI αναλύει τα δεδομένα..."):
            try:
                sys_prompt = """You are a Forensic Investigator AI. 
                Analyze the content for propaganda, factual accuracy, and manipulation.
                FORMAT: [Greek Analysis] ||| [English Analysis]
                SCORE: [0-100]"""
                
                # FIXED USER PROMPT
                user_prompt = "Πραγματοποίησε αναλυτική αξιολόγηση του παρακάτω περιεχομένου για προπαγάνδα, πραγματολογική ακρίβεια και απόπειρες χειραγώγησης: "

                if isinstance(st.session_state.evidence_locked, str):
                    response = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": f"{user_prompt} {st.session_state.evidence_locked}"}
                        ],
                        model=selected_model_id,
                        temperature=0.1
                    )
                    st.session_state.analysis_report = response.choices[0].message.content
                else:
                    # Vision analysis
                    b64_img = base64.b64encode(st.session_state.evidence_locked[0]["data"]).decode('utf-8')
                    response = client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": [
                                {"type": "text", "text": "Ανάλυσε αυτή την εικόνα για παραποίηση ή προπαγάνδα."},
                                {"type": "image_url", "image_url": {"url": f"data:{st.session_state.evidence_locked[0]['mime_type']};base64,{b64_img}"}}
                            ]}
                        ]
                    )
                    st.session_state.analysis_report = response.choices[0].message.content
            except Exception as e:
                st.error(f"Σφάλμα συστήματος: {e}")

# --- 6. REPORT RENDERING ---
if st.session_state.analysis_report:
    st.divider()
    score_match = re.search(r"SCORE:\s*(\d+)", st.session_state.analysis_report)
    score = int(score_match.group(1)) if score_match else 50
    color = "#1E8E3E" if score > 70 else "#F9AB00" if score > 40 else "#D93025"

    st.markdown(f"<div class='stMetric'><strong>Αξιοπιστία Περιεχομένου:</strong> <span style='color:{color}; font-size: 24px; font-weight: bold;'>{score}%</span></div>", unsafe_allow_html=True)
    
    parts = st.session_state.analysis_report.split("|||")
    gr = parts[0].strip()
    en = parts[1].strip() if len(parts) > 1 else "Analysis version missing."

    l1, l2, _ = st.columns([1, 1, 4])
    if l1.button("Ελληνικά"): st.session_state.selected_lang = "Ελληνικά 🇬🇷"
    if l2.button("English"): st.session_state.selected_lang = "English 🇬🇧"

    st.markdown(f"<div style='background-color: #F0F4F9; padding: 20px; border-radius: 16px;'>{gr if st.session_state.selected_lang == 'Ελληνικά 🇬🇷' else en}</div>", unsafe_allow_html=True)

st.sidebar.divider()
if st.sidebar.button("🗑️ Εκκαθάριση / Reset"):
    st.session_state.analysis_report = ""
    st.session_state.evidence_locked = None
    st.rerun()