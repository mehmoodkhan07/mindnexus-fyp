import streamlit as st
import os
import shutil
from auth.auth import login, logout
from utils.voice import speak, listen
from utils.pdf_processor import process_pdf
from utils.history import load_history, save_message

# Updated imports for Cloud Deployment
from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA

# ---------- CONFIG & THEME ----------
st.set_page_config(
    page_title="MindNexus",
    page_icon="🧠",
    layout="wide"
)

# Initialize speaking state
if "speaking" not in st.session_state:
    st.session_state.speaking = False

# Enhanced CSS for Pulse Effect & Modern UI
st.markdown("""
    <style>
    .stChatFloatingInputContainer {padding-bottom: 20px;}
    .stChatMessage {border-radius: 15px; margin-bottom: 10px;}
    
    /* Pulse Waveform Animation */
    .voice-wave {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 5px;
        height: 30px;
        margin: 10px 0;
    }
    .bar {
        width: 4px;
        height: 10px;
        background: #2e7bcf;
        border-radius: 10px;
        animation: pulse 1s ease-in-out infinite;
    }
    .bar:nth-child(2) { animation-delay: 0.1s; }
    .bar:nth-child(3) { animation-delay: 0.2s; }
    .bar:nth-child(4) { animation-delay: 0.3s; }
    .bar:nth-child(5) { animation-delay: 0.4s; }

    @keyframes pulse {
        0%, 100% { height: 10px; }
        50% { height: 30px; }
    }
    
    div.stButton > button:first-child {
        border-radius: 20px;
        padding: 0.5rem 1rem;
    }
    </style>
""", unsafe_allow_html=True)

BASE_DB = "data/libraries"
UPLOAD_DIR = "temp_uploads"

os.makedirs(BASE_DB, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- SESSION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

# ---------- SIDEBAR / LOGOUT ----------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=100)
    st.title("MindNexus")
    st.write(f"Logged in as: **{st.session_state.username}**")
    if st.button("🔓 Logout", use_container_width=True):
        logout()
    st.divider()

# ---------- LOAD CHAT HISTORY ----------
if "messages" not in st.session_state:
    st.session_state.messages = load_history(st.session_state.username)

# ---------- UI HEADER ----------
st.title("🧠 MindNexus – Knowledge Brain")

# Visual Waveform shown only when AI is speaking
if st.session_state.speaking:
    st.markdown("""
        <div class="voice-wave">
            <div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div>
            <span style="color: #2e7bcf; font-weight: bold; margin-left: 10px;">AI is speaking...</span>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---------- ADMIN PANEL ----------
if st.session_state.role == "admin":
    with st.sidebar.expander("📤 Upload New Document", expanded=False):
        uploaded_file = st.file_uploader("Choose PDF", type="pdf")
        if uploaded_file and st.button("Process Document", use_container_width=True):
            doc_name = uploaded_file.name.replace(".pdf", "").replace(" ", "_")
            save_dir = f"{BASE_DB}/{doc_name}"
            file_path = f"{UPLOAD_DIR}/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            with st.spinner("Analyzing PDF..."):
                process_pdf(file_path, save_dir)
            st.success(f"Added: {doc_name}")
            st.rerun()

# ---------- DOCUMENT SELECTION ----------
docs = os.listdir(BASE_DB)
selected_doc = st.sidebar.selectbox("📚 Select Knowledge Base", ["Select a Library"] + docs)

if st.session_state.role == "admin" and selected_doc != "Select a Library":
    if st.sidebar.button("🗑 Delete Selected Base", type="primary", use_container_width=True):
        shutil.rmtree(f"{BASE_DB}/{selected_doc}")
        st.rerun()

# ---------- DISPLAY CHAT HISTORY ----------
for i, msg in enumerate(st.session_state.messages):
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            label = "🛑 Stop" if st.session_state.speaking else "🔊 Listen"
            if st.button(label, key=f"btn_{i}"):
                speak(msg["content"])
                st.rerun()

# ---------- CHAT LOGIC ----------
if selected_doc != "Select a Library":
    # Vector Database setup
    vector_db = Chroma(
        persist_directory=f"{BASE_DB}/{selected_doc}",
        embedding_function=OllamaEmbeddings(model="nomic-embed-text")
    )

    input_col, mic_col = st.columns([0.9, 0.1])
    
    with input_col:
        user_input = st.chat_input("Ask about your documents...")
    with mic_col:
        if st.button("🎤", help="Voice Input"):
            with st.spinner("Listening..."):
                user_input = listen()

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        save_message(st.session_state.username, "user", user_input)
        with st.chat_message("user", avatar="👤"):
            st.write(user_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Synthesizing answer..."):
                # CLOUD LLM CONFIGURATION (Groq)
                llm = ChatGroq(
                    temperature=0.3,
                    groq_api_key=st.secrets["GROQ_API_KEY"],
                    model_name="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"
                )
                
                qa = RetrievalQA.from_chain_type(
                    llm=llm,
                    retriever=vector_db.as_retriever(search_kwargs={"k": 3}),
                    return_source_documents=False
                )
                
                response = qa.invoke({"query": user_input})
                answer = response["result"]
                st.write(answer)
                
                if st.button("🔊 Listen / 🛑 Stop", key="btn_new"):
                    speak(answer)
                    st.rerun()

        st.session_state.messages.append({"role": "assistant", "content": answer})
        save_message(st.session_state.username, "assistant", answer)
else:
    st.info("💡 Please select a document library from the sidebar to begin your research.")