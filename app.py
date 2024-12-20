import streamlit as st

# Set page configuration
st.set_page_config(
    page_title="Operations and monitoring - UMD",
    page_icon=":wrench:",
    layout="wide",
)

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import streamlit.components.v1 as components
import requests
import re
from PIL import Image
import io
import time
import plotly.express as px
import hmac
from translations import lang_content as translations
from navigation import make_sidebar

# Initialize session state variables
if "language" not in st.session_state:
    st.session_state["language"] = "en"  # Default language


def search_dataframe(df, query):
    """
    Search through all columns of a dataframe for a query string.
    Returns a boolean mask of matching rows.
    """
    if not query:
        return pd.Series([True] * len(df))
    
    mask = pd.Series([False] * len(df))
    for column in df.columns:
        # Convert column to string and search
        mask |= df[column].astype(str).str.contains(query, case=False, na=False)
    return mask

def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.header("Operations and monitoring - UMD", divider="grey")
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in st.secrets[
            "passwords"
        ] and hmac.compare_digest(
            st.session_state["password"],
            st.secrets.passwords[st.session_state["username"]],
        ):
            st.session_state["logged_in"] = True
            del st.session_state["password"]  # Don't store the username and password.
            del st.session_state["username"]
        else:
            st.session_state["logged_in"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("logged_in", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "logged_in" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False

make_sidebar()

if not check_password():
    st.stop()

st.title(translations['page_title'][st.session_state['language']])

st.text("Select a page from the sidebar")