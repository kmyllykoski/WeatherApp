import altair as alt
import streamlit as st
import pandas as pd
import numpy as np # Used for mock data generation, remove if using real df

# --- Mock Data Setup (Remove this block when using your actual Streamlit application) ---
# Assuming 'df', 'selected_parameter', and 'selected_stations' are defined
if 'df' not in locals():
    data = {
        'Station': ['Really Long Station Name Alpha', 'Shorter Station Bravo', 'Station Charlie - City Limits', 'Delta', 'Eco-Friendly Station Five'],
        'FMISID': [100, 101, 102, 103, 104],
        'Latitude': [60, 61, 62, 63, 64],
        'Longitude': [20, 21, 22, 23, 24],
        'Parameter': ['Temperature', 'Temperature', 'Temperature', 'Temperature', 'Temperature'],
        'Value': [25.5, 18.2, 30.1, 15.0, 22.8],
        'Unit': ['°C', '°C', '°C', '°C', '°C'],
        'Time': [pd.Timestamp.now()]*5
    }
    df = pd.DataFrame(data)
    selected_parameter = 'Temperature'
    selected_stations = df['Station'].tolist()
# --- End Mock Data Setup ---

# 1. Define the sort order explicitly (Descending by Value)
sort_order = alt.EncodingSortField(field='Value:Q', op='max', order='descending')

# 2. Define the main bar chart (67% width)
bar_chart = alt.Chart(df).mark_bar().encode(
    # X-axis for the bar values
    x=alt.X('Value:Q', title=f"{selected_parameter} ({df['Unit'].iloc[0]})"),
    
    # Y-axis MUST NOT show labels (axis=None) as the label chart handles this
    y=alt.Y('Station:N', title=None, sort=sort_order, axis=None), 
    
    color=alt.Color('Station:N', legend=None),
    tooltip=['Station:N', 'FMISID:N', 'Latitude:Q', 'Longitude:Q', 'Parameter:N', 'Value:Q', 'Unit:N', 'Time:T'],
).properties(
    # Set the width of the main bar area to stretch and fill remaining space
    # (The effective width will be 100% of the container minus 180px for the labels)
    width='container'
)

# 3. Define the Label Chart (33% width)
label_chart = alt.Chart(df).mark_text(
    align='left', 
    baseline='middle',
    color='black'
).encode(
    # Y-axis for alignment, must use the same sort and must NOT show an axis
    y=alt.Y('Station:N', title=None, sort=sort_order, axis=None), 
    
    # X-axis fixed position (value(5) places the text 5 pixels from the left edge)
    x=alt.value(5), 

    # The text itself is the Station name
    text=alt.Text('Station:N', fontSize=12) 
).properties(
    # Fixed width in pixels for the label column. 180px usually provides enough space
    # for long names, acting as the '33%' dedicated space.
    width=180 
)

# 4. Concatenate the two charts using alt.hconcat() and resolve shared scales
final_chart = alt.hconcat(label_chart, bar_chart).resolve_scale(
    y='shared' # Crucial: ensures the Y scales and positions are perfectly aligned
)

# Display the chart in Streamlit (assuming you are running this within a Streamlit app)
# st.altair_chart(final_chart, use_container_width=True)
# If not running in Streamlit, use .show() for testing:
# final_chart.show()
