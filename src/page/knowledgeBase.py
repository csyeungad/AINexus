import streamlit as st
from components.confirmation_dialog import ConfirmDiaglo
from Retriever import retriever

PREVIEW_NO = 3


def handleResetCollection():
    try:
        retriever.db.reset_collection()
        retriever.create_compression_retriever()
        st.sidebar.success(f"Successfully reset database.")
    except Exception as e:
        st.sidebar.error(f"Unable to reset database.")


lcol, rcol = st.columns([0.8, 0.2])
lcol.header("Knowledge base")
lcol.markdown("""
    Shows all the chunks avaliable in the vector database.
""")

rcol.button(f"Reset Database", on_click=handleResetCollection, use_container_width=True)

sources, documents = retriever.db.get_all_data(limit=PREVIEW_NO)
if not sources or not documents:
    st.info(f"There is no documents in the database. Please upload some documents.")
else:
    # Create tabs
    num_sources_per_tab = 5
    num_tabs = (len(sources) + num_sources_per_tab - 1) // num_sources_per_tab  # Calculate number of tabs
    tabs = st.tabs([f"{1 + i * num_sources_per_tab} - {(1 + i) * num_sources_per_tab}" for i in range(num_tabs)])

    # Display sources and their documents in each tab
    for i in range(num_tabs):
        with tabs[i]:
            start_index = i * num_sources_per_tab
            end_index = start_index + num_sources_per_tab
            current_sources = sources[start_index:end_index]
            current_documents = documents[start_index:end_index]

            for src, chunks in zip(current_sources, current_documents):
                lcol, rcol = st.columns([0.9, 0.1])
                with lcol.expander(f"## {src}"):
                    # Delete and confirmation dialog

                    placeholder = rcol.empty()
                    placeholder.markdown(f"### {src}")
                    is_click = placeholder.button(f":x: :red[Delete document]", key=src, use_container_width=True)
                    if is_click:
                        ConfirmDiaglo(src, placeholder)

                    text = ""
                    for i, chunk in enumerate(chunks):
                        text += f"- {chunk}\n"
                        if i == PREVIEW_NO - 1:
                            break
                    st.markdown(text)
                    st.markdown(f"**Skip preview of long documents**..........")
