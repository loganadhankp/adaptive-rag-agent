CUSTOM_CSS = """
/* ==========================================================================
Minimal ChatGPT / Gemini Layout (Zero Clutter)
   ========================================================================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* Hide all Streamlit boilerplate and headers */
header, footer, #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    display: none !important;
    visibility: hidden !important;
}

/* Hide Sidebar completely */
[data-testid="stSidebar"], section[data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display: none !important;
    width: 0px !important;
    visibility: hidden !important;
}

/* Base Body & App */
.stApp {
    background-color: #212121 !important;
    color: #ececec !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Center Chat Area */
.main .block-container {
    max-width: 768px !important;
    padding-top: 2.5rem !important;
    padding-bottom: 7.5rem !important;
    margin: 0 auto !important;
}

/* User Message */
.user-msg-row {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 20px;
    width: 100%;
}

.user-msg-bubble {
    background-color: #2f2f2f !important;
    color: #ececec !important;
    padding: 10px 18px !important;
    border-radius: 20px !important;
    max-width: 75% !important;
    font-size: 14.5px !important;
    line-height: 1.5 !important;
    word-wrap: break-word !important;
}

/* Assistant Message */
.bot-msg-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 24px;
    width: 100%;
}

.bot-msg-body {
    background: transparent !important;
    color: #e5e7eb !important;
    font-size: 14.5px !important;
    line-height: 1.65 !important;
    width: 100% !important;
    word-break: break-word !important;
}

.bot-msg-body h1, .bot-msg-body h2, .bot-msg-body h3, .bot-msg-body h4 {
    color: #f9fafb !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
    margin-top: 1.2rem !important;
    margin-bottom: 0.5rem !important;
}

.bot-msg-body h1 { font-size: 1.45rem !important; }
.bot-msg-body h2 { 
    font-size: 1.25rem !important; 
    border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
    padding-bottom: 6px !important;
}
.bot-msg-body h3 { font-size: 1.1rem !important; }
.bot-msg-body h4 { font-size: 0.95rem !important; }

.bot-msg-body p {
    margin-bottom: 10px !important;
    color: #e5e7eb !important;
    line-height: 1.65 !important;
}

.bot-msg-body strong, .bot-msg-body b {
    color: #ffffff !important;
    font-weight: 600 !important;
}

.bot-msg-body ul, .bot-msg-body ol {
    margin: 0.4rem 0 0.85rem 1.4rem !important;
    padding-left: 0.2rem !important;
}

.bot-msg-body li {
    margin-bottom: 0.35rem !important;
    line-height: 1.6 !important;
    color: #e5e7eb !important;
}

.bot-msg-body blockquote {
    border-left: 3px solid #6366f1 !important;
    background: rgba(99, 102, 241, 0.08) !important;
    padding: 8px 14px !important;
    border-radius: 0 8px 8px 0 !important;
    margin: 12px 0 !important;
    color: #c7d2fe !important;
}

.bot-msg-body hr {
    border: none !important;
    border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
    margin: 1.25rem 0 !important;
}

.bot-msg-body table {
    width: 100% !important;
    border-collapse: collapse !important;
    margin: 14px 0 !important;
    font-size: 13.5px !important;
}

.bot-msg-body th {
    background: rgba(255, 255, 255, 0.06) !important;
    color: #f9fafb !important;
    font-weight: 600 !important;
    padding: 8px 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    text-align: left !important;
}

.bot-msg-body td {
    padding: 8px 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #d1d5db !important;
}

.bot-msg-body code {
    font-family: 'JetBrains Mono', monospace !important;
    background: rgba(255, 255, 255, 0.08) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 13px !important;
}

.bot-msg-body pre {
    background: #171717 !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
    padding: 12px !important;
    margin: 12px 0 !important;
}

/* Dynamic Status Indicator */
.dynamic-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #9ca3af;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 5px 12px;
    border-radius: 20px;
    margin-bottom: 10px;
}

.status-dot {
    width: 6px;
    height: 6px;
    background: #60a5fa;
    border-radius: 50%;
    animation: pulse-dot 1.5s infinite;
}

@keyframes pulse-dot {
    0% { opacity: 0.4; transform: scale(0.9); }
    50% { opacity: 1; transform: scale(1.2); }
    100% { opacity: 0.4; transform: scale(0.9); }
}

/* Sufficiency Badges */
.badge-sufficient {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 8px;
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.25);
}

.badge-partially-sufficient {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 8px;
    background: rgba(245, 158, 11, 0.12);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.25);
}

.badge-insufficient {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 8px;
    background: rgba(249, 115, 22, 0.12);
    color: #f97316;
    border: 1px solid rgba(249, 115, 22, 0.25);
}

.badge-irrelevant {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 8px;
    background: rgba(239, 68, 68, 0.12);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.25);
}

/* Streamlit Bottom Chat Input Bar */
div[data-testid="stBottom"] {
    background-color: #212121 !important;
}

div[data-testid="stBottom"] > div {
    max-width: 768px !important;
    margin: 0 auto !important;
}

div[data-testid="stChatInput"] {
    border-radius: 24px !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    background-color: #2f2f2f !important;
}

div[data-testid="stChatInput"]:focus-within {
    border-color: rgba(255, 255, 255, 0.35) !important;
}

div[data-testid="stChatInput"] textarea {
    color: #ececec !important;
    font-size: 14.5px !important;
}

/* Fixed Upload Document Button at Bottom-Left */
.fixed-bottom-left-upload {
    position: fixed !important;
    bottom: 22px !important;
    left: 24px !important;
    z-index: 99999 !important;
}

.fixed-bottom-left-upload div[data-testid="stPopover"] > button {
    background-color: #2f2f2f !important;
    color: #ececec !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 20px !important;
    padding: 8px 14px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3) !important;
    transition: all 0.15s ease !important;
}

.fixed-bottom-left-upload div[data-testid="stPopover"] > button:hover {
    background-color: #383838 !important;
    border-color: rgba(255, 255, 255, 0.3) !important;
    color: #ffffff !important;
}
"""
