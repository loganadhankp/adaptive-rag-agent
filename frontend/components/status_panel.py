import datetime
import html
import streamlit as st
from frontend.testing_utils import add_testid

PIPELINE_NODES = [
    ("classify_intent", "psychology", "Intent"),
    ("retrieve", "search", "Retrieval"),
    ("grade", "bar_chart", "Relevance"),
    ("knowledge_gap", "fact_check", "Gap Analysis"),
    ("rewrite", "edit", "Rewrite"),
    ("web_search", "travel_explore", "Web Search"),
    ("generate", "smart_toy", "Generation"),
    ("hallucination", "science", "Hallucination"),
    ("evaluate", "star", "Quality"),
]

STEP_TO_NODE_MAP = {
    "classify_intent": "classify_intent",
    "retrieve_documents": "retrieve",
    "retrieve": "retrieve",
    "grade_documents": "grade",
    "knowledge_gap_analysis": "knowledge_gap",
    "knowledge_gap": "knowledge_gap",
    "grade": "grade",
    "rewrite_query": "rewrite",
    "rewrite": "rewrite",
    "retry_retrieval": "retrieve",
    "web_search": "web_search",
    "generate": "generate",
    "generate_answer": "generate",
    "regenerate": "generate",
    "check_hallucination": "hallucination",
    "hallucination": "hallucination",
    "evaluate_answer": "evaluate",
    "evaluate": "evaluate",
}


def render_chevron_stepper(active_stage: str = None, completed_stages: list = None, node_states: dict = None):
    """
    Renders the Persistent Pipeline Visualizer (Top Stepper) matching the HTML dashboard design:
    - Circular stage badges with Material Symbols icons
    - Active stage glowing neon animation (.stage-active)
    - Completed stages with cyan/teal accent
    - Subtle connecting line dividers
    """
    completed = completed_stages or []
    states = node_states or {}

    node_elements = []

    for i, (node_key, icon_name, label) in enumerate(PIPELINE_NODES):
        # Determine node state
        if node_key in states:
            node_state = states[node_key]
        elif node_key == active_stage:
            node_state = "running"
        elif node_key in completed:
            node_state = "success"
        else:
            node_state = "pending"

        node_box = (
            f'<div class="pipeline-step-node {node_state}">'
            f'<div class="pipeline-node-circle">'
            f'<span class="material-symbols-outlined" style="font-size: 17px;">{icon_name}</span>'
            f"</div>"
            f'<span class="pipeline-node-text">{html.escape(label)}</span>'
            f"</div>"
        )
        node_elements.append(node_box)

        # Append divider between nodes except after the last node
        if i < len(PIPELINE_NODES) - 1:
            divider_active = "active" if (node_state == "success" or node_state == "running") else ""
            divider_box = f'<div class="pipeline-step-divider {divider_active}"></div>'
            node_elements.append(divider_box)

    track_inner = "".join(node_elements)
    full_stepper_html = (
        '<div class="pipeline-visualizer-container">'
        '<div class="pipeline-stepper-header">'
        '<span style="color: #c7fff3; display: flex; align-items: center; gap: 6px;">'
        '<span class="material-symbols-outlined" style="color: #14f1d9; font-size: 16px;">hub</span>'
        "Self-Reflecting Pipeline"
        "</span>"
        '<span style="color: #14f1d9; font-size: 10px;">● Live Graph</span>'
        "</div>"
        f'<div class="pipeline-stepper-track">{track_inner}</div>'
        "</div>"
    )
    st.markdown(full_stepper_html, unsafe_allow_html=True)


STEP_LABELS = {
    "retrieve_documents": ("🔍", "Retrieve Documents"),
    "retrieve": ("🔍", "Retrieve Documents"),
    "grade_documents": ("📊", "Grade Documents"),
    "grade": ("📊", "Grade Documents"),
    "rewrite_query": ("✏️", "Rewrite Query"),
    "retry_retrieval": ("🔄", "Retry Retrieval"),
    "web_search": ("🌐", "Web Search Triggered"),
    "generate": ("🤖", "Generate Answer"),
    "generate_answer": ("🤖", "Generate Answer"),
    "check_hallucination": ("🔬", "Hallucination Check"),
    "evaluate_answer": ("✅", "Quality Evaluation"),
}


def render_execution_trace(workflow_steps: list[dict]):
    """
    Renders the collapsible Execution Trace in the Reflection Engine panel:
    ▼ Execution Trace with formatted timestamps [HH:MM:SS].
    """
    add_testid("status-panel")
    if not workflow_steps:
        return

    now_base = datetime.datetime.now()
    step_items_html = []

    for i, step in enumerate(workflow_steps):
        raw_step = step.get("step", "unknown")
        status = step.get("status", "completed")
        detail = step.get("detail", "")
        timestamp = step.get("timestamp")

        if not timestamp:
            # Generate simulated sequential timestamp
            step_time = now_base - datetime.timedelta(seconds=(len(workflow_steps) - i) * 1)
            timestamp = step_time.strftime("%H:%M:%S")

        icon = "✅" if status == "completed" else "❌" if status == "error" else "⏭️" if status == "skipped" else "⏳"
        emoji, title = STEP_LABELS.get(raw_step, ("➡️", str(raw_step).replace("_", " ").title()))

        step_html = (
            '<div style="margin-bottom: 8px; padding: 6px 8px; background: #15242c; border-radius: 6px; border-left: 3px solid #00d2aa;">'
            f'<div style="font-size: 11px; color: #38bdf8; font-weight: 700; display: flex; justify-content: space-between;">'
            f"<span>[{html.escape(timestamp)}] {emoji} {html.escape(title)}</span>"
            f"<span>{icon}</span>"
            "</div>"
        )
        if detail:
            step_html += f'<div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">{html.escape(detail)}</div>'
        step_html += "</div>"
        step_items_html.append(step_html)

    with st.expander("▼ Execution Trace", expanded=True):
        st.markdown("".join(step_items_html), unsafe_allow_html=True)


def render_status_panel(workflow_steps: list[dict]):
    """Legacy alias for status panel."""
    render_execution_trace(workflow_steps)
