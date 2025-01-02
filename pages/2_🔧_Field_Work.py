import streamlit as st
from navigation import make_sidebar
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from translations import lang_content as translations
import numpy as np
from datetime import datetime
from utils import search_dataframe, get_image_content, clean_url, photo_formatter
import re
import time
import io
from utils import check_login

# Check if user is logged in, redirect to home page if not
if not check_login():
    st.stop()
make_sidebar()

st.header(translations['tab_field_title'][st.session_state['language']], divider="grey")

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
colA, empty1, colB = st.columns((0.48, 0.04, 0.48))

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
