import streamlit as st


def render_analytics_dashboard(api_client):
    st.header("📊 Analytics Dashboard")

    if st.button("🔄 Refresh"):
        st.rerun()

    analytics = api_client.get_analytics()

    if not analytics:
        st.info("No analytics data available yet.")
        return

    # Top Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Conversations", analytics.get("total_conversations", 0))
    with col2:
        st.metric("Total Messages", analytics.get("total_messages", 0))
    with col3:
        success_rate = analytics.get("retrieval_success_rate", 0)
        st.metric("Retrieval Success Rate", f"{success_rate:.1f}%")
    with col4:
        avg_score = analytics.get("avg_answer_quality", 0)
        st.metric("Avg Answer Quality", f"{avg_score:.1f}/100")

    st.divider()

    # Second Row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Query Rewrites", analytics.get("query_rewrites_count", 0))
    with col2:
        st.metric("Web Search Fallbacks", analytics.get("web_search_count", 0))
    with col3:
        st.metric("Hallucination Failures", analytics.get("hallucination_failures_count", 0))

    # Optional visualization depends on plotly; skip if not available
    try:
        import plotly.express as px

        st.subheader("Metrics Visualization")

        data = {
            "Metric": [
                "Conversations",
                "Messages",
                "Query Rewrites",
                "Web Searches",
                "Hallucination Alerts",
            ],
            "Count": [
                analytics.get("total_conversations", 0),
                analytics.get("total_messages", 0),
                analytics.get("query_rewrites_count", 0),
                analytics.get("web_search_count", 0),
                analytics.get("hallucination_failures_count", 0),
            ],
        }

        fig = px.bar(
            data, x="Metric", y="Count", title="System Usage & Adaptive Metrics", color="Metric"
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        # Visualization is optional; ignore failures in environments without plotly
        pass
