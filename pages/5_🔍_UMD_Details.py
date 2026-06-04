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
    usecols=['SD', 'LSID', 'Fecha_de_Deployment',
             'ID_M101', 'RA_M101', 'RD_M101', 'PA_M101',
             'ID_M102', 'RA_M102', 'RD_M102', 'PA_M102',
             'ID_M103', 'RA_M103', 'RD_M103', 'PA_M103',
             'eKit_M101', 'eKit_M102', 'eKit_M103',
             'ID_M101_CU', 'RA_M101_CU', 'RD_M101_CU', 'PA_M101_CU',
             'ID_M102_CU', 'RA_M102_CU', 'RD_M102_CU', 'PA_M102_CU',
             'ID_M103_CU', 'RA_M103_CU', 'RD_M103_CU', 'PA_M103_CU',
             'ID_M104_CU', 'RA_M104_CU', 'RD_M104_CU', 'PA_M104_CU',
             'ID_M105_CU', 'RA_M105_CU', 'RD_M105_CU', 'PA_M105_CU',
             'ID_M106_CU', 'RA_M106_CU', 'RD_M106_CU', 'PA_M106_CU',
             'ID_M107_CU', 'RA_M107_CU', 'RD_M107_CU', 'PA_M107_CU',
             'ID_M108_CU', 'RA_M108_CU', 'RD_M108_CU', 'PA_M108_CU',
             'ID_M109_CU', 'RA_M109_CU', 'RD_M109_CU', 'PA_M109_CU',
             'eKit_M101_CU', 'eKit_M102_CU', 'eKit_M103_CU', 'eKit_M104_CU',
             'eKit_M105_CU', 'eKit_M106_CU', 'eKit_M107_CU', 'eKit_M108_CU',
             'eKit_M109_CU',
             'a_M101_CU', 'a_M102_CU', 'a_M103_CU', 'a_M104_CU',
             'a_M105_CU', 'a_M106_CU', 'a_M107_CU', 'a_M108_CU', 'a_M109_CU'],
).rename(columns={
    'SD': 'position', 'LSID': 'id', 'Fecha_de_Deployment': 'install_date',
    'ID_M101': 'id_m101', 'RA_M101': 'RotationAngle_m101',
    'RD_M101': 'RadioDistance_m101', 'PA_M101': 'PositionAngle_m101',
    'ID_M102': 'id_m102', 'RA_M102': 'RotationAngle_m102',
    'RD_M102': 'RadioDistance_m102', 'PA_M102': 'PositionAngle_m102',
    'ID_M103': 'id_m103', 'RA_M103': 'RotationAngle_m103',
    'RD_M103': 'RadioDistance_m103', 'PA_M103': 'PositionAngle_m103',
    'eKit_M101': 'ekit_m101', 'eKit_M102': 'ekit_m102', 'eKit_M103': 'ekit_m103',
    'ID_M101_CU': 'id_m101_cu', 'RA_M101_CU': 'RotationAngle_m101_cu',
    'RD_M101_CU': 'RadioDistance_m101_cu', 'PA_M101_CU': 'PositionAngle_m101_cu',
    'ID_M102_CU': 'id_m102_cu', 'RA_M102_CU': 'RotationAngle_m102_cu',
    'RD_M102_CU': 'RadioDistance_m102_cu', 'PA_M102_CU': 'PositionAngle_m102_cu',
    'ID_M103_CU': 'id_m103_cu', 'RA_M103_CU': 'RotationAngle_m103_cu',
    'RD_M103_CU': 'RadioDistance_m103_cu', 'PA_M103_CU': 'PositionAngle_m103_cu',
    'ID_M104_CU': 'id_m104_cu', 'RA_M104_CU': 'RotationAngle_m104_cu',
    'RD_M104_CU': 'RadioDistance_m104_cu', 'PA_M104_CU': 'PositionAngle_m104_cu',
    'ID_M105_CU': 'id_m105_cu', 'RA_M105_CU': 'RotationAngle_m105_cu',
    'RD_M105_CU': 'RadioDistance_m105_cu', 'PA_M105_CU': 'PositionAngle_m105_cu',
    'ID_M106_CU': 'id_m106_cu', 'RA_M106_CU': 'RotationAngle_m106_cu',
    'RD_M106_CU': 'RadioDistance_m106_cu', 'PA_M106_CU': 'PositionAngle_m106_cu',
    'ID_M107_CU': 'id_m107_cu', 'RA_M107_CU': 'RotationAngle_m107_cu',
    'RD_M107_CU': 'RadioDistance_m107_cu', 'PA_M107_CU': 'PositionAngle_m107_cu',
    'ID_M108_CU': 'id_m108_cu', 'RA_M108_CU': 'RotationAngle_m108_cu',
    'RD_M108_CU': 'RadioDistance_m108_cu', 'PA_M108_CU': 'PositionAngle_m108_cu',
    'ID_M109_CU': 'id_m109_cu', 'RA_M109_CU': 'RotationAngle_m109_cu',
    'RD_M109_CU': 'RadioDistance_m109_cu', 'PA_M109_CU': 'PositionAngle_m109_cu',
    'eKit_M101_CU': 'ekit_m101_cu', 'eKit_M102_CU': 'ekit_m102_cu',
    'eKit_M103_CU': 'ekit_m103_cu', 'eKit_M104_CU': 'ekit_m104_cu',
    'eKit_M105_CU': 'ekit_m105_cu', 'eKit_M106_CU': 'ekit_m106_cu',
    'eKit_M107_CU': 'ekit_m107_cu', 'eKit_M108_CU': 'ekit_m108_cu',
    'eKit_M109_CU': 'ekit_m109_cu',
    'a_M101_CU': 'area_m101_cu', 'a_M102_CU': 'area_m102_cu', 'a_M103_CU': 'area_m103_cu',
    'a_M104_CU': 'area_m104_cu', 'a_M105_CU': 'area_m105_cu', 'a_M106_CU': 'area_m106_cu',
    'a_M107_CU': 'area_m107_cu', 'a_M108_CU': 'area_m108_cu', 'a_M109_CU': 'area_m109_cu',
})

# Clean installation data: keep all rows (CU SDs may have install_date = '-');
# coerce install_date to datetime; NaT is acceptable — the UI hides the "From" row.
df_historial['install_date'] = pd.to_datetime(df_historial['install_date'], dayfirst=True, errors='coerce')
df_historial['id'] = df_historial['id'].astype(int)

# Module column lists (main slots 101-103 + CU slots 101-109)
MAIN_MODULE_COLS = ['id_m101', 'id_m102', 'id_m103']
CU_MODULE_COLS = [f'id_m{n}_cu' for n in range(101, 110)]
ALL_MODULE_COLS = MAIN_MODULE_COLS + CU_MODULE_COLS

# Subset to SDs that have at least one UMD in any of the 12 module slots
has_umd = df_historial[ALL_MODULE_COLS].apply(
    lambda r: any(isinstance(v, str) and v and v != '-' for v in r), axis=1
)
df_with_umd = df_historial[has_umd].copy()

with colA:
    st.header(translations['filters_header'][st.session_state['language']], divider="grey")

    # Add position filter first
    st.markdown(f"### {translations['position_label'][st.session_state['language']]}")
    position_filter = st.selectbox(
        translations['position_label'][st.session_state['language']],
        options=[''] + sorted(df_with_umd['position'].unique().tolist()),
        format_func=lambda x: translations['position_placeholder'][st.session_state['language']] if x == '' else x,
        key="position_filter_umd_details",
        label_visibility="collapsed"
    )

    # Filter UMDs based on selected position (from all 12 module columns)
    if position_filter:
        source_df = df_with_umd[df_with_umd['position'] == position_filter]
    else:
        source_df = df_with_umd
    filtered_umds = pd.concat([source_df[c] for c in ALL_MODULE_COLS]).unique()
    filtered_umds = sorted([u for u in filtered_umds if isinstance(u, str) and u and u != '-'])

    # UMD selection with filtered options
    st.markdown(f"### {translations['select_umd_label'][st.session_state['language']]}")
    selected_umd = st.selectbox(
        translations['select_umd_label'][st.session_state['language']],
        options=[None] + sorted(filtered_umds),
        format_func=lambda x: translations['select_umd_label'][st.session_state['language']] if x is None else str(x),
        key="umd_selector",
        label_visibility="collapsed"
    )

    umd_info = None
    selected_row = None

    if selected_umd:
        # Lookup 1: assembly issues details (df_umd) — independent
        matching_rows = df_umd[df_umd['UMD_ID'] == selected_umd]
        selected_row = matching_rows.iloc[0] if not matching_rows.empty else None

        # Lookup 2: installation info (df_with_umd) — independent
        matches_hist = df_with_umd[
            (df_with_umd['id_m101'] == selected_umd) |
            (df_with_umd['id_m102'] == selected_umd) |
            (df_with_umd['id_m103'] == selected_umd) |
            (df_with_umd['id_m101_cu'] == selected_umd) |
            (df_with_umd['id_m102_cu'] == selected_umd) |
            (df_with_umd['id_m103_cu'] == selected_umd) |
            (df_with_umd['id_m104_cu'] == selected_umd) |
            (df_with_umd['id_m105_cu'] == selected_umd) |
            (df_with_umd['id_m106_cu'] == selected_umd) |
            (df_with_umd['id_m107_cu'] == selected_umd) |
            (df_with_umd['id_m108_cu'] == selected_umd) |
            (df_with_umd['id_m109_cu'] == selected_umd)
        ]
        umd_info = matches_hist.iloc[0] if not matches_hist.empty else None

        if umd_info is not None:
            # Find which module number this UMD is (main or CU)
            module_num = None
            is_cu = False
            for col in ALL_MODULE_COLS:
                if umd_info[col] == selected_umd:
                    if col in MAIN_MODULE_COLS:
                        module_num = int(col[4:])
                    else:
                        module_num = int(col[4:].replace('_cu', ''))
                        is_cu = True
                    break
            suffix = '_cu' if is_cu else ''

            st.markdown(f"""### {translations['installation_info_header'][st.session_state['language']]}""")

            info_lines = [
                f"- **{translations['position_label'][st.session_state['language']]}** {umd_info['position']}",
            ]
            if pd.notna(umd_info['install_date']):
                info_lines.append(
                    f"- **{translations['from_label'][st.session_state['language']]}** "
                    f"{umd_info['install_date'].strftime('%Y-%m-%d')}"
                )
            info_lines.extend([
                f"- **{translations['module_position_label'][st.session_state['language']]}** m-{module_num}",
                f"- **{translations['electronic_kit_label'][st.session_state['language']]}** {umd_info[f'ekit_m{module_num}{suffix}']}",
                f"- **{translations['module_details_label'][st.session_state['language']]}**",
                f"    - {translations['rotation_angle_label'][st.session_state['language']]}: {umd_info[f'RotationAngle_m{module_num}{suffix}']}°",
                f"    - {translations['radio_distance_label'][st.session_state['language']]}: {umd_info[f'RadioDistance_m{module_num}{suffix}']} m",
                f"    - {translations['position_angle_label'][st.session_state['language']]}: {umd_info[f'PositionAngle_m{module_num}{suffix}']}°",
                f"- **{translations['other_modules_label'][st.session_state['language']]}**",
            ])
            def _is_empty(v):
                return v is None or (isinstance(v, str) and (not v or v == '-'))

            for col in MAIN_MODULE_COLS:
                val = umd_info[col]
                if not _is_empty(val):
                    info_lines.append(f"    - Main {col[4:]}: {val}")
            for col in CU_MODULE_COLS:
                val = umd_info[col]
                if not _is_empty(val):
                    info_lines.append(f"    - CU {col[4:].replace('_cu', '')}: {val}")

            st.markdown("\n".join(info_lines))

            st.markdown(f"""### {translations['assembly_issues_header'][st.session_state['language']]}""")
            if selected_row is not None:
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

                st.markdown(details_display)
            else:
                st.markdown(f"_{translations['no_issues_reported'][st.session_state['language']]}_")

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
            details_text = selected_row['Details'] if selected_row is not None else pd.NA
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
