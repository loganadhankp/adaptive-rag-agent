import html
import uuid
import streamlit as st
from frontend.testing_utils import add_testid

def get_robot_hero_html() -> str:
    return """
    <div class="hero-header">
        <svg width="84" height="84" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="50" y1="12" x2="50" y2="24" stroke="#1d4ed8" stroke-width="4" stroke-linecap="round"/>
            <circle cx="50" cy="10" r="5" fill="#1d4ed8"/>
            <rect x="18" y="24" width="64" height="52" rx="26" fill="#ffffff" stroke="#1d4ed8" stroke-width="4"/>
            <rect x="10" y="42" width="10" height="16" rx="5" fill="#1d4ed8"/>
            <rect x="80" y="42" width="10" height="16" rx="5" fill="#1d4ed8"/>
            <rect x="26" y="32" width="48" height="36" rx="18" fill="#0f172a"/>
            <circle cx="39" cy="48" r="4.5" fill="#38bdf8"/>
            <circle cx="61" cy="48" r="4.5" fill="#38bdf8"/>
            <path d="M44 57 Q50 62 56 57" stroke="#38bdf8" stroke-width="2.5" stroke-linecap="round" fill="none"/>
            <path d="M72 16 C72 11.58 76.48 8 82 8 C87.52 8 92 11.58 92 16 C92 20.42 87.52 24 82 24 C80.5 24 79.1 23.7 77.8 23.2 L74 25 L74.8 21.6 C73.1 20.1 72 18.2 72 16 Z" fill="#ffffff" stroke="#3b82f6" stroke-width="2"/>
            <circle cx="78" cy="16" r="1.5" fill="#3b82f6"/>
            <circle cx="82" cy="16" r="1.5" fill="#3b82f6"/>
            <circle cx="86" cy="16" r="1.5" fill="#3b82f6"/>
        </svg>
        <div class="hero-title">Ask me anything about your documents!</div>
        <div class="hero-subtitle">I'll find accurate answers using RAG with self-reflection.</div>
    </div>
    """

def render_chat_window(api_client, settings):
    add_testid("chat-window")

    active_id = st.session_state.get("active_conversation_id")
    if not active_id:
        active_id = str(uuid.uuid4())
        st.session_state.active_conversation_id = active_id

    if active_id not in st.session_state.messages:
        st.session_state.messages[active_id] = []

    messages = st.session_state.messages.get(active_id, [])

    st.markdown(get_robot_hero_html(), unsafe_allow_html=True)

    chat_container = st.container()

    with chat_container:
        if not messages:
            st.markdown(
                '<div class="chat-card-wrapper" style="display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:14px;"></div>',
                unsafe_allow_html=True,
            )
        else:
            for i, msg in enumerate(messages):
                role = msg.get("role", "user")
                content = msg.get("content", "")

                if role == "user":
                    st.markdown(
                        f'<div class="user-msg-row"><div class="user-msg-bubble">{html.escape(content)}</div></div>'
                        f'<div data-testid="user-message" data-msg-idx="{i}" style="display:none"></div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div class="bot-msg-row"><div class="bot-msg-body">\n\n{content}\n\n</div></div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div data-testid="assistant-message" data-msg-idx="{i}" style="display:none"></div>',
                        unsafe_allow_html=True,
                    )

    add_testid("chat-input")
    user_input = st.chat_input("Type your question here...")

    if user_input:
        prompt_text = user_input.strip() if isinstance(user_input, str) else ""

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
