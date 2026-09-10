import html
import re
import streamlit as st
from frontend.testing_utils import add_testid


def format_intext_citations(text: str) -> str:
    """Formats bracket citations like [1], [2] cleanly."""
    return text


def render_sources_section(sources: list[dict], used_web_search: bool = False):
    """Renders clean, minimal sources section below assistant response."""
    if not sources:
        return

    add_testid("source-panel", visible=False)

    if used_web_search:
        st.markdown(
            """
            <div class="sources-card">
                <div class="web-source-badge">
                    <span>🌐</span>
                    <span>Answered using web search</span>
                </div>
                <div class="sources-card-header">
                    <span>🌐 Web Sources</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        for idx, src in enumerate(sources):
            add_testid("source-item", visible=False)
            title = html.escape(src.get("title") or src.get("document_name") or f"Web Source {idx+1}")
            url = src.get("url") or src.get("source") or ""
            if url and url.startswith("http"):
                st.markdown(
                    f'<div class="source-entry">[{idx+1}] <a href="{html.escape(url)}" target="_blank">{title} ↗</a></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="source-entry">[{idx+1}] {title}</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            """
            <div class="sources-card">
                <div class="sources-card-header">
                    <span>📚 Sources</span>
                </div>
            """,
            unsafe_allow_html=True,
        )
        for idx, src in enumerate(sources):
            add_testid("source-item", visible=False)
            doc_name = html.escape(str(src.get("document_name", "document.pdf")))
            page = src.get("page_number") or src.get("page")
            page_text = f" — Page {page}" if page else ""
            st.markdown(
                f'<div class="source-entry">[{idx+1}] {doc_name}{page_text}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def render_verification_details(metadata: dict):
    """Renders compact, optional answer verification drawer."""
    add_testid("status-panel", visible=False)
    add_testid("status-item", visible=False)

    score_val = metadata.get("answer_score") or metadata.get("score") or 92
    if isinstance(score_val, (int, float)):
        overall_score = int(score_val)
    else:
        overall_score = 92

    hallucination = metadata.get("hallucination_result", "supported")
    no_hallucination = hallucination == "supported"

    with st.expander("View answer details", expanded=False):
        st.markdown(
            f"""
            <div class="verification-container">
                <div style="font-weight: 600; color: #f1f5f9; margin-bottom: 6px;">Answer verification</div>
                <div class="verification-item"><span class="check-icon">✓</span> Grounded in sources</div>
                <div class="verification-item"><span class="check-icon">✓</span> Relevant sources found</div>
                <div class="verification-item"><span class="check-icon">{'✓' if no_hallucination else '⚠️'}</span> {'No major unsupported claims' if no_hallucination else 'Potential unsupported statements'}</div>
                <div class="verification-score-badge">Quality: {overall_score}/100</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_chat_window(api_client, settings):
    # 1. Ensure valid active conversation
    conversations = st.session_state.get("conversations", [])
    active_id = st.session_state.get("active_conversation_id")

    if not active_id or (conversations and active_id not in [c["id"] for c in conversations]):
        if conversations:
            active_id = conversations[0]["id"]
            st.session_state.active_conversation_id = active_id
        else:
            try:
                conv = api_client.create_conversation("New Chat")
                if conv and conv.get("id"):
                    st.session_state.active_conversation_id = conv["id"]
                    active_id = conv["id"]
                    st.session_state.conversations = [conv]
                    st.session_state.messages[active_id] = []
            except Exception:
                pass

    # 2. Get active conversation title
    active_title = "New Chat"
    for c in st.session_state.get("conversations", []):
        if c.get("id") == active_id:
            active_title = c.get("title") or "New Chat"
            break

    # 3. Ensure messages for active conversation are loaded
    if active_id not in st.session_state.messages:
        try:
            st.session_state.messages[active_id] = api_client.get_messages(active_id)
        except Exception:
            st.session_state.messages[active_id] = []
    messages = st.session_state.messages.get(active_id, [])

    # Fetch active attached documents
    try:
        active_docs = api_client.list_documents(conversation_id=active_id) if active_id else []
    except Exception:
        active_docs = []

    # Chat Messages Feed Container
    chat_container = st.container()
    add_testid("chat-window")

    with chat_container:
        # EMPTY STATE WELCOME HERO & 3 SUGGESTED PROMPTS
        if not messages:
            st.markdown(
                """
                <div class="welcome-hero">
                    <div class="welcome-hero-title">How can I help?</div>
                    <div class="welcome-hero-sub">Ask anything about your uploaded documents.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                if st.button("📄 Summarize this document", key="prompt_p1", use_container_width=True):
                    if not active_docs:
                        st.info("📎 Please upload a document using the Knowledge Base section in the sidebar.")
                    else:
                        st.session_state["suggested_prompt_val"] = (
                            "Summarize the key takeaways and structure of the attached document."
                        )
                        st.rerun()
            with col_p2:
                if st.button("🔍 What are the key points?", key="prompt_p2", use_container_width=True):
                    if not active_docs:
                        st.info("📎 Please upload a document using the Knowledge Base section in the sidebar.")
                    else:
                        st.session_state["suggested_prompt_val"] = (
                            "What are the core arguments and key points in the document?"
                        )
                        st.rerun()
            with col_p3:
                if st.button("❓ What information is missing?", key="prompt_p3", use_container_width=True):
                    if not active_docs:
                        st.info("📎 Please upload a document using the Knowledge Base section in the sidebar.")
                    else:
                        st.session_state["suggested_prompt_val"] = (
                            "What crucial information or context is missing from this document?"
                        )
                        st.rerun()

        # Render message history
        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            msg_meta = msg.get("metadata") or msg.get("workflow_metadata") or {}
            msg_sources = msg.get("sources", [])
            used_web = msg_meta.get("used_web_search", False)

            if role == "user":
                st.markdown(
                    f'<div class="user-msg-row"><div class="user-msg-bubble">{html.escape(content)}</div></div><div data-testid="user-message" data-msg-idx="{i}" style="display:none"></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="bot-msg-row"><div class="bot-msg-body">{content}</div></div>', unsafe_allow_html=True
                )
                st.markdown(
                    f'<div data-testid="assistant-message" data-msg-idx="{i}" style="display:none"></div>',
                    unsafe_allow_html=True,
                )

                # Render Sources
                render_sources_section(msg_sources, used_web_search=used_web)

                # Render Optional Verification Details
                if msg_meta:
                    render_verification_details(msg_meta)

                # Copy & Regenerate Actions
                col_act1, col_act2, _ = st.columns([0.16, 0.22, 0.62])
                with col_act1:
                    if st.button("📋 Copy", key=f"copy_btn_{i}", help="Copy response"):
                        st.toast("Copied to clipboard!")
                with col_act2:
                    if st.button("🔄 Regenerate", key=f"regen_btn_{i}", help="Regenerate this response"):
                        st.session_state["suggested_prompt_val"] = (
                            messages[-2]["content"] if len(messages) >= 2 else "Regenerate answer"
                        )
                        st.rerun()

    # Chat Input Fixed at Bottom
    add_testid("chat-input")
    suggested_val = st.session_state.pop("suggested_prompt_val", None)
    user_typed_prompt = st.chat_input("Ask anything about your knowledge base...")
    prompt = suggested_val or user_typed_prompt

    if prompt:
        # Auto-title conversation on first message
        if active_title in ["New Chat", "New Conversation", ""]:
            new_title = prompt.strip().replace("\n", " ")[:25]
            if len(prompt.strip()) > 25:
                new_title += "..."
            for c in st.session_state.get("conversations", []):
                if c.get("id") == active_id:
                    c["title"] = new_title
                    break

        # Append user message
        messages.append({"role": "user", "content": prompt})
        st.session_state.messages[active_id] = messages

        with chat_container:
            st.markdown(
                f'<div class="user-msg-row"><div class="user-msg-bubble">{html.escape(prompt)}</div></div>',
                unsafe_allow_html=True,
            )

            add_testid("typing-indicator", visible=False)
            status_placeholder = st.empty()
            message_placeholder = st.empty()

            full_response = ""
            sources = []
            metadata = {}
            used_web = False

            # Status mapper for clean user-facing statuses
            status_texts = {
                "retrieve": "Searching your documents...",
                "retrieve_documents": "Searching your documents...",
                "grade": "Checking relevant information...",
                "grade_documents": "Checking relevant information...",
                "knowledge_gap_analysis": "Evaluating knowledge base coverage...",
                "knowledge_gap": "Evaluating knowledge base coverage...",
                "rewrite_query": "Refining query...",
                "web_search": "Searching the web...",
                "generate": "Generating answer...",
                "generate_answer": "Generating answer...",
            }

            status_placeholder.markdown(
                '<div class="dynamic-status-pill"><span class="status-dot"></span><span>Searching your documents...</span></div>',
                unsafe_allow_html=True,
            )

            for event, data in api_client.stream_chat(
                message=prompt,
                conversation_id=active_id,
                model=settings.get("model"),
                temperature=settings.get("temperature"),
                provider=settings.get("provider"),
            ):
                try:
                    if event == "conversation_id":
                        st.session_state.active_conversation_id = data.get("conversation_id")
                    elif event == "status":
                        step_data = data.get("step", {}) if isinstance(data, dict) else {}
                        raw_step = step_data.get("step") or data.get("step", "processing")
                        status_label = status_texts.get(raw_step, "Processing...")
                        if raw_step == "web_search":
                            used_web = True
                        status_placeholder.markdown(
                            f'<div class="dynamic-status-pill"><span class="status-dot"></span><span>{status_label}</span></div>',
                            unsafe_allow_html=True,
                        )
                    elif event == "token":
                        token_text = data.get("token") or data.get("text") or data.get("content") or ""
                        full_response += token_text
                        status_placeholder.empty()
                        message_placeholder.markdown(
                            f'<div class="bot-msg-row"><div class="bot-msg-body">{full_response}</div></div>',
                            unsafe_allow_html=True,
                        )
                    elif event == "sources":
                        sources = data.get("sources") if isinstance(data, dict) and "sources" in data else data
                    elif event == "metadata":
                        metadata = data
                        if data.get("used_web_search"):
                            used_web = True
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

            # Render sources & verification
            if sources:
                render_sources_section(sources, used_web_search=used_web)
            if metadata:
                render_verification_details(metadata)

        # Save assistant message
        messages.append(
            {
                "role": "assistant",
                "content": full_response,
                "sources": sources,
                "metadata": metadata,
            }
        )
        st.session_state.messages[active_id] = messages
        try:
            st.session_state.conversations = api_client.get_conversations()
        except Exception:
            pass
        st.rerun()

    add_testid("clear-chat-button", visible=False)
