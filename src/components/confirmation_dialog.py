import streamlit as st
from time import sleep
from Retriever import retriever


@st.dialog("Confirm deletion of document")
def ConfirmDiaglo(source, placeholder):
    st.info(f"Source: {source}")
    if st.button("Confirm"):
        ids = retriever.db.get_all_ids(source=source)
        retriever.db.delete_by_ids(ids=ids)
        st.success(f"Sucessfully deleted\n\n{ids}")
        placeholder.empty()
        sleep(1.5)
        st.rerun()
