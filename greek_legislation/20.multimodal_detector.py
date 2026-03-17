import streamlit as st
import os
import glob
import re
import trafilatura
import base64
import yt_dlp
from pydub import AudioSegment  # NEW: The audio slicer
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
        box-shadow: none !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus { outline: 2px solid #1a73e8 !important; }
    
    .stButton>button { 
        border-radius: 24px !important; 
        height: 3em !important; 
        background-color: #F0F4F9 !important; 
        color: #1F1F1F !important; 
        border: none !important; 
        font-weight: 500 !important; 
        transition: all 0.2s ease;
    }
    .stButton>button:hover { background-color: #E1E5EA !important; color: #1a73e8 !important; }
    
    div:nth-child(5) > div > button {
        background-color: #1a73e8 !important; color: white !important; font-weight: bold !important;
    }
    div:nth-child(5) > div > button:hover { background-color: #1557b0 !important; color: white !important; }

    .stMetric { background-color: #FFFFFF; padding: 10px; border-radius: 16px; border: 1px solid #E1E5EA; }
    hr { border-color: #F0F4F9; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #1a73e8;'>✨ Parasecurity Lab</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #5F6368; margin-bottom: 40px;'>How can I help you investigate today?</p>", unsafe_allow_html=True)

# --- 2. SESSION STATE ---
if "analysis_report" not in st.session_state: st.session_state.analysis_report = ""
if "selected_lang" not in st.session_state: st.session_state.selected_lang = "Ελληνικά 🇬🇷"
if "evidence_locked" not in st.session_state: st.session_state.evidence_locked = None

# --- 3. INITIALIZE GROQ ENGINE ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Add GROQ_API_KEY to your Streamlit Secrets.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.sidebar.markdown("### ⚙️ Engine Settings")
groq_models = {
    "Llama 3.3 70B (Fast & Smart)": "llama-3.3-70b-versatile",
    "GPT-OSS 120B (Heavy Reasoning)": "openai/gpt-oss-120b",
    "Qwen 3 32B (Great for Code/Logic)": "qwen/qwen3-32b"
}
selected_model_label = st.sidebar.selectbox("Select Text Model:", list(groq_models.keys()))
selected_model_id = groq_models[selected_model_label]


# --- 4. DATA INPUT PANEL ---
source = st.radio("Evidence Type:", 
                  ["📝 Text", "🔗 YouTube", "📰 Web", "🖼️ Media"], 
                  horizontal=True, label_visibility="collapsed")

if source == "📝 Text":
    user_text = st.text_area("Paste text or claims:", height=200, label_visibility="collapsed", placeholder="Enter text to investigate here...")
    if st.button("Confirm Text"):
        st.session_state.evidence_locked = user_text
        st.toast("Text confirmed! Ready to analyze.", icon="✅")

elif source == "🔗 YouTube":
    url = st.text_input("YouTube URL:", label_visibility="collapsed", placeholder="Paste YouTube Link here...")
    if st.button("Extract Video Evidence"):
        
        if "youtube.com" not in url and "youtu.be" not in url and "shorts/" not in url:
            st.error("⚠️ That doesn't look like a valid YouTube URL.")
        else:
            video_id = ""
            if "v=" in url: video_id = url.split("v=")[-1].split("&")[0]
            elif "youtu.be/" in url: video_id = url.split("youtu.be/")[-1].split("?")[0]
            elif "shorts/" in url: video_id = url.split("shorts/")[-1].split("?")[0]
            else: video_id = url.split("/")[-1]
            
            with st.spinner("Extracting evidence from YouTube..."):
                try:
                    # 1. Try fetching existing subtitles first (Fast)
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                    try:
                        transcript_info = transcript_list.find_transcript(['el', 'en'])
                    except:
                        transcript_info = next(iter(transcript_list))
                    transcript = transcript_info.fetch()
                    st.session_state.evidence_locked = " ".join([i['text'] for i in transcript])
                    st.toast("Subtitles found and loaded!", icon="✅")
                    
                except Exception:
                    # 2. Fallback: Download audio and chunk if necessary
                    st.toast("No subtitles found. Downloading audio track...", icon="🎧")
                    try:
                        ydl_opts = {
                            'format': 'worstaudio[ext=m4a]/m4a/bestaudio/best', # Keep it small
                            'outtmpl': f'temp_audio_{video_id}.%(ext)s',
                            'quiet': True,
                            'extractor_args': {'youtube': {'player_client': ['ios', 'android', 'web']}},
                            'nocheckcertificate': True,
                            'ignoreerrors': True,
                            'no_warnings': True,
                        }
                        
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            ydl.extract_info(url, download=True)
                            
                        downloaded_files = glob.glob(f"temp_audio_{video_id}.*")
                        
                        if not downloaded_files:
                            st.error("⚠️ YouTube blocked the extraction or video is private.")
                        else:
                            audio_file = downloaded_files[0]
                            file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
                            
                            # CHUNKING LOGIC: If file is over 24MB, split it up
                            if file_size_mb > 24:
                                st.toast(f"File is {file_size_mb:.1f}MB. Chopping into smaller parts...", icon="✂️")
                                audio = AudioSegment.from_file(audio_file)
                                
                                # Split into 15-minute chunks (15 * 60 * 1000 milliseconds)
                                chunk_length_ms = 15 * 60 * 1000 
                                chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
                                
                                full_transcript = ""
                                progress_bar = st.progress(0)
                                
                                for i, chunk in enumerate(chunks):
                                    chunk_name = f"chunk_{i}.mp3"
                                    chunk.export(chunk_name, format="mp3") # Export as small mp3
                                    
                                    with open(chunk_name, "rb") as f:
                                        transcription = client.audio.transcriptions.create(
                                            file=(chunk_name, f.read()),
                                            model="whisper-large-v3"
                                        )
                                    full_transcript += transcription.text + " "
                                    os.remove(chunk_name) # Clean up the chunk
                                    
                                    # Update user on progress
                                    progress_bar.progress((i + 1) / len(chunks))
                                
                                st.session_state.evidence_locked = full_transcript
                                st.toast("All parts transcribed and merged!", icon="✅")
                                
                            else:
                                # Normal single-file processing
                                st.toast("Transcribing audio with Whisper AI...", icon="🧠")
                                with open(audio_file, "rb") as file:
                                    transcription = client.audio.transcriptions.create(
                                        file=(audio_file, file.read()),
                                        model="whisper-large-v3"
                                    )
                                st.session_state.evidence_locked = transcription.text
                                st.toast("Audio transcribed by Groq! Ready to analyze.", icon="✅")
                            
                            # Clean up the original file
                            if os.path.exists(audio_file):
                                os.remove(audio_file)
                                
                    except Exception as e:
                        st.error(f"Deep extraction failed: {e}. Check if the video is private or blocked.")

elif source == "📰 Web":
    url = st.text_input("Article Link:", label_visibility="collapsed", placeholder="Paste Article URL here...")
    if st.button("Scrape Article"):
        try:
            downloaded = trafilatura.fetch_url(url)
            st.session_state.evidence_locked = trafilatura.extract(downloaded)
            st.toast("Article scraped successfully!", icon="✅")
        except: st.error("Scraping failed.")

elif source == "🖼️ Media":
    up_file = st.file_uploader("Upload Image:", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    if up_file:
        st.image(up_file, width=300)
        if st.button("Confirm Image"):
            bytes_data = up_file.read()
            st.session_state.evidence_locked = [
                {"mime_type": up_file.type, "data": bytes_data},
                "Analyze this image. Format EXACTLY as: [Greek] ||| [English]. End with SCORE: XX"
            ]
            st.toast("Image ready for Groq Vision analysis!", icon="✅")

# --- 5. FORENSIC ENGINE EXECUTION ---
st.write("") 

if st.session_state.evidence_locked:
    if st.button("✨ Investigate Evidence", use_container_width=True):
        with st.spinner("Engine is thinking..."):
            try:
                payload = st.session_state.evidence_locked
                
                # STRICT SYSTEM PROMPT
                sys_prompt = """You are a Forensic Investigator AI. Today is March 17, 2026.
                You MUST format your final output EXACTLY like this with no exceptions:
                [Your full analysis in Greek here]
                |||
                [Your full analysis in English here]
                
                SCORE: [Provide a number from 0 to 100 representing credibility]"""
                
                # TEXT PROCESSING
                if isinstance(payload, str):
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": f"Analyze this text for propaganda, factual accuracy, and manipulation: {payload}"}
                        ],
                        model=selected_model_id,
                        temperature=0.2
                    )
                    st.session_state.analysis_report = chat_completion.choices[0].message.content
                
                # IMAGE PROCESSING
                else:
                    mime_type = payload[0]["mime_type"]
                    base64_image = base64.b64encode(payload[0]["data"]).decode('utf-8')
                    prompt_text = payload[1]
                    
                    chat_completion = client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt_text},
                                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
                                ]
                            }
                        ],
                        temperature=0.2
                    )
                    st.session_state.analysis_report = chat_completion.choices[0].message.content
                    
            except Exception as e:
                st.error(f"Engine Error: {e}")
else:
    st.markdown("<p style='text-align: center; color: #9AA0A6; font-size: 14px;'>Waiting for evidence...</p>", unsafe_allow_html=True)

# --- 6. REPORT RENDERING ---
if st.session_state.analysis_report:
    st.divider()
    score_match = re.search(r"SCORE:\s*(\d+)", st.session_state.analysis_report)
    score = int(score_match.group(1)) if score_match else 50
    color = "#1E8E3E" if score > 70 else "#F9AB00" if score > 40 else "#D93025"

    st.markdown(f"<div class='stMetric'><strong>Credibility Score:</strong> <span style='color:{color}; font-size: 24px; font-weight: bold;'>{score}%</span></div>", unsafe_allow_html=True)
    st.write("")

    parts = st.session_state.analysis_report.split("|||")
    gr = parts[0].strip()
    en = parts[1].strip() if len(parts) > 1 else "Formatting error from AI: English version dropped."

    l1, l2, _ = st.columns([1, 1, 4])
    if l1.button("Ελληνικά"): st.session_state.selected_lang = "Ελληνικά 🇬🇷"
    if l2.button("English"): st.session_state.selected_lang = "English 🇬🇧"

    st.markdown(f"<div style='background-color: #F0F4F9; padding: 20px; border-radius: 16px;'>{gr if st.session_state.selected_lang == 'Ελληνικά 🇬🇷' else en}</div>", unsafe_allow_html=True)

# Sidebar utilities
st.sidebar.divider()
if st.sidebar.button("🗑️ Clear Chat / Reset"):
    st.session_state.analysis_report = ""
    st.session_state.evidence_locked = None
    st.rerun()
st.sidebar.caption("© 2026 Parasecurity Labs")