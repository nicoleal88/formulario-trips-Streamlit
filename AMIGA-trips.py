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

import hmac


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

# Language dependent content
lang_content = {
    'es': {
        'page_title': "Operaciones y monitoreo - AMIGA",
        'header_title': "Operaciones y monitoreo - AMIGA",
        'tab1_title': "Mapa",
        'tab2_title': "Adquisición de datos",
        'tab3_title': "Salidas al campo",
        'filters_header': "Filtros",
        'position_label': "Posición:",
        'position_placeholder': "Seleccionar posición",
        'status_label': "Estado:",
        'status_placeholder': "Seleccionar estado del problema",
        'team_label': "Equipo:",
        'team_placeholder': "Seleccionar equipo",
        'type_label': "Tipo de salida:",
        'type_placeholder': "Seleccionar tipo de salida",
        'date_interval_label': "Intervalo de fechas:",
        'from_label': "Desde:",
        'to_label': "Hasta:",
        'clear_filters': "Limpiar filtros",
        'results_header': "Resultados",
        'click_report': "⬇ Click para ver el reporte de la salida",
        'report_header': "Reporte",
        'button_text': "Switch to English :uk:",
        'photos_header': "Fotos",
        'no_photos': "No hay fotos disponibles para esta entrada.",
        'loading_image': "Cargando imagen...",
        'image_load_error': "No se pudo cargar la imagen:",
        'image_link': "Enlace a la imagen",
        'contains_photos': "Contiene {} 📷",
    },
    'en': {
        'page_title': "Operations and monitoring - UMD",
        'header_title': "Operations and monitoring - UMD",
        'tab1_title': "Map",
        'tab2_title': "Data Acquisition",
        'tab3_title': "Field trips",
        'filters_header': "Filters",
        'position_label': "Position:",
        'position_placeholder': "Select position",
        'status_label': "Status:",
        'status_placeholder': "Select status of the issue",
        'team_label': "Team:",
        'team_placeholder': "Select team",
        'type_label': "Field Work Type:",
        'type_placeholder': "Select Field Work Type",
        'date_interval_label': "Date Range:",
        'from_label': "From:",
        'to_label': "To:",
        'clear_filters': "Clear filters",
        'results_header': "Results",
        'click_report': "⬇ Click to view the trip report",
        'report_header': "Report",
        'button_text': "Cambiar a Español 🇦🇷",
        'photos_header': "Photos",
        'no_photos': "No photos available for this entry.",
        'loading_image': "Loading image...",
        'image_load_error': "Failed to load image:",
        'image_link': "Link to image",
        'contains_photos': "Contains {} 📷",
    }
}

# Set page configuration
st.set_page_config(
    page_title=lang_content[st.session_state['language']]['page_title'],
    page_icon=":wrench:",
    layout="wide",
)


col_title, col_button = st.columns((0.8, 0.2))
with col_title:
    st.title(lang_content[st.session_state['language']]['header_title'])
with col_button:
    st.button(lang_content[st.session_state['language']]['button_text'], on_click=switch_language)  # Button to switch language
st.divider()


tab1, tab2, tab3 = st.tabs([lang_content[st.session_state['language']]['tab1_title'],
                            lang_content[st.session_state['language']]['tab2_title'],
                            lang_content[st.session_state['language']]['tab3_title']])
with tab1:
    components.iframe("https://amiga-map.ahuekna.org.ar", height=900)
#     components.iframe("http://127.0.0.1:5500/public/", height=900)


with tab3: 
    
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

    # Drop the position(id) column
    df.drop(columns=['position(id)'])

    # Format the date column
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    # Convert min and max dates to datetime objects
    min_date = datetime.strptime(df['date'].min(), '%Y-%m-%d')
    max_date = datetime.strptime(df['date'].max(), '%Y-%m-%d')

    # Create Streamlit widgets for filtering
    empty1, colA, empty2, colB, empty3 = st.columns((0.1, 1, 0.1, 1, 0.1))

    with colA:
        st.header(lang_content[st.session_state['language']]['filters_header'], divider="grey")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### {lang_content[st.session_state['language']]['position_label']}")
            name_dropdown = st.selectbox(lang_content[st.session_state['language']]['position_label'],
                                         np.sort(df['name'].unique()), index=None,
                                         placeholder=lang_content[st.session_state['language']]['position_placeholder'],
                                         key="name_dropdown_1", label_visibility="collapsed")

        if name_dropdown is None:
            filtered_by_name = df
        else:
            filtered_by_name = df[(df['name'] == name_dropdown)]

        with col2:
            st.markdown(f"### {lang_content[st.session_state['language']]['type_label']}")
            type_dropdown = st.selectbox(lang_content[st.session_state['language']]['type_label'],
                                         filtered_by_name['type'].unique(), index=None,
                                         placeholder=lang_content[st.session_state['language']]['type_placeholder'],
                                         key="type_dropdown_1", label_visibility="collapsed")

        if type_dropdown is None:
            filtered_by_type = filtered_by_name
        else:
            filtered_by_type = filtered_by_name[(filtered_by_name['type'] == type_dropdown)]

        st.markdown(f"### {lang_content[st.session_state['language']]['date_interval_label']}")

        col3, col4 = st.columns(2)

        with col3:
            start_date = st.date_input(lang_content[st.session_state['language']]['from_label'],
                                       value=min_date, key="start_date_1")
        with col4:
            end_date = st.date_input(lang_content[st.session_state['language']]['to_label'],
                                     value=max_date, key="end_date_1")

        if start_date is None and end_date is None:
            filtered_by_date = filtered_by_type

        if start_date is not None and end_date is not None:
            filtered_by_date = filtered_by_type[(filtered_by_type['date'] >= start_date.strftime('%Y-%m-%d')) & (filtered_by_type['date'] <= end_date.strftime('%Y-%m-%d'))]

        final_table = filtered_by_date[['date', 'name', 'id', 'type', 'content', 'photos']].sort_values(by='date', ascending=False)
        selections = ["name_dropdown", "type_dropdown"]

        def clear_all():
            for i in selections:
                st.session_state[f'{i}'] = None
            st.session_state['start_date'] = min_date
            st.session_state['end_date'] = max_date

        st.button(lang_content[st.session_state['language']]['clear_filters'], on_click=clear_all)

        st.header(lang_content[st.session_state['language']]['results_header'], divider="grey")
        st.caption(lang_content[st.session_state['language']]['click_report'])

        def photo_formatter(photo_links):
            if isinstance(photo_links, str):
                links = re.findall(r'https://drive\.google\.com/open\?id=[^\s,]+', photo_links)
                return lang_content[st.session_state['language']]['contains_photos'].format(len(links)) if links else ""
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
                                     "date": "Fecha",
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
            st.header(lang_content[st.session_state['language']]['report_header'], divider="grey")
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
                        st.subheader(lang_content[st.session_state['language']]['photos_header'])

                        for link in photo_links:
                            with st.spinner(lang_content[st.session_state['language']]['loading_image']):
                                try:
                                    img = get_image_content(link)

                                    if img.mode == 'RGBA':
                                        img = img.convert('RGB')

                                    img_byte_arr = io.BytesIO()
                                    img.save(img_byte_arr, format='JPEG')
                                    img_byte_arr = img_byte_arr.getvalue()

                                    st.image(img_byte_arr, use_column_width=True)

                                except Exception as e:
                                    st.error(f"{lang_content[st.session_state['language']]['image_load_error']} {str(e)}")
                                    st.markdown(f"[{lang_content[st.session_state['language']]['image_link']}]({link})")

                                time.sleep(0.1)
                    else:
                        st.info(lang_content[st.session_state['language']]['no_photos'])


with tab2:  

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

    # Set Date as index.
    df = df.set_index('date_report') 

    # Convert min and max dates to datetime objects
    dates = df.index.values
    min_date = datetime.strptime(dates.min(), '%Y-%m-%d')
    max_date = datetime.strptime(dates.max(), '%Y-%m-%d')

    # Create Streamlit widgets for filtering
    empty1, colA, empty2, colB, empty3 = st.columns((0.1, 1, 0.1, 1, 0.1))

    with colA:
        st.header(lang_content[st.session_state['language']]['filters_header'], divider="grey")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"### {lang_content[st.session_state['language']]['position_label']}")
            name_dropdown = st.selectbox(lang_content[st.session_state['language']]['position_label'],
                                         np.sort(df['position'].unique()), index=None,
                                         placeholder=lang_content[st.session_state['language']]['position_placeholder'],
                                         key="name_dropdown_2", label_visibility="collapsed")

        if name_dropdown is None:
            filtered_by_name = df
        else:
            filtered_by_name = df[(df['position'] == name_dropdown)]

            
        with col2:
            st.markdown(f"### {lang_content[st.session_state['language']]['status_label']}")
            type_dropdown = st.selectbox(lang_content[st.session_state['language']]['status_label'],
                                            filtered_by_name['status'].unique(), index=None,
                                            placeholder=lang_content[st.session_state['language']]['status_placeholder'],
                                            key="type_dropdown_2", label_visibility="collapsed")

        with col3:
            st.markdown(f"### {lang_content[st.session_state['language']]['team_label']}")
            team_dropdown = st.selectbox(lang_content[st.session_state['language']]['team_label'],
                                            np.sort(filtered_by_name['team'].unique()), index=None,
                                            placeholder=lang_content[st.session_state['language']]['team_placeholder'],
                                            key="team_dropdown_2", label_visibility="collapsed")

        if type_dropdown is None:
            filtered_by_type = filtered_by_name
        else:
            filtered_by_type = filtered_by_name[(filtered_by_name['status'] == type_dropdown)]

        if team_dropdown is None:
            filtered_by_team = filtered_by_type
        else:
            filtered_by_team = filtered_by_type[(filtered_by_type['team'] == team_dropdown)]

        st.markdown(f"### {lang_content[st.session_state['language']]['date_interval_label']}")

        col4, col5 = st.columns(2)

        with col4:
            start_date = st.date_input(lang_content[st.session_state['language']]['from_label'],
                                       value=min_date, key="start_date_2")
        with col5:
            end_date = st.date_input(lang_content[st.session_state['language']]['to_label'],
                                     value=max_date, key="end_date_2")

        if start_date is None and end_date is None:
            filtered_by_date = filtered_by_team

        if start_date is not None and end_date is not None:
            filtered_by_date = filtered_by_team[(filtered_by_team.index.values >= start_date.strftime('%Y-%m-%d')) & (filtered_by_team.index.values <= end_date.strftime('%Y-%m-%d'))]

        final_table = filtered_by_date[['date','position', 'modules', 'summary', 'status', 'team', 'report']].sort_values('status',ascending=True)
        final_table_colA = final_table.loc[final_table['status']!='Complete']
        
        selections = ["name_dropdown", "type_dropdown", "team_dropdown"]
        def clear_all():
            for i in selections:
                st.session_state[f'{i}'] = None
            st.session_state['start_date'] = min_date
            st.session_state['end_date'] = max_date

        st.button(lang_content[st.session_state['language']]['clear_filters'], on_click=clear_all,key='button_2')

        st.header(lang_content[st.session_state['language']]['results_header'], divider="grey")

        st.caption(lang_content[st.session_state['language']]['click_report'])
    
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
            st.header(lang_content[st.session_state['language']]['report_header'], divider="grey")

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

