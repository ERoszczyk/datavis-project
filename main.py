import streamlit as st
from st_pages import Page, show_pages
import pandas as pd
import numpy as np

# Function to load data in chunks
@st.cache_data(persist=True)
def load_data_in_chunks(file_path, chunk_size=100000):
    chunk_list = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size, low_memory=False):
        chunk['ARRIVAL_TIME'] = pd.to_datetime(chunk['ARRIVAL_TIME'], format='%H:%M:%S')
        chunk['DATE'] = pd.to_datetime(chunk['DATE'])
        chunk['ARRIVAL_DELAY'] = chunk['ARRIVAL_DELAY'].astype(np.float32)
        chunk['DEPARTURE_DELAY'] = chunk['DEPARTURE_DELAY'].astype(np.float32)
        chunk_list.append(chunk)
    df = pd.concat(chunk_list, ignore_index=True)
    return df

# Load dataset and store it in session state if not already present
if 'df' not in st.session_state:
    # st.session_state.df = load_data_in_chunks('2015_dataset/merged_1k_sample.csv')
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
