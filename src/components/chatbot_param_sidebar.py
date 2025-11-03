import streamlit as st


def reset_history():
    del st.session_state.history


def sidebar_parameters_setting():
    st.sidebar.write("## Choose the RAG parameters")
    st.sidebar.markdown("### Model")
    st.sidebar.selectbox("Model", ["To be update"], key="model")
    st.sidebar.markdown("### Max number of retrieve documents")
    st.sidebar.slider("Top_k", 3, 10, key="top_k")
    st.sidebar.markdown("### Retrieve score threshold")
    st.sidebar.slider("score", 0.5, 1.5, key="score_threshold")
    st.sidebar.button(":x: Reset Chat History", on_click=reset_history)
