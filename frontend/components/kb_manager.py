import streamlit as st

from frontend.testing_utils import add_testid


def render_kb_manager(api_client):
    st.header("📚 Knowledge Base Management")

    st.subheader("Upload Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF, DOCX, or TXT files",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
    )

    if st.button("Upload", type="primary") and uploaded_files:
        progress_text = "Operation in progress. Please wait."
        my_bar = st.progress(0, text=progress_text)
        # marker for upload button
        add_testid("kb-upload-button")

        for i, file in enumerate(uploaded_files):
            # Update progress
            progress = (i + 1) / len(uploaded_files)
            my_bar.progress(progress, text=f"Uploading {file.name}...")

            res = api_client.upload_document(file.name, file.getvalue(), file.type)
            if res:
                st.toast(f"Successfully uploaded {file.name}!", icon="✅")
            else:
                st.toast(f"Failed to upload {file.name}.", icon="❌")

        my_bar.progress(1.0, text="Upload complete!")
        st.rerun()

    st.divider()

    st.subheader("Uploaded Documents")

    documents = api_client.list_documents()
    add_testid("kb-document-list")

    if not documents:
        st.info("No documents uploaded yet.")
    else:
        for doc in documents:
            with st.container(border=True):
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                with col1:
                    st.markdown(f"**{doc.get('filename', 'Unknown')}**")
                    st.markdown(
                        '<div data-testid="kb-document-item" data-doc-id="%s" style="display:none"></div>'
                        % doc.get("id"),
                        unsafe_allow_html=True,
                    )
                with col2:
                    st.caption(f"Type: {doc.get('file_type', 'Unknown')}")
                with col3:
                    st.caption(f"Chunks: {doc.get('chunk_count', 0)}")
                with col4:
                    st.caption(f"Date: {doc.get('uploaded_at', 'Unknown')}")
                with col5:
                    if st.button("🗑️", key=f"del_doc_{doc.get('id')}", help="Delete"):
                        if api_client.delete_document(doc.get("id")):
                            st.toast(f"Deleted {doc.get('filename')}")
                            st.rerun()
                        else:
                            st.toast("Failed to delete document", icon="❌")
