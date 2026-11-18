import html
import uuid
import streamlit as st
from frontend.testing_utils import add_testid

def get_sufficiency_badge_html(metadata: dict) -> str:
    """Returns empty string - suppresses diagnostic badge headers for clean ChatGPT-style interface."""
    return ""

def render_sufficiency_badge(metadata: dict):
    """Renders colored evidence sufficiency badge into the current container."""
    badge_html = get_sufficiency_badge_html(metadata)
    if badge_html:
        st.markdown(badge_html, unsafe_allow_html=True)

def render_chat_window(api_client, settings):
    """Minimal ChatGPT/Gemini style chat interface."""
    add_testid("chat-window")

    active_id = st.session_state.get("active_conversation_id")
    if not active_id:
        active_id = str(uuid.uuid4())
        st.session_state.active_conversation_id = active_id

    if active_id not in st.session_state.messages:
        st.session_state.messages[active_id] = []

    messages = st.session_state.messages.get(active_id, [])

    chat_container = st.container()

    with chat_container:
        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            msg_meta = msg.get("metadata") or msg.get("workflow_metadata") or {}

            if role == "user":
                st.markdown(
                    f'<div class="user-msg-row"><div class="user-msg-bubble">{html.escape(content)}</div></div>'
                    f'<div data-testid="user-message" data-msg-idx="{i}" style="display:none"></div>',
                    unsafe_allow_html=True,
                )
            else:
                if msg_meta:
                    render_sufficiency_badge(msg_meta)
                st.markdown(
                    f'<div class="bot-msg-row"><div class="bot-msg-body">\n\n{content}\n\n</div></div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div data-testid="assistant-message" data-msg-idx="{i}" style="display:none"></div>',
                    unsafe_allow_html=True,
                )

    st.markdown('<div class="fixed-bottom-left-upload">', unsafe_allow_html=True)
    with st.popover("📎 Upload Document", help="Upload document to Knowledge Base"):
        add_testid("kb-upload-button", visible=False)
        uploaded_files = st.file_uploader(
            "Select files",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            key="fixed_kb_uploader",
            label_visibility="collapsed",
        )
        if uploaded_files:
            if st.button("Upload to Knowledge Base", key="btn_upload_fixed_docs", use_container_width=True):
                with st.spinner("Indexing documents..."):
                    for doc in uploaded_files:
                        api_client.upload_document(
                            doc.name, doc.getvalue(), doc.type, conversation_id=active_id
                        )
                st.toast(f"✓ Uploaded {len(uploaded_files)} document(s)")
    st.markdown('</div>', unsafe_allow_html=True)

    add_testid("chat-input")
    user_input = st.chat_input(
        "Message...",
        accept_file="multiple",
        file_type=["pdf", "docx", "txt", "md"],
    )

    if user_input:
        attached_files = getattr(user_input, "files", []) or []
        for af in attached_files:
            try:
                api_client.upload_document(af.name, af.getvalue(), af.type, conversation_id=active_id)
                st.toast(f"✓ Uploaded {af.name}")
            except Exception:
                pass

        prompt_text = getattr(user_input, "text", None) or str(user_input)
        prompt_text = prompt_text.strip() if isinstance(prompt_text, str) else ""

        if prompt_text:
            messages.append({"role": "user", "content": prompt_text})
            st.session_state.messages[active_id] = messages

            with chat_container:
                st.markdown(
                    f'<div class="user-msg-row"><div class="user-msg-bubble">{html.escape(prompt_text)}</div></div>',
                    unsafe_allow_html=True,
                )

                add_testid("typing-indicator", visible=False)
                status_placeholder = st.empty()
                badge_placeholder = st.empty()
                message_placeholder = st.empty()

                full_response = ""
                sources = []
                metadata = {}

                status_texts = {
                    "classify_intent": "Thinking...",
                    "retrieve": "Retrieving Context...",
                    "retrieve_documents": "Retrieving Context...",
                    "check_sufficiency": "Checking Sufficiency...",
                    "grade": "Checking Sufficiency...",
                    "grade_documents": "Checking Sufficiency...",
                    "general_chat": "Thinking...",
                    "rewrite_query": "Refining Query...",
                    "web_search": "Searching the Web...",
                    "generate": "Generating Answer...",
                    "generate_answer": "Generating Answer...",
                    "evidence_insufficient": "Evidence Insufficient",
                    "insufficient_evidence": "Evidence Insufficient",
                }

                status_placeholder.markdown(
                    '<div class="dynamic-status-pill"><span class="status-dot"></span><span>Thinking...</span></div>',
                    unsafe_allow_html=True,
                )

                for event, data in api_client.stream_chat(
                    message=prompt_text,
                    conversation_id=active_id,
                    model=settings.get("model"),
                    temperature=settings.get("temperature", 0.0),
                    provider=settings.get("provider", "gemini"),
                ):
                    try:
                        if event == "status":
                            step_data = data.get("step", {}) if isinstance(data, dict) else {}
                            raw_step = step_data.get("step") or data.get("step", "processing")
                            status_label = (
                                step_data.get("label")
                                or status_texts.get(raw_step)
                                or "Processing..."
                            )
                            status_placeholder.markdown(
                                f'<div class="dynamic-status-pill"><span class="status-dot"></span><span>{status_label}</span></div>',
                                unsafe_allow_html=True,
                            )
                        elif event == "token":
                            token_text = data.get("token") or data.get("text") or data.get("content") or ""
                            full_response += token_text
                            status_placeholder.empty()
                            message_placeholder.markdown(
                                f'<div class="bot-msg-row"><div class="bot-msg-body">\n\n{full_response}\n\n</div></div>',
                                unsafe_allow_html=True,
                            )
                        elif event == "metadata":
                            metadata = data
                            badge_html = get_sufficiency_badge_html(metadata)
                            if badge_html:
                                badge_placeholder.markdown(badge_html, unsafe_allow_html=True)
                        elif event == "sources":
                            sources = data.get("sources", []) if isinstance(data, dict) else data
                        elif event == "error":
                            err_detail = data.get("detail", str(data))
                            status_placeholder.empty()
                            if not full_response:
                                full_response = f"⚠️ {err_detail}"
                            break
                    except Exception as e:
                        status_placeholder.empty()
                        if not full_response:
                            full_response = f"⚠️ Stream error: {e}"
                        break

                status_placeholder.empty()

                if not full_response:
                    full_response = "⚠️ No response generated. Please check your model configuration."

                if metadata:
                    badge_html = get_sufficiency_badge_html(metadata)
                    if badge_html:
                        badge_placeholder.markdown(badge_html, unsafe_allow_html=True)

                message_placeholder.markdown(
                    f'<div class="bot-msg-row"><div class="bot-msg-body">{full_response}</div></div>',
                    unsafe_allow_html=True,
                )
                add_testid("assistant-message")

            messages.append(
                {
                    "role": "assistant",
                    "content": full_response,
                    "sources": sources,
                    "metadata": metadata,
                }
            )
            st.session_state.messages[active_id] = messages
