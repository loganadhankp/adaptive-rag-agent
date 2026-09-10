import streamlit as st

from frontend.api_client import RAGApiClient
from frontend.components.analytics_dashboard import render_analytics_dashboard
from frontend.components.chat_window import render_chat_window
from frontend.components.kb_manager import render_kb_manager
from frontend.components.settings_page import render_settings_page
from frontend.components.sidebar import render_sidebar
from frontend.styles import CUSTOM_CSS

import textwrap

# Page config
st.set_page_config(
    page_title="Knowledge Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

# Top Navigation Bar (Header)
st.markdown(
    textwrap.dedent("""
    <div class="top-header">
        <div class="top-header-title">
            <span style="font-size: 24px;">📚</span>
            Knowledge Assistant
        </div>
        <div class="top-header-subtitle">
            Ask questions about your documents. If the answer isn't in your knowledge base, I'll search the web.
        </div>
    </div>
    """).strip(),
    unsafe_allow_html=True,
)


# Initialize session state
def init_session_state():
    defaults = {
        "conversations": [],
        "active_conversation_id": None,
        "messages": {},  # {conversation_id: [messages]}
        "current_page": "chat",
        "settings": {
            "provider": "gemini",
            "model": "gemini-3.5-flash-lite",
            "temperature": 0.7,
            "answer_quality_threshold": 80,
            "max_retries": 2,
            "max_retrieval_results": 4,
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Auto-upgrade any stale session state model
    if st.session_state.settings.get("model") in ["gemini-2.5-flash", "gemini-2.5-flash-lite"]:
        st.session_state.settings["model"] = "gemini-3.5-flash-lite"


init_session_state()

# Initialize API client and expose to session state for components
api_client = RAGApiClient()
if "api_client" not in st.session_state:
    st.session_state["api_client"] = api_client

# Check backend health
if not api_client.health_check():
    st.error(
        "⚠️ Cannot connect to backend. Please ensure FastAPI is running on http://localhost:8000"
    )
    st.stop()

# Load conversations from API on first run
if not st.session_state.conversations:
    try:
        convs = st.session_state.api_client.get_conversations()
        st.session_state.conversations = convs
    except Exception:
        st.session_state.conversations = []

# If no conversations exist, create a fresh single "New Chat"
if not st.session_state.conversations:
    try:
        new_conv = st.session_state.api_client.create_conversation("New Chat")
        if new_conv and new_conv.get("id"):
            st.session_state.conversations = [new_conv]
            st.session_state.active_conversation_id = new_conv["id"]
    except Exception:
        pass

# Ensure active conversation ID is valid
valid_ids = [c["id"] for c in st.session_state.conversations]
if st.session_state.active_conversation_id not in valid_ids and valid_ids:
    st.session_state.active_conversation_id = valid_ids[0]

# Sync messages for active conversation if not loaded
active_id = st.session_state.active_conversation_id
if active_id and active_id not in st.session_state.messages:
    try:
        st.session_state.messages[active_id] = st.session_state.api_client.get_messages(
            active_id
        )
    except Exception:
        st.session_state.messages[active_id] = []

# Render sidebar and get current page
current_page = render_sidebar()

# Page routing
if current_page == "chat":
    render_chat_window(api_client, st.session_state.settings)
elif current_page == "kb":
    render_kb_manager(api_client)
elif current_page == "analytics":
    render_analytics_dashboard(api_client)
elif current_page == "settings":
    render_settings_page()
