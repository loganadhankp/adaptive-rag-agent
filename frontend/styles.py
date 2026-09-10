CUSTOM_CSS = """
/* ==========================================================================
   Google Fonts & Material Symbols
   ========================================================================== */
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

/* ==========================================================================
   Clean Dark Minimal Base Layout (ChatGPT / Gemini Dark Style)
   ========================================================================== */
header {visibility: hidden !important;}
footer {visibility: hidden !important;}
#MainMenu {visibility: hidden !important;}

.stApp {
    background-color: #0f172a !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Material Symbols Helper */
.material-symbols-outlined {
    font-family: 'Material Symbols Outlined' !important;
    font-weight: normal;
    font-style: normal;
    font-size: 18px;
    line-height: 1;
    display: inline-block;
    vertical-align: middle;
}

/* Main Container Centering & Max Width */
.main .block-container {
    max-width: 840px !important;
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    margin: 0 auto !important;
}

/* ==========================================================================
   Top Header (Knowledge Assistant)
   ========================================================================== */
.top-header {
    text-align: center;
    padding: 10px 0 16px 0;
    margin-bottom: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.top-header-title {
    font-family: 'Geist', 'Inter', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    letter-spacing: -0.02em;
}

.top-header-subtitle {
    font-size: 13px;
    color: #94a3b8;
    margin-top: 4px;
    line-height: 1.4;
}

/* ==========================================================================
   Sidebar Styling (Clean Minimal)
   ========================================================================== */
section[data-testid="stSidebar"] {
    background-color: #0b1120 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    width: 300px !important;
}

section[data-testid="stSidebar"] .block-container {
    padding: 1.25rem 1rem !important;
}

.sidebar-app-title {
    font-family: 'Geist', 'Inter', sans-serif;
    font-size: 16px;
    font-weight: 700;
    color: #f8fafc;
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 12px;
    margin-bottom: 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-section-header {
    font-size: 11px;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 18px 0 8px 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Document Row in Sidebar */
.kb-doc-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 10px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    margin-bottom: 6px;
    font-size: 12px;
}

.kb-doc-info {
    display: flex;
    align-items: center;
    gap: 8px;
    overflow: hidden;
    flex: 1;
}

.kb-doc-name {
    color: #e2e8f0;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.kb-doc-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    font-weight: 600;
    padding: 2px 5px;
    border-radius: 3px;
    background: rgba(56, 189, 248, 0.12);
    color: #38bdf8;
}

.kb-doc-status {
    font-size: 10px;
    color: #10b981;
    display: flex;
    align-items: center;
    gap: 3px;
}

/* ==========================================================================
   Chat Messages (User & Assistant)
   ========================================================================== */
.user-msg-row {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 12px;
}

.user-msg-bubble {
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
    padding: 10px 16px !important;
    border-radius: 18px 18px 4px 18px !important;
    max-width: 80% !important;
    font-size: 14px !important;
    line-height: 1.5 !important;
    word-wrap: break-word !important;
    border: 1px solid rgba(255, 255, 255, 0.06) !important;
    margin-left: auto !important;
}

.bot-msg-row {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    margin-bottom: 16px;
    width: 100%;
}

.bot-msg-body {
    background: transparent !important;
    color: #f1f5f9 !important;
    font-size: 14px !important;
    line-height: 1.65 !important;
    width: 100% !important;
}

.bot-msg-body p {
    margin-bottom: 10px !important;
}

.bot-msg-body ul, .bot-msg-body ol {
    margin-left: 20px !important;
    margin-bottom: 10px !important;
}

.bot-msg-body code {
    font-family: 'JetBrains Mono', monospace !important;
    background: rgba(255, 255, 255, 0.08) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-size: 13px !important;
}

.bot-msg-body pre {
    background: #0b1120 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 8px !important;
    padding: 12px !important;
    margin: 10px 0 !important;
}

/* ==========================================================================
   Sources & Citations Box
   ========================================================================== */
.sources-card {
    margin-top: 10px;
    padding: 10px 14px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    width: 100%;
}

.sources-card-header {
    font-size: 11px;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.source-entry {
    font-size: 12px;
    color: #cbd5e1;
    margin-bottom: 3px;
    line-height: 1.4;
}

.source-entry a {
    color: #38bdf8;
    text-decoration: none;
    font-weight: 500;
}

.source-entry a:hover {
    text-decoration: underline;
}

.web-source-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.1);
    padding: 2px 8px;
    border-radius: 4px;
    margin-bottom: 8px;
}

/* ==========================================================================
   Answer Details / Verification (Optional Collapsible)
   ========================================================================== */
.verification-container {
    margin-top: 4px;
    font-size: 12px;
    color: #94a3b8;
}

.verification-item {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 3px;
    color: #cbd5e1;
    font-size: 12px;
}

.verification-item .check-icon {
    color: #10b981;
    font-weight: bold;
}

.verification-score-badge {
    margin-top: 6px;
    font-size: 12px;
    font-weight: 600;
    color: #f1f5f9;
}

/* ==========================================================================
   Dynamic Status Indicator
   ========================================================================== */
.dynamic-status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #94a3b8;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 6px 12px;
    border-radius: 20px;
    margin-bottom: 8px;
}

.status-dot {
    width: 6px;
    height: 6px;
    background: #38bdf8;
    border-radius: 50%;
    animation: pulse-dot 1.5s infinite;
}

@keyframes pulse-dot {
    0% { opacity: 0.4; transform: scale(0.9); }
    50% { opacity: 1; transform: scale(1.2); }
    100% { opacity: 0.4; transform: scale(0.9); }
}

/* ==========================================================================
   Empty State Welcome Hero
   ========================================================================== */
.welcome-hero {
    text-align: center;
    padding: 40px 20px 20px 20px;
    max-width: 640px;
    margin: 0 auto;
}

.welcome-hero-title {
    font-family: 'Geist', 'Inter', sans-serif;
    font-size: 30px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.03em;
    margin-bottom: 8px;
}

.welcome-hero-sub {
    font-size: 14px;
    color: #94a3b8;
    margin-bottom: 24px;
    line-height: 1.5;
}

/* ==========================================================================
   Chat Input Bar & Buttons
   ========================================================================== */
.stChatInputContainer textarea {
    background-color: #1e293b !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 14px !important;
    color: #f1f5f9 !important;
    font-size: 14px !important;
}

.stChatInputContainer textarea:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 1px #38bdf8 !important;
}

.stButton > button {
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
}

.stButton > button:hover {
    border-color: rgba(255, 255, 255, 0.2) !important;
    background-color: #334155 !important;
    color: #ffffff !important;
}

.stButton > button[kind="primary"] {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #1d4ed8 !important;
}

::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
}
"""


