import streamlit as st
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

from translations import lang_content as translations  # Import the content dictionary directly

# Scintillator mapping data
num_scintillator = list(range(1, 65))
num_canalFPGA = [
    13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32, 5, 6, 7, 8,
    40, 39, 38, 37, 48, 47, 46, 45, 64, 63, 62, 61, 56, 55, 54, 53,
    12, 11, 10, 9, 20, 19, 18, 17, 28, 27, 26, 25, 4, 3, 2, 1,
    33, 34, 35, 36, 41, 42, 43, 44, 57, 58, 59, 60, 49, 50, 51, 52
]
num_canaldatos = [
    52, 51, 50, 49, 44, 43, 42, 41, 36, 35, 34, 33, 60, 59, 58, 57,
    25, 26, 27, 28, 17, 18, 19, 20, 1, 2, 3, 4, 9, 10, 11, 12,
    53, 54, 55, 56, 45, 46, 47, 48, 37, 38, 39, 40, 61, 62, 63, 64,
    32, 31, 30, 29, 24, 23, 22, 21, 8, 7, 6, 5, 16, 15, 14, 13
]

# Create mapping dictionary for easy lookup
scintillator_mapping = {
    scint: {
        'fpga': fpga,
        'datos': datos
    }
    for scint, fpga, datos in zip(num_scintillator, num_canalFPGA, num_canaldatos)
}

# Configuration for shaded periods
SHADED_PERIODS = [
    {
        'name': 'COVID Lockdown',
        'start_date': '2020-03-20',
        'end_date': '2020-06-08',
        'color': 'gray',
        'opacity': 0.2
    },
    {
        'name': 'Summer Break 2025',
        'start_date': '2025-01-01',
        'end_date': '2025-02-15',
        'color': 'orange',
        'opacity': 0.1
    },
    {
        'name': 'Summer Break 2024',
        'start_date': '2024-01-01',
        'end_date': '2024-02-15',
        'color': 'orange',
        'opacity': 0.1
    },
    {
        'name': 'Summer Break 2023',
        'start_date': '2023-01-01',
        'end_date': '2023-02-15',
        'color': 'orange',
        'opacity': 0.1
    },
    {
        'name': 'Summer Break 2022',
        'start_date': '2022-01-01',
        'end_date': '2022-02-15',
        'color': 'orange',
        'opacity': 0.1
    },
    {
        'name': 'Summer Break 2021',
        'start_date': '2021-01-01',
        'end_date': '2021-02-15',
        'color': 'orange',
        'opacity': 0.1
    },
    {
        'name': 'Summer Break 2020',
        'start_date': '2020-01-01',
        'end_date': '2020-02-15',
        'color': 'orange',
        'opacity': 0.1
    },
    {
        'name': 'Summer Break 2019',
        'start_date': '2019-01-01',
        'end_date': '2019-02-15',
        'color': 'orange',
        'opacity': 0.1
    }

    # Add more periods as needed:
    # {
    #     'name': 'Another Period',
    #     'start_date': 'YYYY-MM-DD',
    #     'end_date': 'YYYY-MM-DD',
    #     'color': 'color_name_or_hex',
    #     'opacity': 0.0 to 1.0
    # }
]

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
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the username and password.
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("😕 User not known or password incorrect")
    return False


if not check_password():
    st.stop()

# Initialize or get the language from session state
if 'language' not in st.session_state:
    st.session_state['language'] = 'es'  # Default language is Spanish

# Function to switch language
def switch_language():
    st.session_state['language'] = 'en' if st.session_state['language'] == 'es' else 'es'    

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

# Set page configuration
st.set_page_config(
    page_title=translations['page_title'][st.session_state['language']],
    page_icon=":wrench:",
    layout="wide",
)

col_title, col_button = st.columns((0.8, 0.2))
with col_title:
    st.title(translations['header_title'][st.session_state['language']])
with col_button:
    st.button(translations['button_text'][st.session_state['language']], on_click=switch_language)  # Button to switch language
st.divider()

tab_map, tab_field, tab_acq, tab_stats, tab_umd_details = st.tabs([
    translations['tab_map_title'][st.session_state['language']],
    translations['tab_field_title'][st.session_state['language']],
    translations['tab_acq_title'][st.session_state['language']],
    translations['tab_stats_title'][st.session_state['language']],
    'UMD Details'  # We'll add this to translations later
])

with tab_map:
    components.iframe("https://amiga-map.ahuekna.org.ar", height=900)

with tab_field: 
    
    conn = st.connection("nico", type=GSheetsConnection)

    # Specify the column indices you want to select
    column_indices = [1, 2, 3, 5, 6, 54]

    # Rename the columns
    new_column_names = ['content', 'position(id)', 'type', 'team', 'date', 'photos']

    df = conn.read(usecols=column_indices, names=new_column_names,
                   parse_dates=['date'],
                   dayfirst=True,
                   header=0)

    # Extract name and id from position(id) column
    df[['name', 'id']] = df['position(id)'].str.extract(r'([\w\s.]+)\s*\(id=(\d+)\)', expand=True)

    # Format the date column (keep original date column for sorting)
    df['formatted_date'] = df['date'].dt.strftime('%Y-%m-%d')

    # Drop the position(id) column
    df = df.drop(columns=['position(id)'])

    # Get min and max dates
    if len(df) > 0:
        min_date = df['date'].min()
        max_date = df['date'].max()
    else:
        min_date = datetime.now()
        max_date = datetime.now()

    # Create Streamlit widgets for filtering
    empty1, colA, empty2, colB, empty3 = st.columns((0.1, 1, 0.1, 1, 0.1))

    with colA:
        st.header(translations['filters_header'][st.session_state['language']], divider="grey")
        
        # Add search box in the filters section
        st.markdown(f"### {translations['search_label'][st.session_state['language']]}")
        search_query = st.text_input(
            label=translations['search_placeholder'][st.session_state['language']],
            key="search_tab_field",
            label_visibility="collapsed"
        )

        # Reset index before applying search to ensure proper alignment
        df = df.reset_index(drop=True)
        
        if search_query:
            search_mask = search_dataframe(df, search_query)
            df_filtered = df[search_mask].copy()  # Create a copy to avoid SettingWithCopyWarning
            if len(df_filtered) == 0:
                st.warning(translations['no_results'][st.session_state['language']].format(search_query))
            else:
                st.info(translations['search_results'][st.session_state['language']].format(len(df_filtered), search_query))
                df = df_filtered  # Only update df if there are matches

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### {translations['position_label'][st.session_state['language']]}")
            name_dropdown = st.selectbox(translations['position_label'][st.session_state['language']],
                                         np.sort(df['name'].unique()), index=None,
                                         placeholder=translations['position_placeholder'][st.session_state['language']],
                                         key="name_dropdown_1", label_visibility="collapsed")

        if name_dropdown is None:
            filtered_by_name = df
        else:
            filtered_by_name = df[(df['name'] == name_dropdown)]

        with col2:
            st.markdown(f"### {translations['type_label'][st.session_state['language']]}")
            type_dropdown = st.selectbox(translations['type_label'][st.session_state['language']],
                                         filtered_by_name['type'].unique(), index=None,
                                         placeholder=translations['type_placeholder'][st.session_state['language']],
                                         key="type_dropdown_1", label_visibility="collapsed")

        if type_dropdown is None:
            filtered_by_type = filtered_by_name
        else:
            filtered_by_type = filtered_by_name[(filtered_by_name['type'] == type_dropdown)]

        st.markdown(f"### {translations['date_interval_label'][st.session_state['language']]}")

        col3, col4 = st.columns(2)

        with col3:
            start_date = st.date_input(translations['from_label'][st.session_state['language']],
                                       value=min_date, key="start_date_1")
        with col4:
            end_date = st.date_input(translations['to_label'][st.session_state['language']],
                                     value=max_date, key="end_date_1")

        if start_date is None and end_date is None:
            filtered_by_date = filtered_by_type

        if start_date is not None and end_date is not None:
            filtered_by_date = filtered_by_type[(filtered_by_type['formatted_date'] >= start_date.strftime('%Y-%m-%d')) & (filtered_by_type['formatted_date'] <= end_date.strftime('%Y-%m-%d'))]

        final_table = filtered_by_date[['formatted_date', 'name', 'id', 'type', 'content', 'photos']].sort_values(by='formatted_date', ascending=False)
        selections = ["name_dropdown", "type_dropdown"]

        def clear_all():
            for i in selections:
                st.session_state[f'{i}'] = None
            st.session_state['start_date'] = min_date
            st.session_state['end_date'] = max_date

        st.button(translations['clear_filters'][st.session_state['language']], on_click=clear_all)

        st.header(translations['results_header'][st.session_state['language']], divider="grey")
        st.caption(translations['click_report'][st.session_state['language']])

        def photo_formatter(photo_links):
            if isinstance(photo_links, str):
                links = re.findall(r'https://drive\.google\.com/open\?id=[^\s,]+', photo_links)
                return translations['contains_photos'][st.session_state['language']].format(len(links)) if links else ""
            return ""

        # Create a new column for the photo indicator
        final_table['photo_indicator'] = final_table['photos'].apply(photo_formatter)

        selection = st.dataframe(final_table, on_select="rerun", selection_mode="single-row",
                                 height=200 if len(df) > 5 else None, width=800, column_config={
                                     "content": None,
                                     "photos": None,  # Hide the original photos column
                                     "photo_indicator": st.column_config.Column(
                                         "Fotos",
                                         width="small",
                                         help="📷 indicates available photos"
                                     ),
                                     "formatted_date": "Fecha",
                                     "type": "Tipo de Salida",
                                     "name": "Posición"
                                 }, hide_index=True)

        # Function to clean up the URL
        def clean_url(url):
            return url.rstrip(',')  # Remove trailing comma if present

        # Function to get image content from Google Drive link
        def get_image_content(drive_link):
            clean_link = clean_url(drive_link)
            file_id = clean_link.split('=')[-1]
            url = f"https://drive.google.com/uc?export=view&id={file_id}"
            response = requests.get(url, stream=True)
            if response.status_code == 404:
                raise Exception("Image not found. It may have been deleted or is not publicly accessible.")
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))

        with colB:
            st.header(translations['report_header'][st.session_state['language']], divider="grey")
            if len(selection["selection"]["rows"]) > 0:
                selected_row = final_table.iloc[selection["selection"]["rows"]]
                md_content = selected_row["content"].values[0]
                with st.container():
                    st.write(md_content)

                # Add photo visualization
                photos = selected_row["photos"].values[0]
                if photos and isinstance(photos, str):
                    photo_links = re.findall(r'(https://drive\.google\.com/open\?id=[^\s,]+)', photos)
                    photo_links = [clean_url(link) for link in photo_links]

                    if photo_links:
                        st.subheader(translations['photos_header'][st.session_state['language']])

                        for link in photo_links:
                            with st.spinner(translations['loading_image'][st.session_state['language']]):
                                try:
                                    img = get_image_content(link)

                                    if img.mode == 'RGBA':
                                        img = img.convert('RGB')

                                    img_byte_arr = io.BytesIO()
                                    img.save(img_byte_arr, format='JPEG')
                                    img_byte_arr = img_byte_arr.getvalue()

                                    st.image(img_byte_arr, use_column_width=True)

                                except Exception as e:
                                    st.error(f"{translations['image_load_error'][st.session_state['language']]} {str(e)}")
                                    st.markdown(f"[{translations['image_link'][st.session_state['language']]}]({link})")

                                time.sleep(0.1)
                    else:
                        st.info(translations['no_photos'][st.session_state['language']])

with tab_acq:  
    conn = st.connection("belu", type=GSheetsConnection)

    # Specify the column indices you want to select
    column_indices = [0, 2, 3, 6, 9, 11, 12]

    # Rename the columns
    new_column_names = ['position', 'modules', 'date_report',
                        'summary', 'team', 'status', 'report']

    df = conn.read(usecols=column_indices, names=new_column_names,
                   parse_dates=['date_report'],
                   dayfirst=True,
                   header=0)

    # Format the date column
    df['date_report'] = df['date_report'].dt.strftime('%Y-%m-%d')
    df['date'] = df['date_report']

    # Get min and max dates before any filtering
    if len(df) > 0:
        min_date = datetime.strptime(df['date_report'].min(), '%Y-%m-%d')
        max_date = datetime.strptime(df['date_report'].max(), '%Y-%m-%d')
    else:
        min_date = datetime.now()
        max_date = datetime.now()

    # Create Streamlit widgets for filtering
    empty1, colA, empty2, colB, empty3 = st.columns((0.1, 1, 0.1, 1, 0.1))

    with colA:
        st.header(translations['filters_header'][st.session_state['language']], divider="grey")
        
        # Add search box in the filters section
        st.markdown(f"### {translations['search_label'][st.session_state['language']]}")
        search_query = st.text_input(
            label=translations['search_placeholder'][st.session_state['language']],
            key="search_tab_acq",
            label_visibility="collapsed"
        )

        # Reset index before applying search to ensure proper alignment
        df = df.reset_index(drop=True)
        
        if search_query:
            search_mask = search_dataframe(df, search_query)
            df_filtered = df[search_mask].copy()  # Create a copy to avoid SettingWithCopyWarning
            if len(df_filtered) == 0:
                st.warning(translations['no_results'][st.session_state['language']].format(search_query))
            else:
                st.info(translations['search_results'][st.session_state['language']].format(len(df_filtered), search_query))
                df = df_filtered  # Only update df if there are matches

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"### {translations['position_label'][st.session_state['language']]}")
            name_dropdown = st.selectbox(translations['position_label'][st.session_state['language']],
                                         np.sort(df['position'].unique()), index=None,
                                         placeholder=translations['position_placeholder'][st.session_state['language']],
                                         key="name_dropdown_2", label_visibility="collapsed")

        if name_dropdown is None:
            filtered_by_name = df
        else:
            filtered_by_name = df[(df['position'] == name_dropdown)]

            
        with col2:
            st.markdown(f"### {translations['status_label'][st.session_state['language']]}")
            type_dropdown = st.selectbox(translations['status_label'][st.session_state['language']],
                                            filtered_by_name['status'].unique(), index=None,
                                            placeholder=translations['status_placeholder'][st.session_state['language']],
                                            key="type_dropdown_2", label_visibility="collapsed")

        with col3:
            st.markdown(f"### {translations['team_label'][st.session_state['language']]}")
            team_dropdown = st.selectbox(translations['team_label'][st.session_state['language']],
                                            np.sort(filtered_by_name['team'].unique()), index=None,
                                            placeholder=translations['team_placeholder'][st.session_state['language']],
                                            key="team_dropdown_2", label_visibility="collapsed")

        if type_dropdown is None:
            filtered_by_type = filtered_by_name
        else:
            filtered_by_type = filtered_by_name[(filtered_by_name['status'] == type_dropdown)]

        if team_dropdown is None:
            filtered_by_team = filtered_by_type
        else:
            filtered_by_team = filtered_by_type[(filtered_by_type['team'] == team_dropdown)]

        st.markdown(f"### {translations['date_interval_label'][st.session_state['language']]}")

        col4, col5 = st.columns(2)

        with col4:
            start_date = st.date_input(translations['from_label'][st.session_state['language']],
                                       value=min_date, key="start_date_2")
        with col5:
            end_date = st.date_input(translations['to_label'][st.session_state['language']],
                                     value=max_date, key="end_date_2")

        if start_date is None and end_date is None:
            filtered_by_date = filtered_by_team

        if start_date is not None and end_date is not None:
            filtered_by_date = filtered_by_team[(filtered_by_team['date'] >= start_date.strftime('%Y-%m-%d')) & (filtered_by_team['date'] <= end_date.strftime('%Y-%m-%d'))]

        final_table = filtered_by_date[['date','position', 'modules', 'summary', 'status', 'team', 'report']].sort_values('status',ascending=True)
        final_table_colA = final_table.loc[final_table['status']!='Complete']
        
        selections = ["name_dropdown", "type_dropdown", "team_dropdown"]
        def clear_all():
            for i in selections:
                st.session_state[f'{i}'] = None
            st.session_state['start_date'] = min_date
            st.session_state['end_date'] = max_date

        st.button(translations['clear_filters'][st.session_state['language']], on_click=clear_all,key='button_2')

        st.header(translations['results_header'][st.session_state['language']], divider="grey")

        st.caption(translations['click_report'][st.session_state['language']])
    
        selection = st.dataframe(final_table_colA, on_select="rerun", selection_mode="single-row",
                                 height=200 if len(final_table_colA) > 5 else None, width=800, 
                                 column_config={
                                     "report": None,
                                     "date": "Date",
                                     "modules": "Modules",
                                     "position": "Position",
                                     "summary": "Summary of issue",
                                     "status":"Current status"},
                                 hide_index=True)

        with colB:
            st.header(translations['report_header'][st.session_state['language']], divider="grey")
            if len(selection["selection"]["rows"]) > 0:
                selected_row = final_table_colA.iloc[selection["selection"]["rows"]]            
                full_selection = final_table.loc[final_table['position']==selected_row['position'].values[0]]
                full_selection = full_selection.loc[full_selection['summary']==selected_row['summary'].values[0]]
                
                

                if len(full_selection) > 1:                    
                    """ There are several reports about this issue. Choose which one you want to see:"""
                    selection_colB = st.dataframe(full_selection, on_select="rerun", selection_mode="single-row",
                                     #height=200 if len(df) > 5 else None, width=800, 
                                     width=800, 
                                     column_config={
                                         "report": None,
                                         "date": "Date",
                                         "modules": "Modules",
                                         "position": "Position",
                                         "summary": "Summary of issue",
                                         "status":"Current status"},
                                     hide_index=True,key='selection_colB')
                    
                    if len(selection_colB["selection"]["rows"]) > 0:
                        new_selected_row = full_selection.iloc[selection_colB["selection"]["rows"]]
                        md_content = new_selected_row["report"].values[0]
                        with st.container():
                            st.write(md_content)
                else:
                    md_content = selected_row["report"].values[0]
                    with st.container():
                        st.write(md_content)

with tab_stats:
    # Stock dataframe - Assembly progress
    conn_stock = st.connection("stats_stock", type=GSheetsConnection)
    df_stock = conn_stock.read(
        usecols=[0, 1],
        names=['date', 'UMD_number'],
        header=None,
        dayfirst=True,
        skiprows=9
    ).dropna()  # Remove rows without cumulative numbers
    
    # Convert and clean stock data
    df_stock['UMD_number'] = df_stock['UMD_number'].astype(int)
    df_stock['date'] = pd.to_datetime(df_stock['date'], format="%d/%m/%y")
    
    # Installation history dataframe
    conn_historial = st.connection("stats_historial", type=GSheetsConnection)
    df_historial = conn_historial.read(
        usecols=[2, 3, 6, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 31, 32, 33],  # name, id, install_date, id_m101, id_m102, id_m103, RotationAngle_m101, RadioDistance_m101, PositionAngle_m101, RotationAngle_m102, RadioDistance_m102, PositionAngle_m102, RotationAngle_m103, RadioDistance_m103, PositionAngle_m103
        names=['position', 'id', 'install_date', 
        'id_m101', 'RotationAngle_m101', 'RadioDistance_m101', 'PositionAngle_m101',
        'id_m102', 'RotationAngle_m102', 'RadioDistance_m102', 'PositionAngle_m102',
        'id_m103', 'RotationAngle_m103', 'RadioDistance_m103', 'PositionAngle_m103',
        'ekit_m101', 'ekit_m102', 'ekit_m103'],
        header=None,
        skiprows=7
    )
    
    # Clean installation data
    df_historial = df_historial[~df_historial["install_date"].str.contains("-", na=False)]  # Remove not installed
    df_historial['install_date'] = pd.to_datetime(df_historial['install_date'])  # Convert install_date to datetime
    df_historial = df_historial.dropna(subset=['install_date'])  # Remove rows without install date
    df_historial['id'] = df_historial['id'].astype(int)
    
    # Count only valid modules (starting with "M-")
    def is_valid_module(x):
        return isinstance(x, str) and x.startswith('M-')
    
    # Apply the validation to each module column
    module_columns = ['id_m101', 'id_m102', 'id_m103']
    for col in module_columns:
        df_historial[f'{col}_valid'] = df_historial[col].apply(is_valid_module)
    
    # Count valid modules per installation
    df_historial['modules_installed'] = df_historial[[f'{col}_valid' for col in module_columns]].sum(axis=1)
    df_historial = df_historial.sort_values(by='install_date')
    
    # Display metrics
    st.markdown(f"## {translations['stats_header'][st.session_state['language']]}")
    
    # Time period filter
    time_filters = {
        'All Time': None,
        'Last Month': pd.DateOffset(months=1),
        'Last Quarter': pd.DateOffset(months=3),
        'Last Year': pd.DateOffset(years=1),
        'Q4 2024': (pd.Timestamp('2024-10-01'), pd.Timestamp('2024-12-31')),
        'Q3 2024': (pd.Timestamp('2024-07-01'), pd.Timestamp('2024-09-30')),
        'Q2 2024': (pd.Timestamp('2024-04-01'), pd.Timestamp('2024-06-30')),
        'Q1 2024': (pd.Timestamp('2024-01-01'), pd.Timestamp('2024-03-31')),
        'Q4 2023': (pd.Timestamp('2023-10-01'), pd.Timestamp('2023-12-31')),
        'Q3 2023': (pd.Timestamp('2023-07-01'), pd.Timestamp('2023-09-30')),
        'Q2 2023': (pd.Timestamp('2023-04-01'), pd.Timestamp('2023-06-30')),
        'Q1 2023': (pd.Timestamp('2023-01-01'), pd.Timestamp('2023-03-31')),
    }
    
    # Create two columns for filter and date range
    filter_col, _ = st.columns([1, 2])
    
    with filter_col:
        selected_filter = st.selectbox(
            translations['stats_time_filter'][st.session_state['language']],
            options=list(time_filters.keys()),
            format_func=lambda x: translations[f'stats_filter_{x.lower().replace(" ", "_") if x != "All Time" else "all_time"}'][st.session_state['language']]
        )
        if time_filters[selected_filter] is not None:
            if isinstance(time_filters[selected_filter], pd.DateOffset):
                cutoff_date = pd.Timestamp.now() - time_filters[selected_filter]
                st.info(f"{cutoff_date.strftime('%Y-%m-%d')} → {pd.Timestamp.now().strftime('%Y-%m-%d')}")
            else:
                start_date, end_date = time_filters[selected_filter]
                st.info(f"{start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
    
 
    # Apply time filter to data
    if time_filters[selected_filter] is not None:
        if isinstance(time_filters[selected_filter], pd.DateOffset):
            # For relative periods (Last Month, Last Quarter, Last Year)
            cutoff_date = pd.Timestamp.now() - time_filters[selected_filter]
            current_max = df_stock[df_stock['date'] > cutoff_date]['UMD_number'].max()
            previous_max = df_stock[df_stock['date'] <= cutoff_date]['UMD_number'].max()
            
            # Handle NaN values and calculate delta
            if pd.isna(current_max):
                assembled_delta = 0  # No UMDs assembled in current period
            else:
                current_max = int(current_max)
                previous_max = 0 if pd.isna(previous_max) else int(previous_max)
                assembled_delta = current_max - previous_max if current_max > previous_max else 0
            
            installed_delta = int(df_historial[df_historial['install_date'] > cutoff_date]['modules_installed'].sum())
            positions_delta = df_historial[df_historial['install_date'] > cutoff_date]['position'].nunique()
        else:
            # For specific quarters
            start_date, end_date = time_filters[selected_filter]
            assembled_delta = int(df_stock[(df_stock['date'] >= start_date) & (df_stock['date'] <= end_date)]['UMD_number'].max() or 0) - int(df_stock[df_stock['date'] < start_date]['UMD_number'].max() or 0)
            installed_delta = int(df_historial[(df_historial['install_date'] >= start_date) & (df_historial['install_date'] <= end_date)]['modules_installed'].sum())
            positions_delta = df_historial[(df_historial['install_date'] >= start_date) & (df_historial['install_date'] <= end_date)]['position'].nunique()
    else:
        # For all time, no deltas
        assembled_delta = None
        installed_delta = None
        positions_delta = None

    # Calculate overall metrics (these never change with filters)
    total_assembled = int(df_stock['UMD_number'].max() if not df_stock.empty else 0)
    total_installed = int(df_historial['modules_installed'].sum())
    installation_positions = df_historial['position'].nunique() + 4

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        label=translations['stats_assembled'][st.session_state['language']],
        value=total_assembled,
        delta=f"+{assembled_delta}" if assembled_delta and assembled_delta > 0 else str(assembled_delta) if assembled_delta and assembled_delta != 0 else None
    )

    col2.metric(
        label=translations['stats_installed'][st.session_state['language']],
        value=total_installed,
        delta=f"+{installed_delta}" if installed_delta and installed_delta > 0 else str(installed_delta) if installed_delta and installed_delta != 0 else None
    )

    col3.metric(
        label=translations['stats_positions'][st.session_state['language']],
        value=installation_positions,
        delta=f"+{positions_delta}" if positions_delta and positions_delta > 0 else str(positions_delta) if positions_delta and positions_delta != 0 else None
    )

    col4.metric(
        label=translations['stats_rate'][st.session_state['language']],
        value=f"{(installation_positions/73 *100):.1f}%"
    )

    # Plots
    st.markdown(f"### {translations['stats_plots_title'][st.session_state['language']]}")

    # Create a date range from min to max date of complete dataset
    if not df_stock.empty and not df_historial.empty:
        date_range = pd.date_range(
            start=min(df_stock['date'].min(), df_historial['install_date'].min()),
            end=max(df_stock['date'].max(), df_historial['install_date'].max()),
            freq='D'
        )
        
        # Prepare data for combined view
        df_combined = pd.DataFrame({'date': date_range})
        
        # Add assembly data
        df_combined = pd.merge_asof(
            df_combined,
            df_stock[['date', 'UMD_number']],
            on='date',
            direction='backward'
        )
        
        # Count cumulative installations per date
        installation_counts = df_historial.groupby('install_date')['modules_installed'].sum().reset_index()
        installation_counts.columns = ['date', 'daily_installations']
        installation_counts['cumulative_installations'] = installation_counts['daily_installations'].cumsum()
        
        # Add installation data
        df_combined = pd.merge_asof(
            df_combined,
            installation_counts[['date', 'cumulative_installations']],
            on='date',
            direction='backward'
        )
        
        # Fill NaN values with previous values or 0
        df_combined = df_combined.fillna(method='ffill').fillna(0)

        # Create the combined plot
        fig = px.line(df_combined,
                    x='date',
                    y=['UMD_number', 'cumulative_installations'],
                    title=translations['stats_combined_title'][st.session_state['language']],
                    labels={
                        'date': 'Date',
                        'value': 'Number of UMDs',
                        'variable': 'Type'
                    })
        
        # Add shaded periods
        for period in SHADED_PERIODS:
            fig.add_vrect(
                x0=period['start_date'],
                x1=period['end_date'],
                fillcolor=period['color'],
                opacity=period['opacity'],
                layer="below",
                line_width=0,
                name=period["name"],
                visible=True,
                showlegend=True
            )
        
        fig.update_traces(mode='lines+markers')
        fig.update_layout(
            title=translations['stats_combined_title'][st.session_state['language']],
            yaxis_title="Number of UMDs",
            legend_title="Type",
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )
        
        # Update legend labels
        newnames = {'UMD_number': 'Assembled', 'cumulative_installations': 'Installed'}
        fig.for_each_trace(lambda t: t.update(name=newnames[t.name] if t.name in newnames else t.name))
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available")

with tab_umd_details:
    conn = st.connection("umd_details", type=GSheetsConnection)
    
    # Get data from the spreadsheet
    df_umd = conn.read(usecols=[0, 2])  # Columns A and C
    df_umd.columns = ['UMD_ID', 'Details']
    
    # Get installation history data
    conn_historial = st.connection("stats_historial", type=GSheetsConnection)
    df_historial = conn_historial.read(
        usecols=[2, 3, 6, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 31, 32, 33],  # name, id, install_date, id_m101, id_m102, id_m103, RotationAngle_m101, RadioDistance_m101, PositionAngle_m101, RotationAngle_m102, RadioDistance_m102, PositionAngle_m102, RotationAngle_m103, RadioDistance_m103, PositionAngle_m103
        names=['position', 'id', 'install_date', 
        'id_m101', 'RotationAngle_m101', 'RadioDistance_m101', 'PositionAngle_m101',
        'id_m102', 'RotationAngle_m102', 'RadioDistance_m102', 'PositionAngle_m102',
        'id_m103', 'RotationAngle_m103', 'RadioDistance_m103', 'PositionAngle_m103',
        'ekit_m101', 'ekit_m102', 'ekit_m103'],
        header=None,
        skiprows=7
    )
    
    # Clean installation data
    df_historial = df_historial[~df_historial["install_date"].str.contains("-", na=False)]  # Remove not installed
    df_historial['install_date'] = pd.to_datetime(df_historial['install_date'])  # Convert install_date to datetime
    df_historial = df_historial.dropna(subset=['install_date'])  # Remove rows without install date
    df_historial['id'] = df_historial['id'].astype(int)
    
    # Process details to extract problematic scintillators for each row
    def extract_scints(details: Optional[str]) -> List[int]:
        if pd.isna(details):
            return []
        matches = re.findall(r'\d+(?=\s*\()', str(details))
        return [int(m) for m in matches]
    
    df_umd['Problematic Scints'] = df_umd['Details'].apply(extract_scints)
    
    def create_umd_position_plot(umd_info: pd.Series, selected_umd: str) -> go.Figure:
        # Constants
        circle_diameter = 3.6  # meters
        margin_diameter = 13.6  # meters
        umd_width = 1.4  # meters
        umd_height = 9.0  # meters
        
        # Create figure
        fig = go.Figure()
        
        # Add central circle (tank)
        theta = np.linspace(0, 2*np.pi, 100)
        x_circle = (circle_diameter/2) * np.cos(theta)
        y_circle = (circle_diameter/2) * np.sin(theta)
        fig.add_trace(go.Scatter(
            x=x_circle, y=y_circle,
            fill="toself",
            fillcolor="rgba(255,200,200,0.5)",
            line=dict(color="rgba(255,200,200,0.8)"),
            name="Tank"
        ))
        
        # Add margin circle
        x_margin = (margin_diameter/2) * np.cos(theta)
        y_margin = (margin_diameter/2) * np.sin(theta)
        fig.add_trace(go.Scatter(
            x=x_margin, y=y_margin,
            line=dict(color="rgba(200,200,200,0.5)"),
            name="Margin"
        ))
        
        # Add UMDs
        for module in ['101', '102', '103']:
            # Skip if module ID is "-"
            if umd_info[f'id_m{module}'] == "-":
                continue
                
            rd = float(umd_info[f'RadioDistance_m{module}'].replace(',', '.'))
            pa = np.radians(float(umd_info[f'PositionAngle_m{module}']))
            ra = np.radians(float(umd_info[f'RotationAngle_m{module}']))
            
            # Calculate center position
            x = -rd * np.sin(pa)
            y = -rd * np.cos(pa)
            
            # Create rectangle corners (rotated)
            corners_x = []
            corners_y = []
            
            # Calculate corners of rectangle
            for dx, dy in [(-umd_width/2, -umd_height/2), 
                        (umd_width/2, -umd_height/2),
                        (umd_width/2, umd_height/2),
                        (-umd_width/2, umd_height/2),
                        (-umd_width/2, -umd_height/2)]:  # Close the shape
                # Rotate point by RA
                rx = -dx * np.cos(ra) - dy * np.sin(ra)
                ry = dx * np.sin(ra) - dy * np.cos(ra)
                # Translate to position
                corners_x.append(x + rx)
                corners_y.append(y + ry)
            
            # Set color based on whether this is the selected UMD
            is_selected = umd_info[f'id_m{module}'] == selected_umd
            fillcolor = "rgba(255,255,255,0.8)" if is_selected else "rgba(200,200,255,0.5)"
            line_width = 2 if is_selected else 1
            
            # Add UMD rectangle
            fig.add_trace(go.Scatter(
                x=corners_x, y=corners_y,
                fill="toself",
                fillcolor=fillcolor,
                line=dict(color="black", width=line_width),
                name=f"UMD {umd_info[f'id_m{module}']}",
                hovertext=f"UMD {umd_info[f'id_m{module}']}<br>RD: {rd}m<br>PA: {umd_info[f'PositionAngle_m{module}']}°<br>RA: {umd_info[f'RotationAngle_m{module}']}°",
                showlegend=False
            ))

            fig.add_shape(
                type="circle",
                xref="x",
                yref="y",
                x0=x-0.3,
                y0=y-0.3,
                x1=x+0.3,
                y1=y+0.3,
                # line_color="blue",
                fillcolor="lightblue",
                opacity=0.7
            )
        
        # Add North indicator
        fig.add_trace(go.Scatter(
            x=[0, 0],
            y=[circle_diameter/2 + 0.5, circle_diameter/2 + 1.5],
            mode='lines',
            line=dict(color="gray"),
            name="North"
        ))
        fig.add_annotation(
            x=0, y=circle_diameter/2 + 2,
            text="N",
            showarrow=False,
            font=dict(size=14)
        )
        
        # Update layout
        fig.update_layout(
            showlegend=True,
            width=600,
            height=600,
            xaxis=dict(
                scaleanchor="y",
                scaleratio=1,
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False
            ),
            hovermode='closest'
        )
        
        return fig

    # Create two columns
    col1, col2 = st.columns([0.25, 0.75])
    
    with col1:
        st.header("UMD Selection", divider="grey")
        selected_umd = st.selectbox(
            "Select UMD",
            options=df_umd['UMD_ID'].tolist(),
            index=None,
            placeholder="Choose a UMD..."
        )
        
        if selected_umd:
            selected_row = df_umd[df_umd['UMD_ID'] == selected_umd].iloc[0]
            
            # Get installation info by searching in all module columns
            umd_info = df_historial[
                (df_historial['id_m101'] == selected_umd) |
                (df_historial['id_m102'] == selected_umd) |
                (df_historial['id_m103'] == selected_umd)
            ].iloc[0] if len(df_historial[
                (df_historial['id_m101'] == selected_umd) |
                (df_historial['id_m102'] == selected_umd) |
                (df_historial['id_m103'] == selected_umd)
            ]) > 0 else None
            
            if umd_info is not None:
                # Find which module number this UMD is
                module_num = None
                if umd_info['id_m101'] == selected_umd:
                    module_num = 101
                elif umd_info['id_m102'] == selected_umd:
                    module_num = 102
                elif umd_info['id_m103'] == selected_umd:
                    module_num = 103
                
                # Format details text for markdown
                details_display = selected_row['Details']
                if pd.isna(details_display):
                    details_display = 'No issues reported'
                else:
                    # Split by numbers followed by parentheses to separate issues
                    issues = re.findall(r'\d+\s*\([^)]+\)', details_display)
                    if issues:
                        # Format each issue as a list item
                        details_display = '\n'.join(f"- {issue.strip()}" for issue in issues)
                    else:
                        details_display = f"- {details_display}"
                    
                    # Escape any markdown special characters
                    details_display = details_display.replace('*', '\\*').replace('_', '\\_')
                
                st.markdown("""### Installation Information""")
                st.markdown(f"""
                            - **Position:** {umd_info['position']}
                            - **Installation Date:** {umd_info['install_date'].strftime('%Y-%m-%d')}
                            - **Module Position:** m-{module_num}
                            - **Electronic Kit:** {umd_info[f'ekit_m{module_num}']}
                            - **Module Details:**
                                - Rotation Angle: {umd_info[f'RotationAngle_m{module_num}']}°
                                - Radio Distance: {umd_info[f'RadioDistance_m{module_num}']} m
                                - Position Angle: {umd_info[f'PositionAngle_m{module_num}']}°
                            - **Other Modules in Position:**
                                - Module 1: {umd_info['id_m101']}
                                - Module 2: {umd_info['id_m102']}
                                - Module 3: {umd_info['id_m103']}
                            """)
                
                st.markdown("""### Issues during Assembly:""")
                st.markdown(details_display)
                
            else:
                st.warning("No installation information found for this UMD")
    
    with col2:
        if selected_umd:
            st.header("UMD Layout", divider="grey")
            # Parse details to get problematic scintillator numbers
            details_text = selected_row['Details']
            problematic_scints = []
            
            # Extract numbers from the details text if it's not empty
            if pd.notna(details_text) and details_text.strip():
                numbers = re.findall(r'\d+', details_text)
                problematic_scints = [int(num) for num in numbers]
            
            # UMD visualization parameters
            umd_width = 1.28
            scint_num = 32
            scint_width = umd_width / scint_num
            scint_length = 0.5
            scint_offset = 0.25

            # Create sample data for scintillators
            df_top = pd.DataFrame({
                'x': np.linspace(-umd_width/2, umd_width/2 - scint_width, scint_num)
            })

            df_bottom = pd.DataFrame({
                'x': np.linspace(-umd_width/2, umd_width/2 - scint_width, scint_num)
            })

            # Create the figure
            fig = go.Figure()
            
            # Add top scintillators (numbered 1-32 from left to right)
            for i in range(len(df_top)):
                scint_num = i + 1  # Numbers 1-32
                fillcolor = "red" if scint_num in problematic_scints else "white"
                
                fig.add_trace(go.Scatter(
                    x=[df_top['x'][i], df_top['x'][i], df_top['x'][i] + scint_width, df_top['x'][i] + scint_width, df_top['x'][i]],
                    y=[scint_offset, scint_offset + scint_length, scint_offset + scint_length, scint_offset, scint_offset],
                    fill="toself",
                    fillcolor=fillcolor,
                    line=dict(color="Black", width=1),
                    hoverinfo="text",
                    text=f"Scintillator: {scint_num}<br>FPGA Channel: {scintillator_mapping[scint_num]['fpga']}<br>Data Channel: {scintillator_mapping[scint_num]['datos']}",
                    showlegend=False
                ))

            # Add bottom scintillators (numbered 33-64 from right to left)
            for i in range(len(df_bottom)):
                scint_num = 64 - i  # Numbers 64-33 from right to left
                fillcolor = "red" if scint_num in problematic_scints else "white"
                
                fig.add_trace(go.Scatter(
                    x=[df_bottom['x'][i], df_bottom['x'][i], df_bottom['x'][i] + scint_width, df_bottom['x'][i] + scint_width, df_bottom['x'][i]],
                    y=[-scint_offset, -scint_offset - scint_length, -scint_offset - scint_length, -scint_offset, -scint_offset],
                    fill="toself",
                    fillcolor=fillcolor,
                    line=dict(color="Black", width=1),
                    hoverinfo="text",
                    text=f"Scintillator: {scint_num}<br>FPGA Channel: {scintillator_mapping[scint_num]['fpga']}<br>Data Channel: {scintillator_mapping[scint_num]['datos']}",
                    showlegend=False
                ))

            # Add central circle
            fig.add_shape(
                type="circle",
                xref="x",
                yref="y",
                x0=-0.15,
                y0=-0.15,
                x1=0.15,
                y1=0.15,
                # line_color="blue",
                fillcolor="lightblue",
                opacity=0.7
            )

            # Update layout
            fig.update_layout(
                xaxis=dict(
                    scaleanchor="y",
                    scaleratio=1,
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False
                ),
                width=600,
                height=800,
                showlegend=False,
                hovermode='closest',
                # plot_bgcolor='white'
            )
            
            plot_col1, plot_col2 = st.columns(2)
            
            with plot_col1:
                st.markdown("### UMD Layout")
                # fig.update_layout(
                #     width=400,
                #     height=400,
                # )
                st.plotly_chart(fig, use_container_width=True)
            
            with plot_col2:
                st.markdown("### UMD Position Plot")
                position_fig = create_umd_position_plot(umd_info, selected_umd)
                st.plotly_chart(position_fig, use_container_width=True)
