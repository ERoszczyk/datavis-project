import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import streamlit as st
from streamlit_plotly_events import plotly_events

scale = [[0.0, 'rgb(0,100,0)'], [0.2, 'rgb(34,139,34)'],
         [0.4, 'rgb(60,179,60)'], [0.6, 'rgb(173,255,47)'],
         [0.8, 'rgb(255,215,0)'], [1.0, 'rgb(255,99,71)']]

def clean_data(df):
    """Clean the dataset by removing or filling NaN values."""
    required_columns = ['LONGITUDE_x', 'LATITUDE_x', 'LONGITUDE_y', 'LATITUDE_y', 'Percentage Delayed', 'ARRIVAL_TIME', 'DATE']
    if all(column in df.columns for column in required_columns):
        df = df.dropna(subset=required_columns)
        df.loc[:, 'Percentage Delayed'] = pd.to_numeric(df['Percentage Delayed'], errors='coerce').fillna(0)
        df = df.dropna(subset=['Percentage Delayed'])
    else:
        missing_cols = [col for col in required_columns if col not in df.columns]
        st.error(f"Missing columns in the dataset: {missing_cols}")
        df = pd.DataFrame(columns=required_columns)  # Return an empty DataFrame with required columns
    return df

def draw_map_with_mean_delay(df, start_date, end_date, start_time, end_time):
    df = clean_data(df)
    if df.empty:
        st.warning("The dataset is empty or missing required columns.")
        return

    mask = (df['DATE'] >= start_date) & (df['DATE'] <= end_date) & (
            pd.to_datetime(df['ARRIVAL_TIME'], format='%H:%M:%S').dt.time >= start_time) & (
                   pd.to_datetime(df['ARRIVAL_TIME'], format='%H:%M:%S').dt.time <= end_time)
    df = df.loc[mask]

    # Aggregate data by airports
    aggregated_df = df.groupby(['AIRPORT_x', 'CITY_x', 'STATE_x', 'LATITUDE_x', 'LONGITUDE_x'], as_index=False).agg({
        'ARRIVAL_DELAY': 'mean',
        'Percentage Delayed': 'mean'
    }).round(2)

    trace = go.Scattergeo(
        lon=aggregated_df['LONGITUDE_x'],
        lat=aggregated_df['LATITUDE_x'],
        text=('Airport: ' + aggregated_df['AIRPORT_x'] + '<br>'
              + 'City: ' + aggregated_df['CITY_x'] + '<br>'
              + 'State: ' + aggregated_df['STATE_x'] + '<br>'
              + 'Average Arrival Delay: ' + aggregated_df['ARRIVAL_DELAY'].astype(str) + ' mins<br>'
              + 'Percentage of delayed flights: ' + aggregated_df['Percentage Delayed'].astype(str) + '%<br>'),
        mode='markers',
        marker=dict(
            autocolorscale=False,
            cmax=aggregated_df['Percentage Delayed'].max(),
            cmin=0,
            color=aggregated_df['Percentage Delayed'],
            colorbar=dict(title="Percentage of Delay (%)"),
            colorscale=px.colors.sequential.YlOrRd,
            line=dict(
                color="rgba(102,102,102)",
                width=1
            ),
            opacity=0.8,
            size=8
        )
    )

    layout = go.Layout(
        showlegend=False,
        geo=dict(scope='north america',
                 projection=dict(type='natural earth'),
                 showlakes=False,
                 showland=True,
                 lakecolor='rgb(95,145,237)',
                 landcolor='rgb(250,250,250)',
                 ),
        margin=go.layout.Margin(
            l=20,
            r=20,
            b=30,
            t=20,
            pad=30
        ),
        autosize=True
    )

    fig = go.Figure(data=[trace], layout=layout)
    selected_airport = plotly_events(fig)
    if selected_airport:
        nr = selected_airport[0]['pointIndex']
        airport = aggregated_df.iloc[nr]['AIRPORT_x']
        st.session_state.selected_airport = airport

def draw_routes(df, departure_cities, arrival_cities, departure_airports, arrival_airports):
    df = clean_data(df)
    if df.empty:
        st.warning("The dataset is empty or missing required columns.")
        return

    if len(departure_cities) > 0:
        df = df[df['CITY_x'].isin(departure_cities)]
    if len(arrival_cities) > 0:
        df = df[df['CITY_y'].isin(arrival_cities)]
    if len(departure_airports) > 0:
        df = df[df['AIRPORT_x'].isin(departure_airports)]
    if len(arrival_airports) > 0:
        df = df[df['AIRPORT_y'].isin(arrival_airports)]

    # Aggregate data by routes
    aggregated_df = df.groupby(
        ['AIRPORT_x', 'AIRPORT_y', 'CITY_x', 'CITY_y', 'LATITUDE_x', 'LONGITUDE_x', 'LATITUDE_y', 'LONGITUDE_y'],
        as_index=False)['ARRIVAL_DELAY'].mean()

    # draw the airport points in the map
    data = [dict(
        type='scattergeo',
        lat=aggregated_df['LATITUDE_x'],
        lon=aggregated_df['LONGITUDE_x'],
        marker=dict(
            color='#FFD700',
            line=dict(
                color="rgba(102,102,102)",
                width=1
            ),
            opacity=0.8,
            size=6,
        ),
        mode='markers',
        name='',
        hoverinfo='skip'  # Disable hoverinfo for points
    )]
    data += [dict(
        type='scattergeo',
        lat=aggregated_df['LATITUDE_y'],
        lon=aggregated_df['LONGITUDE_y'],
        marker=dict(
            color='#FFD700',
            line=dict(
                color="rgba(102,102,102)",
                width=1
            ),
            opacity=0.8,
            size=6,
        ),
        mode='markers',
        name='',
        hoverinfo='skip'  # Disable hoverinfo for points
    )]

    # draw the flight route in the map
    for i in range(aggregated_df.shape[0]):
        row = aggregated_df.iloc[i]
        avg_delay = row['ARRIVAL_DELAY']
        data += [dict(
            type="scattergeo",
            lat=[row['LATITUDE_x'], row['LATITUDE_y']],
            lon=[row['LONGITUDE_x'], row['LONGITUDE_y']],
            mode="lines",
            hoverinfo='text',  # Enable hoverinfo for lines
            text=('From: ' + row['AIRPORT_x']
                  + '<br>To: ' + row['AIRPORT_y']
                  + '<br>Avg. Delay: ' + str(round(avg_delay, 2)) + ' mins'),
            line=dict(
                color='#4682B4',
                width=1
            ),
            opacity=0.8,
            name=''
        )]

    # layout
    layout = go.Layout(
        geo=dict(
            scope='north america',
            projection=dict(type="azimuthal equal area"),
            showlakes=False,
            showland=True,
            lakecolor='rgb(95,145,237)',
            landcolor='rgb(250,250,250)'
        ),
        margin=go.layout.Margin(
            l=20,
            r=80,
            b=30,
            t=20,
            pad=30
        ),
        autosize=True,
        showlegend=False
    )

    fig = go.Figure(data=data, layout=layout)

    selected_route = plotly_events(fig)
    if selected_route:
        nr = selected_route[0]['curveNumber']
        airport_dep = aggregated_df.iloc[nr - 2]['AIRPORT_x']
        airport_arr = aggregated_df.iloc[nr - 2]['AIRPORT_y']
        st.session_state.route_origin = airport_dep
        st.session_state.route_destination = airport_arr

