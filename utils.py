import pandas as pd
import streamlit as st
import requests
from PIL import Image
import io
import re
from translations import lang_content as translations
import plotly.graph_objects as go
import numpy as np


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

def switch_language():
    """Switch between English and Spanish languages"""
    st.session_state['language'] = 'en' if st.session_state['language'] == 'es' else 'es'

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

# Function to clean up the URL
def clean_url(url):
    return url.rstrip(',')  # Remove trailing comma if present

def photo_formatter(photo_links):
    if isinstance(photo_links, str):
        links = re.findall(r'https://drive\.google\.com/open\?id=[^\s,]+', photo_links)
        return translations['contains_photos'][st.session_state['language']].format(len(links)) if links else ""
    return ""




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

def check_login():
    """
    Check if user is logged in and redirect to home page if not.
    Returns True if logged in, False otherwise.
    """
    if not st.session_state.get("logged_in", False):
        st.switch_page("app.py")
        return False
    return True

def create_umd_position_plot(umd_info, selected_umd):
    try:
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

            rd = float(str(umd_info[f'RadioDistance_m{module}']).replace(',', '.'))
            pa = np.radians(float(str(umd_info[f'PositionAngle_m{module}']).replace(',', '.')))
            ra = np.radians(float(str(umd_info[f'RotationAngle_m{module}']).replace(',', '.')))

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
            height=800,
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
    except Exception as e:
        print(f"Error creating plot: {str(e)}")
        return None