import uuid
import streamlit as st

from frontend.api_client import RAGApiClient
from frontend.components.chat_window import render_chat_window
from frontend.styles import CUSTOM_CSS
from frontend.testing_utils import add_testid

st.set_page_config(
    page_title="Adaptive RAG Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
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

with st.sidebar:
    add_testid("sidebar")

    st.markdown(
        """
        <div class="sidebar-section-title">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#0f172a" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <span>Upload Documents</span>
        </div>
        <div class="sidebar-section-subtitle">Supports PDF, DOCX and TXT files</div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        key="sidebar_file_uploader",
        label_visibility="collapsed",
    )

    add_testid("kb-upload-button", visible=False)
    if uploaded_files:
        if st.button("Upload to Knowledge Base", key="btn_upload_docs", use_container_width=True):
            with st.spinner("Indexing documents..."):
                active_id = st.session_state.get("active_conversation_id")
                for doc in uploaded_files:
                    api_client.upload_document(
                        doc.name, doc.getvalue(), doc.type, conversation_id=active_id
                    )
            st.toast(f"✓ Uploaded {len(uploaded_files)} document(s)")
            st.rerun()

    st.markdown(
        """
        <div class="sidebar-section-title" style="margin-top: 18px;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10" fill="#10b981"/>
                <path d="m9 12 2 2 4-4" stroke="#ffffff"/>
            </svg>
            <span>Uploaded Files</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    kb_docs = api_client.list_documents()
    if kb_docs:
        for doc in kb_docs:
            doc_id = doc.get("id")
            filename = doc.get("filename", "document")
            ext = filename.split(".")[-1].lower() if "." in filename else "txt"
            badge_class = f"badge-{ext}" if ext in ["pdf", "docx", "txt", "md"] else "badge-txt"

            col_doc, col_del = st.columns([0.85, 0.15])
            with col_doc:
                st.markdown(
                    f"""
                    <div class="uploaded-file-row">
                        <div class="file-info-group">
                            <span class="doc-type-badge {badge_class}">{ext.upper()}</span>
                            <span class="doc-file-name" title="{filename}">{filename}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_del:
                if st.button("✕", key=f"del_doc_{doc_id}", help="Delete document"):
                    api_client.delete_document(doc_id)
                    st.toast(f"Deleted {filename}")
                    st.rerun()
    else:
        st.markdown(
            '<div style="font-size: 12px; color: #94a3b8; padding: 4px 0 10px 4px;">No files uploaded yet</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="sidebar-section-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0f172a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>Chat History</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    add_testid("new-chat-button", visible=False)
    if st.button("➕ New Chat", key="btn_sidebar_new_chat", use_container_width=True):
        fresh_id = str(uuid.uuid4())
        created = api_client.create_conversation("New Chat")
        if created and "id" in created:
            fresh_id = created["id"]
        st.session_state.active_conversation_id = fresh_id
        if fresh_id not in st.session_state.messages:
            st.session_state.messages[fresh_id] = []
        st.rerun()

    conversations = api_client.get_conversations()
    active_conv_id = st.session_state.get("active_conversation_id")

    if conversations:
        for conv in conversations:
            c_id = conv.get("id")
            c_title = conv.get("title") or "New Chat"
            if len(c_title) > 24:
                c_title = c_title[:24] + "..."

            is_active = c_id == active_conv_id
            btn_label = f"💬  {c_title}" if not is_active else f"👉  {c_title}"

            col_c, col_d = st.columns([0.85, 0.15])
            with col_c:
                if st.button(btn_label, key=f"conv_{c_id}", use_container_width=True):
                    st.session_state.active_conversation_id = c_id
                    if c_id not in st.session_state.messages or not st.session_state.messages[c_id]:
                        history_msgs = api_client.get_messages(c_id)
                        loaded_msgs = []
                        for hm in history_msgs:
                            loaded_msgs.append({
                                "role": hm.get("role", "user"),
                                "content": hm.get("content", ""),
                                "sources": hm.get("sources", []),
                                "metadata": hm.get("workflow_metadata", {}),
                            })
                        st.session_state.messages[c_id] = loaded_msgs
                    st.rerun()
            with col_d:
                if st.button("✕", key=f"del_conv_{c_id}", help="Delete chat"):
                    api_client.delete_conversation(c_id)
                    if c_id in st.session_state.messages:
                        del st.session_state.messages[c_id]
                    if c_id == active_conv_id:
                        fresh_id = str(uuid.uuid4())
                        st.session_state.active_conversation_id = fresh_id
                        st.session_state.messages[fresh_id] = []
                    st.rerun()
    else:
        st.markdown(
            '<div style="font-size: 12px; color: #94a3b8; padding: 4px 0 10px 4px;">No chats yet</div>',
            unsafe_allow_html=True,
        )

render_chat_window(api_client, st.session_state.settings)
