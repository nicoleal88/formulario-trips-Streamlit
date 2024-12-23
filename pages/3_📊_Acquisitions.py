import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from translations import lang_content as translations
from navigation import make_sidebar
from datetime import datetime
import numpy as np
from utils import search_dataframe

make_sidebar()

st.header(translations['tab_acq_title'][st.session_state['language']], divider="grey")

# Connect to Google Sheets
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
colA, empty1, colB = st.columns((0.48, 0.04, 0.48))

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