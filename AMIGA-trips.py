import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import numpy as np
from datetime import datetime
import requests
import re
from PIL import Image
import io
import time
import pandas as pd
import plotly.express as px

import hmac
from translations import lang_content

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
    page_title=lang_content['page_title'][st.session_state['language']],
    page_icon=":wrench:",
    layout="wide",
)

col_title, col_button = st.columns((0.8, 0.2))
with col_title:
    st.title(lang_content['header_title'][st.session_state['language']])
with col_button:
    st.button(lang_content['button_text'][st.session_state['language']], on_click=switch_language)  # Button to switch language
st.divider()

tab_map, tab_field, tab_acq, tab_stats = st.tabs([
    lang_content['tab_map_title'][st.session_state['language']],
    lang_content['tab_field_title'][st.session_state['language']],
    lang_content['tab_acq_title'][st.session_state['language']],
    lang_content['tab_stats_title'][st.session_state['language']]
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
        st.header(lang_content['filters_header'][st.session_state['language']], divider="grey")
        
        # Add search box in the filters section
        st.markdown(f"### {lang_content['search_label'][st.session_state['language']]}")
        search_query = st.text_input(
            label=lang_content['search_placeholder'][st.session_state['language']],
            key="search_tab_field",
            label_visibility="collapsed"
        )

        # Reset index before applying search to ensure proper alignment
        df = df.reset_index(drop=True)
        
        if search_query:
            search_mask = search_dataframe(df, search_query)
            df_filtered = df[search_mask].copy()  # Create a copy to avoid SettingWithCopyWarning
            if len(df_filtered) == 0:
                st.warning(lang_content['no_results'][st.session_state['language']].format(search_query))
            else:
                st.info(lang_content['search_results'][st.session_state['language']].format(len(df_filtered), search_query))
                df = df_filtered  # Only update df if there are matches

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### {lang_content['position_label'][st.session_state['language']]}")
            name_dropdown = st.selectbox(lang_content['position_label'][st.session_state['language']],
                                         np.sort(df['name'].unique()), index=None,
                                         placeholder=lang_content['position_placeholder'][st.session_state['language']],
                                         key="name_dropdown_1", label_visibility="collapsed")

        if name_dropdown is None:
            filtered_by_name = df
        else:
            filtered_by_name = df[(df['name'] == name_dropdown)]

        with col2:
            st.markdown(f"### {lang_content['type_label'][st.session_state['language']]}")
            type_dropdown = st.selectbox(lang_content['type_label'][st.session_state['language']],
                                         filtered_by_name['type'].unique(), index=None,
                                         placeholder=lang_content['type_placeholder'][st.session_state['language']],
                                         key="type_dropdown_1", label_visibility="collapsed")

        if type_dropdown is None:
            filtered_by_type = filtered_by_name
        else:
            filtered_by_type = filtered_by_name[(filtered_by_name['type'] == type_dropdown)]

        st.markdown(f"### {lang_content['date_interval_label'][st.session_state['language']]}")

        col3, col4 = st.columns(2)

        with col3:
            start_date = st.date_input(lang_content['from_label'][st.session_state['language']],
                                       value=min_date, key="start_date_1")
        with col4:
            end_date = st.date_input(lang_content['to_label'][st.session_state['language']],
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

        st.button(lang_content['clear_filters'][st.session_state['language']], on_click=clear_all)

        st.header(lang_content['results_header'][st.session_state['language']], divider="grey")
        st.caption(lang_content['click_report'][st.session_state['language']])

        def photo_formatter(photo_links):
            if isinstance(photo_links, str):
                links = re.findall(r'https://drive\.google\.com/open\?id=[^\s,]+', photo_links)
                return lang_content['contains_photos'][st.session_state['language']].format(len(links)) if links else ""
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
            st.header(lang_content['report_header'][st.session_state['language']], divider="grey")
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
                        st.subheader(lang_content['photos_header'][st.session_state['language']])

                        for link in photo_links:
                            with st.spinner(lang_content['loading_image'][st.session_state['language']]):
                                try:
                                    img = get_image_content(link)

                                    if img.mode == 'RGBA':
                                        img = img.convert('RGB')

                                    img_byte_arr = io.BytesIO()
                                    img.save(img_byte_arr, format='JPEG')
                                    img_byte_arr = img_byte_arr.getvalue()

                                    st.image(img_byte_arr, use_column_width=True)

                                except Exception as e:
                                    st.error(f"{lang_content['image_load_error'][st.session_state['language']]} {str(e)}")
                                    st.markdown(f"[{lang_content['image_link'][st.session_state['language']]}]({link})")

                                time.sleep(0.1)
                    else:
                        st.info(lang_content['no_photos'][st.session_state['language']])

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
        st.header(lang_content['filters_header'][st.session_state['language']], divider="grey")
        
        # Add search box in the filters section
        st.markdown(f"### {lang_content['search_label'][st.session_state['language']]}")
        search_query = st.text_input(
            label=lang_content['search_placeholder'][st.session_state['language']],
            key="search_tab_acq",
            label_visibility="collapsed"
        )

        # Reset index before applying search to ensure proper alignment
        df = df.reset_index(drop=True)
        
        if search_query:
            search_mask = search_dataframe(df, search_query)
            df_filtered = df[search_mask].copy()  # Create a copy to avoid SettingWithCopyWarning
            if len(df_filtered) == 0:
                st.warning(lang_content['no_results'][st.session_state['language']].format(search_query))
            else:
                st.info(lang_content['search_results'][st.session_state['language']].format(len(df_filtered), search_query))
                df = df_filtered  # Only update df if there are matches

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"### {lang_content['position_label'][st.session_state['language']]}")
            name_dropdown = st.selectbox(lang_content['position_label'][st.session_state['language']],
                                         np.sort(df['position'].unique()), index=None,
                                         placeholder=lang_content['position_placeholder'][st.session_state['language']],
                                         key="name_dropdown_2", label_visibility="collapsed")

        if name_dropdown is None:
            filtered_by_name = df
        else:
            filtered_by_name = df[(df['position'] == name_dropdown)]

            
        with col2:
            st.markdown(f"### {lang_content['status_label'][st.session_state['language']]}")
            type_dropdown = st.selectbox(lang_content['status_label'][st.session_state['language']],
                                            filtered_by_name['status'].unique(), index=None,
                                            placeholder=lang_content['status_placeholder'][st.session_state['language']],
                                            key="type_dropdown_2", label_visibility="collapsed")

        with col3:
            st.markdown(f"### {lang_content['team_label'][st.session_state['language']]}")
            team_dropdown = st.selectbox(lang_content['team_label'][st.session_state['language']],
                                            np.sort(filtered_by_name['team'].unique()), index=None,
                                            placeholder=lang_content['team_placeholder'][st.session_state['language']],
                                            key="team_dropdown_2", label_visibility="collapsed")

        if type_dropdown is None:
            filtered_by_type = filtered_by_name
        else:
            filtered_by_type = filtered_by_name[(filtered_by_name['status'] == type_dropdown)]

        if team_dropdown is None:
            filtered_by_team = filtered_by_type
        else:
            filtered_by_team = filtered_by_type[(filtered_by_type['team'] == team_dropdown)]

        st.markdown(f"### {lang_content['date_interval_label'][st.session_state['language']]}")

        col4, col5 = st.columns(2)

        with col4:
            start_date = st.date_input(lang_content['from_label'][st.session_state['language']],
                                       value=min_date, key="start_date_2")
        with col5:
            end_date = st.date_input(lang_content['to_label'][st.session_state['language']],
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

        st.button(lang_content['clear_filters'][st.session_state['language']], on_click=clear_all,key='button_2')

        st.header(lang_content['results_header'][st.session_state['language']], divider="grey")

        st.caption(lang_content['click_report'][st.session_state['language']])
    
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
            st.header(lang_content['report_header'][st.session_state['language']], divider="grey")
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
        usecols=[2, 3, 6, 11, 15, 19],  # name, id, install_date, id_m101, id_m102, id_m103
        names=['position', 'id', 'install_date', 'id_m101', 'id_m102', 'id_m103'],
        header=None,
        skiprows=7
    )
    
    # Clean installation data
    df_historial = df_historial[~df_historial["install_date"].str.contains("-", na=False)]  # Remove not installed
    df_historial = df_historial.dropna(subset=['install_date'])  # Remove rows without install date
    df_historial['id'] = df_historial['id'].astype(int)
    df_historial['install_date'] = pd.to_datetime(df_historial['install_date'], format="%d/%m/%y")
    
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
    st.markdown(f"## {lang_content['stats_header'][st.session_state['language']]}")
    
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
    filter_col, date_range_col = st.columns([1, 2])
    
    with filter_col:
        selected_filter = st.selectbox(
            lang_content['stats_time_filter'][st.session_state['language']],
            options=list(time_filters.keys()),
            format_func=lambda x: lang_content[f'stats_filter_{x.lower().replace(" ", "_") if x != "All Time" else "all_time"}'][st.session_state['language']]
        )
    
    with date_range_col:
        if time_filters[selected_filter] is not None:
            if isinstance(time_filters[selected_filter], pd.DateOffset):
                cutoff_date = pd.Timestamp.now() - time_filters[selected_filter]
                st.text(f"{cutoff_date.strftime('%Y-%m-%d')} → {pd.Timestamp.now().strftime('%Y-%m-%d')}")
            else:
                start_date, end_date = time_filters[selected_filter]
                st.text(f"{start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}")
    
    # Apply time filter to data
    if time_filters[selected_filter] is not None:
        if isinstance(time_filters[selected_filter], pd.DateOffset):
            # For relative periods (Last Month, Last Quarter, Last Year)
            cutoff_date = pd.Timestamp.now() - time_filters[selected_filter]
            assembled_delta = int(df_stock[df_stock['date'] > cutoff_date]['UMD_number'].max() or 0) - int(df_stock[df_stock['date'] <= cutoff_date]['UMD_number'].max() or 0)
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
        label=lang_content['stats_assembled'][st.session_state['language']],
        value=total_assembled,
        delta=f"+{assembled_delta}" if assembled_delta and assembled_delta > 0 else str(assembled_delta) if assembled_delta and assembled_delta != 0 else None
    )

    col2.metric(
        label=lang_content['stats_installed'][st.session_state['language']],
        value=total_installed,
        delta=f"+{installed_delta}" if installed_delta and installed_delta > 0 else str(installed_delta) if installed_delta and installed_delta != 0 else None
    )

    col3.metric(
        label=lang_content['stats_positions'][st.session_state['language']],
        value=installation_positions,
        delta=f"+{positions_delta}" if positions_delta and positions_delta > 0 else str(positions_delta) if positions_delta and positions_delta != 0 else None
    )

    col4.metric(
        label=lang_content['stats_rate'][st.session_state['language']],
        value=f"{(installation_positions/73 *100):.1f}%"
    )

    # Combined view
    st.markdown(f"### {lang_content['stats_combined_title'][st.session_state['language']]}")

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
                    title=lang_content['stats_combined_title'][st.session_state['language']],
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
            title=lang_content['stats_combined_title'][st.session_state['language']],
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