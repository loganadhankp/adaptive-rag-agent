import streamlit as st

from frontend.testing_utils import add_testid


def render_settings_page():
    st.header("⚙️ Settings")

    settings = st.session_state.settings

    st.subheader("LLM Configuration")
    providers = ["gemini", "openai", "anthropic"]
    current_provider = settings.get("provider", "gemini")
    provider_idx = providers.index(current_provider) if current_provider in providers else 0
    provider = st.selectbox(
        "Provider",
        providers,
        index=provider_idx,
    )
    model = st.text_input("Model", value=settings.get("model", "gemini-3.5-flash-lite"))
    temperature = st.slider("Temperature", 0.0, 1.0, settings["temperature"], 0.05)

    st.subheader("RAG Configuration")
    answer_quality = st.slider(
        "Answer quality threshold", 50, 100, settings["answer_quality_threshold"]
    )
    max_retries = st.number_input("Max retries", 1, 5, settings["max_retries"])
    max_retrieval = st.number_input(
        "Max retrieval results", 1, 10, settings["max_retrieval_results"]
    )

    if st.button("Save Settings", type="primary"):
        st.session_state.settings.update(
            {
                "provider": provider,
                "model": model,
                "temperature": temperature,
                "answer_quality_threshold": answer_quality,
                "max_retries": max_retries,
                "max_retrieval_results": max_retrieval,
            }
        )
        st.success("Settings saved successfully!")
    add_testid("settings-panel")

    with st.expander("Current Settings JSON"):
        st.json(st.session_state.settings)
