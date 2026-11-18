import uuid
import streamlit as st

from frontend.api_client import RAGApiClient
from frontend.components.chat_window import render_chat_window
from frontend.styles import CUSTOM_CSS

st.set_page_config(
    page_title="RAG Agent",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

def init_session_state():
    if "session_initialized" not in st.session_state:
        st.session_state.session_initialized = True
        fresh_id = str(uuid.uuid4())
        st.session_state.active_conversation_id = fresh_id
        st.session_state.messages = {fresh_id: []}
        st.session_state.conversations = []
        st.session_state.settings = {
            "provider": "gemini",
            "model": "gemini-3.5-flash-lite",
            "temperature": 0.0,
        }

init_session_state()

api_client = RAGApiClient()
if "api_client" not in st.session_state:
    st.session_state["api_client"] = api_client

render_chat_window(api_client, st.session_state.settings)
