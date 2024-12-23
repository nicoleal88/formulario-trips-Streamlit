import streamlit as st
from navigation import make_sidebar
from translations import lang_content as translations
import streamlit.components.v1 as components

make_sidebar()

st.header(translations['tab_map_title'][st.session_state['language']], divider="grey")

components.iframe("https://amiga-map.ahuekna.org.ar", height=900)
