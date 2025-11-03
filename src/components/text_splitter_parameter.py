import streamlit as st


def text_splitter_param_view():
    st.subheader("1. Select **RecursiveCharacterTextSplitter** parameters.")
    st.info("""Split a text into chunks using a **RecursiveCharacterTextSplitter**. Parameters include:

    - `chunk_size`: Max size of the resulting chunks
    - `chunk_overlap`: Overlap between the resulting chunks
    """)
    col1, col2 = st.columns([1, 1])

    with col1:
        chunk_size = st.number_input(value=1000, min_value=100, max_value=1200, label="Chunk Size", key="chunk_size")

    with col2:
        # Setting the max value of chunk_overlap based on chunk_size
        chunk_overlap = st.number_input(
            value=int(chunk_size * 0.1),
            min_value=1,
            max_value=chunk_size - 1,
            label="Chunk Overlap",
            key="chunk_overlap",
        )

        # Display a warning if chunk_overlap is not less than chunk_size
        if chunk_overlap >= chunk_size:
            st.warning("Chunk Overlap should be less than Chunk Length!")
