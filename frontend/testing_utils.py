import streamlit as st


def add_testid(testid: str, visible: bool = False) -> None:
    """Insert a small DOM marker with a stable data-testid attribute.

    We render a tiny div with the data-testid so Playwright can reliably
    query it. By default it's visually hidden to avoid layout changes.
    """
    style = "display:none;" if not visible else "display:block;"
    st.markdown(
        f'<div data-testid="{testid}" style="{style}"></div>', unsafe_allow_html=True
    )
