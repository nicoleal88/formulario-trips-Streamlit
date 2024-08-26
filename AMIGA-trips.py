import streamlit as st
from streamlit_gsheets import GSheetsConnection
import numpy as np
from datetime import datetime
import requests
import re
from PIL import Image
import io
import time

# Initialize or get the language from session state
if 'language' not in st.session_state:
    st.session_state['language'] = 'es'  # Default language is Spanish

# Function to switch language
def switch_language():
    st.session_state['language'] = 'en' if st.session_state['language'] == 'es' else 'es'

# Language dependent content
lang_content = {
    'es': {
        'page_title': "Salidas al campo - AMIGA",
        'header_title': "Salidas al campo - Team AMIGA",
        'filters_header': "Filtros",
        'position_label': "Posición:",
        'position_placeholder': "Seleccionar posición",
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
        'contains_photos': "Contiene {} 📷"
    },
    'en': {
        'page_title': "Field Trips - AMIGA",
        'header_title': "Field Trips - Team AMIGA",
        'filters_header': "Filters",
        'position_label': "Position:",
        'position_placeholder': "Select position",
        'type_label': "Type of trip:",
        'type_placeholder': "Select type of trip",
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
        'contains_photos': "Contains {} 📷"
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
conn = st.connection("gsheets", type=GSheetsConnection)

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
                                     key="name_dropdown", label_visibility="collapsed")

    if name_dropdown is None:
        filtered_by_name = df
    else:
        filtered_by_name = df[(df['name'] == name_dropdown)]

    with col2:
        st.markdown(f"### {lang_content[st.session_state['language']]['type_label']}")
        type_dropdown = st.selectbox(lang_content[st.session_state['language']]['type_label'],
                                     filtered_by_name['type'].unique(), index=None,
                                     placeholder=lang_content[st.session_state['language']]['type_placeholder'],
                                     key="type_dropdown", label_visibility="collapsed")

    if type_dropdown is None:
        filtered_by_type = filtered_by_name
    else:
        filtered_by_type = filtered_by_name[(filtered_by_name['type'] == type_dropdown)]

    st.markdown(f"### {lang_content[st.session_state['language']]['date_interval_label']}")

    col3, col4 = st.columns(2)

    with col3:
        start_date = st.date_input(lang_content[st.session_state['language']]['from_label'],
                                   value=min_date, key="start_date")
    with col4:
        end_date = st.date_input(lang_content[st.session_state['language']]['to_label'],
                                 value=max_date, key="end_date")

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