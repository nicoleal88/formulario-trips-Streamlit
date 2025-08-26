import streamlit as st
from navigation import make_sidebar
from translations import lang_content as translations
import streamlit.components.v1 as components
from utils import check_login

# Check if user is logged in, redirect to home page if not
if not check_login():
    st.stop()

make_sidebar()

st.header(translations['tab_map_title'][st.session_state['language']], divider="grey")

# components.iframe("https://amiga-map.ahuekna.org.ar", height=900)
components.iframe("https://plot-amiga.nicoleal88.cc", height=900)