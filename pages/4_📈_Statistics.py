import streamlit as st
import pandas as pd
import plotly.express as px
from translations import lang_content as translations
from streamlit_gsheets import GSheetsConnection
from navigation import make_sidebar
from utils import check_login, SHADED_PERIODS

# Check if user is logged in, redirect to home page if not
if not check_login():
    st.stop()
make_sidebar()

st.header(translations['tab_stats_title'][st.session_state['language']], divider="grey")

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
def generate_quarters(start_date, end_date):
    quarters = {}
    current = pd.Timestamp(start_date)
    while current <= end_date:
        quarter = (current.month - 1) // 3 + 1
        quarter_start = pd.Timestamp(f"{current.year}-{(quarter-1)*3 + 1:02d}-01")
        quarter_end = quarter_start + pd.offsets.QuarterEnd()
        quarters[f"Q{quarter} {current.year}"] = (quarter_start, quarter_end)
        current = quarter_start + pd.DateOffset(months=3)
    return quarters

# Generate quarters from Jan 2023 to current date
start_date = pd.Timestamp('2023-01-01')
end_date = pd.Timestamp.now()
quarter_filters = generate_quarters(start_date, end_date)

time_filters = {
    'All Time': None,
    'Last Month': pd.DateOffset(months=1),
    'Last Quarter': pd.DateOffset(months=3),
    'Last Year': pd.DateOffset(years=1),
    **{k: v for k, v in sorted(quarter_filters.items(), reverse=True)}  # Add quarters in reverse chronological order
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