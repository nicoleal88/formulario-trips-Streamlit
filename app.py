import streamlit as st
import hmac
from translations import lang_content as translations
from navigation import make_sidebar

# Set page configuration
st.set_page_config(
    page_title="Operations and monitoring - UMD",
    page_icon=":wrench:",
    layout="wide",
)

# Initialize session state variables
if "language" not in st.session_state:
    st.session_state["language"] = "en"  # Default language

empty1, col1, empty2 = st.columns((0.25, .5, 0.25))

def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with col1:
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

with col1:
    st.header("Welcome to UMD Operations & Monitoring! 👋")
    st.write("This web application helps you track and manage UMD operations. Here's what you can find in each section:")

    st.subheader("📍 Navigation Guide")
    
    st.markdown("""
    - **🗺️ Map**: Interactive map showing UMD locations and deployment status
    - **🔧 Field Work**: Track and log field work activities and maintenance records
    - **📊 Acquisitions**: Monitor data acquisition status and known issues
    - **📈 Statistics**: View statistical analysis and trends of UMD operations
    - **🔍 UMD Details**: Detailed information and diagnostics for specific UMDs
    
    Use the navigation sidebar on the left to explore these sections. Each page includes search and filter options to help you find specific information quickly.
    
    Need help? Contact support through the link in the sidebar.
    """)