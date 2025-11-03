import streamlit as st
import time
import os
import shutil
from components.text_splitter_parameter import text_splitter_param_view
import tempfile
from DocumentLoader import DocumentLoader
from langchain.schema import Document
from Retriever import retriever
TEMP_DIR = "../fileupload_tmp"

os.makedirs(TEMP_DIR, exist_ok=True)
if "docs_chunks_with_ids" not in st.session_state.keys():
    st.session_state.docs_chunks = []

def upload_to_database(docs_chunks: list[Document]):
    upload_status = retriever.db.add_chunks(docs_chunks)
    if upload_status:
        retriever.create_compression_retriever()
        st.success(f"Documents ingested to database successfully!")
    else:
        st.info(f"No documents are ingested into database. Check if documents already exist in database.")


st.header("Upload Documents")
text_splitter_param_view()
st.subheader("2. Upload documents (multiple files allowed).")
st.file_uploader("Choose a file", type=["pdf", "txt", ".md", "html"], key="file_uploader", accept_multiple_files=True)

if st.button("Split documents"):
    if st.session_state.file_uploader is not None:
        # Upload and save files to a temporary directory
        current_time = time.strftime("%Y%m%d")
        temp_dir = tempfile.mkdtemp(dir="../fileupload_tmp", prefix=f"{current_time}_")
        st.session_state.files_path = []
        # Download to temp
        for file in st.session_state.file_uploader:
            path = os.path.join(temp_dir, file.name)
            with open(path, "wb") as f:
                f.write(file.getvalue())
            st.session_state.files_path.append(path)
            # st.success(f"{file.name} uploaded to server successfully!")

        with st.spinner(f"Splitting {len(st.session_state.files_path)} files into chunks..."):
            st.session_state.docs_chunks = DocumentLoader(
                files=st.session_state.files_path,
                chunk_size=st.session_state.chunk_size,
                chunk_overlap=st.session_state.chunk_overlap,
            ).docs_chunks

    else:
        st.error("Please upload a file before clicking the upload button.")

if st.session_state.docs_chunks:
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Failed to clean temp dir: {e}")
        
    st.subheader("3. Edit the split documents before ingesting in to the database...")
    with st.expander(f"Chunks Preview:"):
        for i, doc_chunks in enumerate(st.session_state.docs_chunks):
            chunk_id = doc_chunks.metadata["chunk_id"]
            text = st.text_area(
                label=f"**{chunk_id}**",
                value=doc_chunks.page_content,
                key=f"{chunk_id}_chunk",
            )

    st.subheader("4. Confirm to upload to database...")
    upload = st.button("Upload to database", on_click=upload_to_database, args=[st.session_state.docs_chunks])
    if upload:
        # Clear file upload and chunks related session state
        for k, v in st.session_state.items():
            if k == "file_uploader" or k == "files_path":
                del st.session_state[f"{k}"]
            if "_chunk" in k:
                del st.session_state[f"{k}"]
        st.success(f"Cleaned file_upload state.")
