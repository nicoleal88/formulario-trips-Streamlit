import streamlit as st
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components
import numpy as np
import pandas as pd
from datetime import datetime
import requests
import re
from PIL import Image
import io
import time
import plotly.express as px

import hmac
from translations import lang_content

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


tab1, tab2, tab3, tab4 = st.tabs([lang_content[st.session_state['language']]['tab1_title'],
                                lang_content[st.session_state['language']]['tab2_title'],
                                lang_content[st.session_state['language']]['tab3_title'],
                                lang_content[st.session_state['language']]['tab4_title']])

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
        st.header(lang_content[st.session_state['language']]['filters_header'], divider="grey")
        
        # Add search box in the filters section
        st.markdown(f"### {lang_content[st.session_state['language']]['search_label']}")
        search_query = st.text_input(
            label=lang_content[st.session_state['language']]['search_placeholder'],
            key="search_tab3",
            label_visibility="collapsed"
        )

        # Reset index before applying search to ensure proper alignment
        df = df.reset_index(drop=True)
        
        if search_query:
            search_mask = search_dataframe(df, search_query)
            df = df[search_mask].copy()  # Create a copy to avoid SettingWithCopyWarning
            if len(df) == 0:
                st.warning(lang_content[st.session_state['language']]['no_results'].format(search_query))
                st.stop()
            else:
                st.info(lang_content[st.session_state['language']]['search_results'].format(len(df), search_query))

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
            filtered_by_date = filtered_by_type[
                (filtered_by_type['date'] >= pd.Timestamp(start_date)) & 
                (filtered_by_type['date'] <= pd.Timestamp(end_date))
            ]

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

        # Cambia a los filtros guardados en tab3
        # if 'selected_position' in st.session_state:
        #     print(st.session_state['selected_position'])
        #     st.selectbox("Posición", options=np.sort(df['name'].unique()), index=None,
        #                 key="name_dropdown_1", label_visibility="collapsed",
        #                 value="CATHERINA")
            
        # if 'selected_status' in st.session_state:
        #     st.selectbox("Estado", options=df['status'].unique(), index=None,
        #                 key="type_dropdown_1", label_visibility="collapsed",
        #                 value=st.session_state['selected_status'])
            
        # if 'selected_team' in st.session_state:
        #     st.selectbox("Equipo", options=np.sort(df['team'].unique()), index=None,
        #                 key="team_dropdown_1", label_visibility="collapsed",
        #                 value=st.session_state['selected_team'])

        # Borra los filtros después de aplicarlos
        # for key in ['selected_position']: #, 'selected_status', 'selected_team']:
        #     st.session_state.pop(key, None)

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

    # Get min and max dates before any filtering
    if len(df) > 0:
        dates = df['date_report'].values
        min_date = datetime.strptime(dates.min(), '%Y-%m-%d')
        max_date = datetime.strptime(dates.max(), '%Y-%m-%d')
    else:
        min_date = datetime.now()
        max_date = datetime.now()

    # Create Streamlit widgets for filtering
    empty1, colA, empty2, colB, empty3 = st.columns((0.1, 1, 0.1, 1, 0.1))

    with colA:
        st.header(lang_content[st.session_state['language']]['filters_header'], divider="grey")
        
        # Add search box in the filters section
        st.markdown(f"### {lang_content[st.session_state['language']]['search_label']}")
        search_query = st.text_input(
            label=lang_content[st.session_state['language']]['search_placeholder'],
            key="search_tab2",
            label_visibility="collapsed"
        )

        # Reset index before applying search to ensure proper alignment
        df = df.reset_index(drop=True)
        
        if search_query:
            search_mask = search_dataframe(df, search_query)
            df = df[search_mask].copy()  # Create a copy to avoid SettingWithCopyWarning
            if len(df) == 0:
                st.warning(lang_content[st.session_state['language']]['no_results'].format(search_query))
                st.stop()
            else:
                st.info(lang_content[st.session_state['language']]['search_results'].format(len(df), search_query))

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
            filtered_by_date = filtered_by_team[(filtered_by_team['date_report'] >= start_date.strftime('%Y-%m-%d')) & (filtered_by_team['date_report'] <= end_date.strftime('%Y-%m-%d'))]

        final_table = filtered_by_date[['date','position', 'modules', 'summary', 'status', 'team', 'report']].sort_values('status',ascending=True)
        final_table_colA = final_table.loc[final_table['status']!='Complete']
        
        selections = ["name_dropdown", "type_dropdown", "team_dropdown"]
        def clear_all():
            for i in selections:
                st.session_state[f'{i}'] = None
            st.session_state['start_date'] = min_date
            st.session_state['end_date'] = max_date

        def go_to_tab3_with_filters():
                    st.session_state['selected_position'] = st.session_state['name_dropdown_2']
                    st.session_state['selected_status'] = st.session_state['type_dropdown_2']
                    st.session_state['selected_team'] = st.session_state['team_dropdown_2']
                    st.session_state['tab'] = 'tab3'
                    # print(st.session_state['selected_position'], st.session_state['selected_status'], st.session_state['selected_team'])

        st.button("Ir a Salidas al Campo", on_click=go_to_tab3_with_filters)

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

with tab4:
    # Conexión y configuración para obtener el dataframe de stock
    conn_stock = st.connection("stats_stock", type=GSheetsConnection)
    column_indices_stock = [0, 1]
    new_column_names_stock = ['date', 'UMD_number']

    # Leer y limpiar el dataframe de stock
    df_stock = conn_stock.read(usecols=column_indices_stock,
                               names=new_column_names_stock,
                               header=None,
                               dayfirst=True,
                               skiprows=9).dropna()
    # Convertir la columna 'UMD_number' a tipo entero
    df_stock['UMD_number'] = df_stock['UMD_number'].astype(int)
    # Formatear la columna de fechas
    df_stock['date'] = pd.to_datetime(df_stock['date'], format="%d/%m/%y")

    # Conexión y configuración para obtener el dataframe de historial
    conn_historial = st.connection("stats_historial", type=GSheetsConnection)
    column_indices_historial = [2, 3, 6]
    new_column_names_historial = ['name', 'id', 'date']

    # Leer y limpiar el dataframe de historial
    df_historial = conn_historial.read(usecols=column_indices_historial,
                                       names=new_column_names_historial,
                                       header=None,
                                       dayfirst=True,
                                       skiprows=7).dropna()
    # Filtrar filas donde la fecha contenga "-"
    df_historial = df_historial[~df_historial["date"].str.contains("-")]
    # Convertir la columna 'id' a tipo entero
    df_historial['id'] = df_historial['id'].astype(int)
    # Formatear la columna de fechas y ordenar
    df_historial['date'] = pd.to_datetime(df_historial['date'], format="%d/%m/%y")
    df_historial = df_historial.sort_values(by='date')

    # Agregar un número de fila como contador
    df_historial = df_historial.assign(row_number=range(1, len(df_historial) + 1))

    # Métricas
    st.markdown("## Quarterly Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric(label="UMDs Deployed", value="143", delta="8")
    col2.metric(label="ekits Deployed", value="134", delta="5")
    col3.metric(label="Entered ACQ", value="45", delta="3")

    # Graficar el dataframe de stock
    fig = px.line(df_stock, x="date", y="UMD_number", title="UMD Number over Time")
    st.plotly_chart(fig)

    # Graficar el dataframe de historial
    fig2 = px.line(df_historial, x="date", y="row_number", title="Row Number over Time")
    st.plotly_chart(fig2)

    # Merge de ambos dataframes y gráfico combinado
    df_merged = pd.merge(df_stock, df_historial, on='date', how='outer', suffixes=('_df1', '_df2'))
    df_merged = df_merged.sort_values(by='date')
    # Rellenar NaN con 0 en las columnas 'UMD_number_df1' y 'row_number_df2'
    df_merged['UMD_number_df1'] = df_merged['UMD_number'].fillna(0)
    df_merged['row_number_df2'] = df_merged['row_number'].fillna(0)
    
    # Graficar las series combinadas
    fig3 = px.line(df_merged, x='date', y=['UMD_number', 'row_number'],
                   labels={'date': 'Fecha', 'value': 'Valor Acumulado'},
                   title="Valores Acumulativos en el Tiempo")
    st.plotly_chart(fig3)
