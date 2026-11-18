CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

header, footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    display: none !important;
    visibility: hidden !important;
}

.stApp {
    background-color: #ffffff !important;
    color: #1a1a2e !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

section[data-testid="stSidebar"] {
    background-color: #f8fafc !important;
    border-right: 1px solid #e2e8f0 !important;
    width: 320px !important;
    min-width: 320px !important;
    padding-top: 1.2rem !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding-left: 1.2rem !important;
    padding-right: 1.2rem !important;
}

.sidebar-title-container {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 2px;
}

.sidebar-section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 4px;
}

.sidebar-section-subtitle {
    font-size: 12px;
    color: #64748b;
    margin-bottom: 12px;
}

section[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    border: 2px dashed #cbd5e1 !important;
    border-radius: 12px !important;
    padding: 12px !important;
    background: #ffffff !important;
    text-align: center !important;
    transition: all 0.2s ease !important;
}

section[data-testid="stSidebar"] [data-testid="stFileUploader"]:hover {
    border-color: #1e3a8a !important;
    background: #f0f7ff !important;
}

section[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
    padding: 0 !important;
}

section[data-testid="stSidebar"] button {
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
}

.sidebar-divider {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 16px 0;
}

.uploaded-file-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    margin-bottom: 6px;
    gap: 8px;
}

.file-info-group {
    display: flex;
    align-items: center;
    gap: 8px;
    overflow: hidden;
    flex: 1;
}

.doc-type-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    font-weight: 700;
    padding: 3px 6px;
    border-radius: 4px;
    color: #ffffff;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    flex-shrink: 0;
}

.badge-pdf { background-color: #ef4444; }
.badge-docx { background-color: #2563eb; }
.badge-txt { background-color: #64748b; }
.badge-md { background-color: #8b5cf6; }

.doc-file-name {
    font-size: 13px;
    font-weight: 500;
    color: #1e293b;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.main .block-container {
    max-width: 960px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 6.5rem !important;
    margin: 0 auto !important;
}

.hero-header {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    margin-top: 10px;
    margin-bottom: 24px;
}

.hero-title {
    font-size: 26px;
    font-weight: 700;
    color: #0f172a;
    margin-top: 14px;
    margin-bottom: 6px;
    letter-spacing: -0.02em;
}

.hero-subtitle {
    font-size: 14px;
    color: #475569;
    margin: 0;
}

.chat-card-wrapper {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    min-height: 420px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
    margin-bottom: 16px;
}

.user-msg-row {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 18px;
    width: 100%;
}

.user-msg-bubble {
    background-color: #16284f !important;
    color: #ffffff !important;
    padding: 10px 18px !important;
    border-radius: 18px 18px 4px 18px !important;
    max-width: 75% !important;
    font-size: 14px !important;
    line-height: 1.5 !important;
    word-wrap: break-word !important;
}

.bot-msg-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 20px;
    width: 100%;
}

.bot-msg-body {
    background: #f8fafc !important;
    color: #1e293b !important;
    font-size: 14px !important;
    line-height: 1.65 !important;
    width: 100% !important;
    word-break: break-word !important;
    padding: 14px 18px !important;
    border-radius: 18px 18px 18px 4px !important;
    border: 1px solid #e2e8f0 !important;
}

.bot-msg-body h1, .bot-msg-body h2, .bot-msg-body h3, .bot-msg-body h4 {
    color: #0f172a !important;
    font-weight: 600 !important;
    margin-top: 1rem !important;
    margin-bottom: 0.4rem !important;
}

.bot-msg-body p {
    margin-bottom: 8px !important;
    color: #334155 !important;
    line-height: 1.65 !important;
}

.bot-msg-body strong, .bot-msg-body b {
    color: #0f172a !important;
    font-weight: 600 !important;
}

.bot-msg-body ul, .bot-msg-body ol {
    margin: 0.3rem 0 0.7rem 1.4rem !important;
    padding-left: 0.2rem !important;
}

.bot-msg-body li {
    margin-bottom: 0.3rem !important;
    line-height: 1.6 !important;
    color: #334155 !important;
}

.bot-msg-body code {
    font-family: 'JetBrains Mono', monospace !important;
    background: #e2e8f0 !important;
    color: #0f172a !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 12.5px !important;
}

.bot-msg-body pre {
    background: #0f172a !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
    padding: 12px !important;
    margin: 10px 0 !important;
}

.bot-msg-body pre code {
    background: transparent !important;
    color: #e2e8f0 !important;
}

.dynamic-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #64748b;
    background: #f1f5f9;
    border: 1px solid #e2e8f0;
    padding: 5px 12px;
    border-radius: 20px;
    margin-bottom: 10px;
}

.status-dot {
    width: 6px;
    height: 6px;
    background: #16284f;
    border-radius: 50%;
    animation: pulse-dot 1.5s infinite;
}

@keyframes pulse-dot {
    0% { opacity: 0.4; transform: scale(0.9); }
    50% { opacity: 1; transform: scale(1.2); }
    100% { opacity: 0.4; transform: scale(0.9); }
}

div[data-testid="stBottom"] {
    background-color: #ffffff !important;
    border-top: 1px solid #f1f5f9 !important;
}

div[data-testid="stBottom"] > div {
    max-width: 960px !important;
    margin: 0 auto !important;
}

div[data-testid="stChatInput"] {
    border-radius: 10px !important;
    border: 1px solid #cbd5e1 !important;
    background-color: #f8fafc !important;
}

div[data-testid="stChatInput"]:focus-within {
    border-color: #16284f !important;
    background-color: #ffffff !important;
}

div[data-testid="stChatInput"] textarea {
    color: #0f172a !important;
    font-size: 14px !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    color: #64748b !important;
}

div[data-testid="stChatInput"] button {
    background-color: #16284f !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 8px 16px !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    min-width: 82px !important;
    justify-content: center !important;
}

div[data-testid="stChatInput"] button:hover {
    background-color: #0f1d38 !important;
}

div[data-testid="stChatInput"] button::after {
    content: "Send" !important;
    color: #ffffff !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    margin-left: 4px !important;
}

div[data-testid="stChatInput"] button svg {
    fill: #ffffff !important;
    color: #ffffff !important;
}
"""
