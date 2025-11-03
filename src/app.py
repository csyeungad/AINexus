import streamlit as st
from logger import setup_logging
import logging
from dotenv import load_dotenv

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AINexus", layout="wide", page_icon=":memo:", initial_sidebar_state= "expanded")

pages = {
    "Chat": [st.Page("page/chat.py", title="Chat with Documents")],
    "Knowledge Base": [
        st.Page("page/uploadFile.py", title="Upload Documents"),
        st.Page("page/knowledgeBase.py", title="View Documents"),
    ],
}

if __name__ == "__main__":
    pg = st.navigation(pages)
    pg.run()
