import streamlit as st
from streamlit_gsheets import GSheetsConnection
import numpy as np

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

df[['name', 'id']] = df['position(id)'].str.extract(r'([\w\s.]+)\s*\(id=(\d+)\)', expand=True)

df.drop(columns=['position(id)'])

df['date'] = df['date'].dt.strftime('%Y-%m-%d')

# Create Streamlit widgets for filtering
# age_slider = st.slider('Select maximum age:', min_value=0, max_value=100, value=40)

st.markdown("### Posición:")

name_dropdown = st.selectbox("Posición:", np.sort(df['name'].unique()), index=None, placeholder="Seleccionar posición", label_visibility="collapsed")

if name_dropdown is None:
    filtered_by_name = df
else:
    filtered_by_name = df[(df['name'] == name_dropdown)]

st.markdown("### Tipo de salida:")

type_dropdown = st.selectbox("Tipo de salida:", filtered_by_name['type'].unique(), index=None, placeholder="Seleccionar tipo de salida", label_visibility="collapsed")

st.markdown("### Click en \"Ver informe\"  para ver el reporte de la salida:")

if type_dropdown is None:
    filtered_by_type = filtered_by_name
else:
    filtered_by_type = filtered_by_name[(filtered_by_name['type'] == type_dropdown)]


# final_table = filtered_by_type[['date','name', 'id','type']].sort_values(by='date', ascending=False)
final_table = filtered_by_type[['date','name', 'id','type', 'content']].sort_values(by='date', ascending=False)
# st.table(final_table)


def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)
    edited_df = st.data_editor(
        df_with_selections,
        width=800,
        column_config={"Select": st.column_config.CheckboxColumn(required=True),
                    "content": None,
                    "date": "Fecha",
                    "type": "Tipo de Salida",
                    "Select": "Ver informe"
                    },
        disabled=df.columns,
        hide_index=True,
    )
    selected_indices = list(np.where(edited_df.Select)[0])
    selected_rows = df[edited_df.Select]
    return {"selected_rows_indices": selected_indices, "selected_rows": selected_rows}

selection = dataframe_with_selections(final_table)

# st.write("Your selection:")

if len(selection["selected_rows_indices"]) > 0:
    md_content = selection["selected_rows"]["content"].iloc[0]
    st.write(md_content)
