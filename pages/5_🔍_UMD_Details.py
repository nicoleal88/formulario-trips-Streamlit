import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from translations import lang_content as translations
from navigation import make_sidebar
from utils import scintillator_mapping, create_umd_position_plot, check_login
import re

# Check if user is logged in, redirect to home page if not
if not check_login():
    st.stop()
make_sidebar()

st.header(translations['tab_umd_details'][st.session_state['language']], divider="grey")

# Create two main columns
colA, empty1, colB = st.columns((0.24, 0.04, 0.72))

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

with colA:
    st.header(translations['filters_header'][st.session_state['language']], divider="grey")

    # Add position filter first
    st.markdown(f"### {translations['position_label'][st.session_state['language']]}")
    position_filter = st.selectbox(
        translations['position_label'][st.session_state['language']],
        options=[''] + sorted(df_historial['position'].unique().tolist()),
        format_func=lambda x: translations['position_placeholder'][st.session_state['language']] if x == '' else x,
        key="position_filter_umd_details",
        label_visibility="collapsed"
    )

    # Filter UMDs based on selected position
    if position_filter:
        filtered_umds = pd.concat([
            df_historial[df_historial['position'] == position_filter]['id_m101'],
            df_historial[df_historial['position'] == position_filter]['id_m102'],
            df_historial[df_historial['position'] == position_filter]['id_m103']
        ]).unique()
        # Remove "-" from the list if present
        filtered_umds = filtered_umds[filtered_umds != "-"]
    else:
        # Get all UMDs from all three columns
        filtered_umds = pd.concat([
            df_historial['id_m101'],
            df_historial['id_m102'],
            df_historial['id_m103']
        ]).unique()
        # Remove "-" from the list if present
        filtered_umds = filtered_umds[filtered_umds != "-"]

    # UMD selection with filtered options
    st.markdown(f"### {translations['select_umd_label'][st.session_state['language']]}")
    selected_umd = st.selectbox(
        translations['select_umd_label'][st.session_state['language']],
        options=[None] + sorted(filtered_umds),
        format_func=lambda x: translations['select_umd_label'][st.session_state['language']] if x is None else str(x),
        key="umd_selector",
        label_visibility="collapsed"
    )

    if selected_umd:
        matching_rows = df_umd[df_umd['UMD_ID'] == selected_umd]
        if not matching_rows.empty:
            selected_row = matching_rows.iloc[0]
            
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
                    details_display = translations['no_issues_reported'][st.session_state['language']]
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
                
                st.markdown(f"""### {translations['installation_info_header'][st.session_state['language']]}""")
                st.markdown(f"""
                            - **{translations['position_label'][st.session_state['language']]}** {umd_info['position']}
                            - **{translations['from_label'][st.session_state['language']]}** {umd_info['install_date'].strftime('%Y-%m-%d')}
                            - **{translations['module_position_label'][st.session_state['language']]}** m-{module_num}
                            - **{translations['electronic_kit_label'][st.session_state['language']]}** {umd_info[f'ekit_m{module_num}']}
                            - **{translations['module_details_label'][st.session_state['language']]}**
                                - {translations['rotation_angle_label'][st.session_state['language']]}: {umd_info[f'RotationAngle_m{module_num}']}°
                                - {translations['radio_distance_label'][st.session_state['language']]}: {umd_info[f'RadioDistance_m{module_num}']} m
                                - {translations['position_angle_label'][st.session_state['language']]}: {umd_info[f'PositionAngle_m{module_num}']}°
                            - **{translations['other_modules_label'][st.session_state['language']]}**
                                - Module 1: {umd_info['id_m101']}
                                - Module 2: {umd_info['id_m102']}
                                - Module 3: {umd_info['id_m103']}
                            """)
                
                st.markdown(f"""### {translations['assembly_issues_header'][st.session_state['language']]}""")
                st.markdown(details_display)
                
            else:
                st.warning(translations['no_installation_info'][st.session_state['language']])

with colB:
    st.header(translations['report_header'][st.session_state['language']], divider="grey")

    if selected_umd and umd_info is not None:
        # Create two columns for the plots
        plot_col1, plot_col2 = st.columns(2)
        
        with plot_col1:
            st.markdown(f"### {translations['umd_layout_header'][st.session_state['language']]}")
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
                hovermode='closest'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with plot_col2:
            st.markdown(f"### {translations['umd_position_header'][st.session_state['language']]}")
            position_fig = create_umd_position_plot(umd_info, selected_umd)
            if position_fig is not None:
                st.plotly_chart(position_fig, use_container_width=True)
            else:
                st.warning(translations['no_plot_data'][st.session_state['language']])
