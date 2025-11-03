import streamlit as st


def session_monitor_sidebar():
    st.sidebar.write("## Session State Monitor")
    # st.sidebar.markdown(f"#### Session id: {st.session_state.config['configurable']['thread_id']}")
    selection = st.sidebar.selectbox(
        label="Session State Monitor", options=st.session_state.keys(), label_visibility="hidden"
    )
    if selection:
        st.sidebar.json(st.session_state[f"{selection}"])
