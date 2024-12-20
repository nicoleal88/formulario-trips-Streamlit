import streamlit as st
from time import sleep
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages
from translations import lang_content as translations
from utils import switch_language


def get_current_page_name() -> str:
    """Returns the name of the current page."""
    try:
        return st.get_query_params()["page"][0]
    except:
        return "app"


def make_sidebar():
    with st.sidebar:
        st.title("Navigation")
        st.write("")

        if st.session_state.get("logged_in", False):
            st.page_link("pages/1_map.py", label="Map", icon="🗺️")
            st.page_link("pages/2_field.py", label="Field", icon="📋")
            st.page_link("pages/3_acquisition.py", label="Acquisition", icon="📊")
            st.page_link("pages/4_stats.py", label="Statistics", icon="📈")
            st.page_link("pages/5_umd_details.py", label="UMD Details", icon="🔍")

            st.write("")
            st.write("")

            # Add language switcher in the sidebar
            if st.button("🌐 " + translations['switch_language'][st.session_state['language']]):
                switch_language()

            if st.button("Log out"):
                logout()

        elif get_current_page_name() != "app":
            # If anyone tries to access a secret page without being logged in,
            # redirect them to the login page
            st.switch_page("app.py")


def logout():
    st.session_state.logged_in = False
    st.info("Logged out successfully!")
    sleep(0.5)
    st.switch_page("app.py")