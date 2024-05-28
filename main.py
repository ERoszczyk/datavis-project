import streamlit as st
from st_pages import Page, show_pages
import pandas as pd
import numpy as np

# Function to load data in chunks
@st.cache_data(persist=True)
def load_data_in_chunks(file_path, chunk_size=100000):
    chunk_list = []
    required_columns = ['ARRIVAL_TIME', 'DATE', 'ARRIVAL_DELAY', 'DEPARTURE_DELAY']
    for chunk in pd.read_csv(file_path, chunksize=chunk_size, low_memory=False):
        if all(column in chunk.columns for column in required_columns):
            chunk['ARRIVAL_TIME'] = pd.to_datetime(chunk['ARRIVAL_TIME'], format='%H:%M:%S', errors='coerce')
            chunk['DATE'] = pd.to_datetime(chunk['DATE'], errors='coerce')
            chunk['ARRIVAL_DELAY'] = chunk['ARRIVAL_DELAY'].astype(np.float32, errors='ignore')
            chunk['DEPARTURE_DELAY'] = chunk['DEPARTURE_DELAY'].astype(np.float32, errors='ignore')
            chunk_list.append(chunk)
        else:
            st.warning("Some chunks are missing required columns and will be skipped.")
    if chunk_list:
        df = pd.concat(chunk_list, ignore_index=True)
    else:
        st.error("No valid data loaded. Please check your dataset.")
        df = pd.DataFrame(columns=required_columns)
    return df

# Load dataset and store it in session state if not already present
if 'df' not in st.session_state:
    st.session_state.df = load_data_in_chunks('2015_dataset/merged_full_dataset.csv')

show_pages(
    [
        Page("pages/Airport.py", "Delay By Airport", "📌"),
        Page("pages/Routes.py", "Delay By Routes", "🗺"),
        Page("pages/Time.py", "Delay By Time", "📅"),
        Page("pages/Airlines.py", "Delay By Airlines", "🛫")
    ]
)

st.rerun()
