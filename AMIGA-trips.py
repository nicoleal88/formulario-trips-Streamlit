import streamlit as st
from streamlit_gsheets import GSheetsConnection
import numpy as np
from datetime import datetime

st.set_page_config(
    page_title="Salidas al campo - AMIGA",
    page_icon=":wrench:",
)
st.title("Salidas al campo - Team AMIGA")

conn = st.connection("gsheets", type=GSheetsConnection)

# Specify the column indices you want to select
column_indices = [1, 2, 3, 5, 6]

# Rename the columns
new_column_names = ['content', 'position(id)', 'type', 'team', 'date']

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
st.markdown("---")

col1, col2 = st.columns(2)
with col1:

    st.markdown("### Posición:")

    name_dropdown = st.selectbox("Posición:", np.sort(df['name'].unique()), index=None, placeholder="Seleccionar posición", key="name_dropdown", label_visibility="collapsed")

if name_dropdown is None:
    filtered_by_name = df
else:
    filtered_by_name = df[(df['name'] == name_dropdown)]

with col2:

    st.markdown("### Tipo de salida:")

    type_dropdown = st.selectbox("Tipo de salida:", filtered_by_name['type'].unique(), index=None, placeholder="Seleccionar tipo de salida", key="type_dropdown", label_visibility="collapsed")

if type_dropdown is None:
    filtered_by_type = filtered_by_name
else:
    filtered_by_type = filtered_by_name[(filtered_by_name['type'] == type_dropdown)]

st.markdown("### Intervalo de fechas:")

col3, col4 = st.columns(2)

with col3:
    start_date = st.date_input("Desde:", value=min_date, key="start_date")
with col4:
    end_date = st.date_input("Hasta:", value=max_date, key="end_date")

if start_date is None and end_date is None:
    filtered_by_date = filtered_by_type

if start_date is not None and end_date is not None:
    filtered_by_date = filtered_by_type[(filtered_by_type['date'] >= start_date.strftime('%Y-%m-%d')) & (filtered_by_type['date'] <= end_date.strftime('%Y-%m-%d'))]

final_table = filtered_by_date[['date','name', 'id','type', 'content']].sort_values(by='date', ascending=False)


#create your button to clear the state of the checkboxes

selections = ["name_dropdown","type_dropdown"]

def clear_all():
    for i in selections:
        # print(st.session_state[f'{i}'])
        st.session_state[f'{i}'] = None
    st.session_state['start_date'] = min_date
    st.session_state['end_date'] = max_date
    return

st.button("Limpiar filtros", on_click=clear_all)

st.markdown("---")

st.markdown("### Click en \"Ver informe\"  para ver el reporte de la salida:")

# Filter the dataframe based on the selected name, type, and date range
# if name_dropdown is not None:
#     df = df[df['name'] == name_dropdown]

# if type_dropdown is not None:
#     df = df[df['type'] == type_dropdown]




def dataframe_with_selections(df):
    # Add a checkbox column for selection
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)
    
    # Determine the height of the data editor based on the length of the DataFrame
    height = 200 if len(df) > 5 else None
    
    # Display the data editor
    edited_df = st.data_editor(
        df_with_selections,
        width=800,
        height=height,
        column_config={"Select": st.column_config.CheckboxColumn(required=True),
                    "content": None,
                    "date": "Fecha",
                    "type": "Tipo de Salida",
                    "Select": "Ver informe",
                    "name": "Posición"
                    },
        disabled=df.columns,
        hide_index=True,
    )
    
    # Get the selected rows
    selected_indices = list(np.where(edited_df.Select)[0])
    selected_rows = df[edited_df.Select]
    return {"selected_rows_indices": selected_indices, "selected_rows": selected_rows}

selection = dataframe_with_selections(final_table)

# Display the selected report content
if len(selection["selected_rows_indices"]) > 0:
    st.markdown("---")
    md_content = selection["selected_rows"]["content"].iloc[0]
    st.write(md_content)
