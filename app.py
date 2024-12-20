import streamlit as st
import hmac
from navigation import make_sidebar

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

st.title("Welcome to Diamond Corp")