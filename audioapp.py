import streamlit as st
from PyPDF2 import PdfReader
from gtts import gTTS
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import io
import pyttsx3   # offline TTS

# ----------------- FUNCTIONS -----------------
def pdf_to_text(pdf_file, pages):
    """Extracts text from a PDF file, with OCR fallback."""
    text = ""

    pdf_file.seek(0)
    file_bytes = pdf_file.read()

    try:
        # Use PyPDF2 to extract text
        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        num_pages = len(pdf_reader.pages)

        first_page, last_page = (0, num_pages)
        if pages:
            first_page = max(0, pages[0])
            last_page = min(num_pages, pages[1])

        for i in range(first_page, last_page):
            page = pdf_reader.pages[i]
            text += page.extract_text() or ""

    except Exception as e:
        st.warning(f"PyPDF2 failed: {e}. Falling back to OCR.")
        text = ""

    # OCR fallback for scanned PDFs
    if not text.strip():
        st.info("No text found with standard methods. Attempting OCR...")
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for i in range(doc.page_count):
                if pages and not (pages[0] <= i < pages[1]):
                    continue
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                ocr_text = pytesseract.image_to_string(img)
                text += ocr_text + "\n"
            doc.close()
        except Exception as ocr_error:
            st.error(f"OCR processing failed: {ocr_error}")
            return ""

    return text


def text_to_audio_gtts(text, lang='en'):
    """Converts text to audio using gTTS (online)."""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp
    except Exception as e:
        st.error(f"Failed to generate audio (gTTS): {e}")
        return None


def text_to_audio_pyttsx3(text):
    """Converts text to audio using pyttsx3 (offline)."""
    try:
        audio_fp = io.BytesIO()
        engine = pyttsx3.init()
        engine.save_to_file(text, "output_offline.mp3")  # saves to file
        engine.runAndWait()
        # Read file back into memory
        with open("output_offline.mp3", "rb") as f:
            audio_fp.write(f.read())
        audio_fp.seek(0)
        return audio_fp
    except Exception as e:
        st.error(f"Failed to generate audio (pyttsx3): {e}")
        return None


# ----------------- STREAMLIT UI -----------------
st.set_page_config(page_title="PDF to Audio", layout="wide")

# Custom CSS with animations
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        html, body, [class*="st-"] {
            font-family: 'Poppins', sans-serif;
            background-color: #0f121a;
            color: #e0e6f0;
        }
        .main .block-container { max-width: 1000px; padding-top: 3rem; padding-bottom: 3rem; }
        header {visibility: hidden;} footer {visibility: hidden;} #MainMenu {visibility: hidden;}
        h1, h2, h3, h4, h5, h6 { color: #ffffff; font-weight: 600; animation: fadeIn 1.2s ease-in-out; }
        h1 { border-bottom: 2px solid #5778a8; padding-bottom: 10px; }
        .stButton>button { background-color: #2e3542; color: #ffffff; border: none; 
            padding: 12px 28px; border-radius: 10px; width: 100%; font-weight: 600; 
            transition: transform 0.2s, background-color 0.2s; animation: popIn 0.8s ease; }
        .stButton>button:hover { background-color: #3f4756; transform: translateY(-2px) scale(1.02); }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stRadio label {
            background-color: #1a1e26; color: #e0e6f0; border: 1px solid #3a475a;
            border-radius: 8px; padding: 10px; transition: box-shadow 0.2s;
        }
        .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox div[data-baseweb="select"]:focus {
            box-shadow: 0 0 10px #00b4d8;
        }
        .stTextArea textarea { min-height: 300px; }
        .stAudio { width: 100%; margin-top: 20px; animation: fadeInUp 1s ease-in-out; }
        .stAudio audio { width: 100%; border-radius: 10px; background-color: #1a1e26; }
        .team-title { text-align: center; font-size: 2rem; color: #00b4d8; font-weight: 700; margin-bottom: 1rem; animation: slideIn 1s ease-in-out; }

        /* Animations */
        @keyframes fadeIn {
            from {opacity: 0;} to {opacity: 1;}
        }
        @keyframes fadeInUp {
            from {opacity: 0; transform: translateY(20px);} to {opacity: 1; transform: translateY(0);}
        }
        @keyframes popIn {
            from {opacity: 0; transform: scale(0.9);} to {opacity: 1; transform: scale(1);}
        }
        @keyframes slideIn {
            from {opacity: 0; transform: translateX(-50px);} to {opacity: 1; transform: translateX(0);}
        }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("logocode.png", width=180)
    st.markdown("## 📖 *PDF to Audio Converter*")
    st.markdown("Easily transform your documents into an immersive listening experience. 🎧")
    st.markdown("---")
    pdf_file = st.file_uploader("Upload your PDF", type=["pdf"])
    page_input = st.text_input("Page Range", placeholder="e.g., 1-5 or 3")

    # Language selection (for gTTS only)
    languages = {
        "English": "en",
        "Hindi (हिंदी)": "hi",
        "Telugu (తెలుగు)": "te",
        "French (Français)": "fr",
        "German (Deutsch)": "de",
        "Spanish (Español)": "es",
        "Tamil (தமிழ்)": "ta",
        "Arabic (العربية)": "ar",
        "Chinese (中文)": "zh-CN",
        "Japanese (日本語)": "ja"
    }
    lang_choice = st.selectbox("Select Language (for gTTS)", list(languages.keys()))
    lang_code = languages[lang_choice]

    # Choose TTS engine
    engine_choice = st.radio("Choose TTS Engine:", ["Google gTTS (Online)", "pyttsx3 (Offline)"])

    st.markdown("---")
    convert_button = st.button("Convert to Audio 🚀")

# --- Main Area ---
st.markdown('<div class="team-title">🚀 Team SquadCodez</div>', unsafe_allow_html=True)
st.title("📚 PDF to Audio")
st.markdown("Upload a PDF, choose your language and TTS engine, then click 'Convert' to generate an audio version of your document.")

if convert_button and pdf_file:
    try:
        pages = None
        if page_input:
            if "-" in page_input:
                first, last = map(int, page_input.split("-"))
                pages = (first - 1, last)
            else:
                page_num = int(page_input)
                pages = (page_num - 1, page_num)

        with st.spinner("Extracting text from PDF..."):
            extracted_text = pdf_to_text(pdf_file, pages)

        if not extracted_text.strip():
            st.error("No text could be found. The PDF may be empty or encrypted.")
        else:
            st.success("Text extracted successfully! ✅")

            with st.expander("📜 View Extracted Text"):
                st.text_area("Extracted Text", extracted_text, height=250)

            with st.spinner("Generating audio... This may take a moment."):
                if engine_choice == "Google gTTS (Online)":
                    audio_file = text_to_audio_gtts(extracted_text, lang=lang_code)
                else:
                    audio_file = text_to_audio_pyttsx3(extracted_text)

            if audio_file:
                st.success(f"Audio conversion complete using {engine_choice}! 🎉")
                st.audio(audio_file, format="audio/mp3")

                st.download_button(
                    label="💾 Download Audio",
                    data=audio_file,
                    file_name=f"output_{lang_code}.mp3",
                    mime="audio/mp3"
                )
            else:
                st.error("Audio generation failed. Please try again.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
elif convert_button:
    st.warning("⚠ Please upload a PDF file to begin.")
