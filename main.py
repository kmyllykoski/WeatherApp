import datetime as dt
from math import isnan
from fmiopendata.wfs import download_stored_query
import pickle
import json
import pprint
import streamlit as st
# from streamlit_dimensions import st_dimensions
import pandas as pd
import altair as alt
# import plotly.express as px

# Using https://github.com/pnuu/fmiopendata to download observation data from Finnish Meteorological Institute (FMI)


hours_to_download = 4 # how many hours of data to download
do_save_json = False
do_save_pretty_print = False
do_print_all_observation_times = False
do_print_observation_data_to_console = False

def save_pickle_file(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f)

def load_pickle_file(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)
    
def _convert(obj):
            # Recursively convert objects to JSON-serializable types,
            # converting datetime keys/values to "YYYY-MM-DDTHH:MM:SSZ".
            if isinstance(obj, dict):
                out = {}
                for k, v in obj.items():
                    # ensure JSON keys are strings; format datetimes as UTC ISO + Z
                    if isinstance(k, dt.datetime):
                        key = k.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    else:
                        key = str(k)
                    out[key] = _convert(v)
                return out
            if isinstance(obj, (list, tuple, set)):
                return [_convert(x) for x in obj]
            if isinstance(obj, dt.datetime):
                return obj.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if isinstance(obj, (int, float, str, bool)) or obj is None:
                return obj
            if hasattr(obj, "__dict__"):
                return _convert(vars(obj))
            return str(obj)

def save_json_file(data, filename):
    serializable = _convert(data)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)

def pretty_print_to_file(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        pprint.pprint(data, stream=f, width=120)

def get_data_from_file_or_download():

    # Check if there is a file named 'obs_full.pickle' in the current directory.
    # If so, load the data from there instead of downloading it again.
    try:
        obs = load_pickle_file("obs_full.pickle")
        print("Loaded observation data from obs_full.pickle")

        if do_save_json:
            save_json_file(obs.data, "obs_data.json")
            print("Saved observation data to obs_data.json")
        if do_save_pretty_print:
            pretty_print_to_file(obs.data, "obs_data.txt")
            print("Saved observation data to obs_data.txt")

    except FileNotFoundError:
        print("obs_full.pickle not found, downloading data from Finnish Meteorological Institute (FMI)...")

        end_time = dt.datetime.now(dt.timezone.utc)
        start_time = end_time - dt.timedelta(hours=hours_to_download)

        start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Retrieve the latest hour of data from a bounding box
        obs = download_stored_query("fmi::observations::weather::multipointcoverage",
                                    args=["bbox=18,55,35,75",
                                        "starttime=" + start_time,
                                        "endtime=" + end_time,
                                        "timeseries=True"])
        
        # --- Save the returned object to files (three options) ---

        # Always save entire obs object with pickle (binary)
        save_pickle_file(obs, "obs_full.pickle")
        print("Saved full observation data to obs_full.pickle")

        # Optionally save observation data as JSON
        if do_save_json:
            save_json_file(obs.data, "obs_data.json")
            print("Saved observation data to obs_data.json")

        # Optionally save observation data as pretty-printed text
        if do_save_pretty_print:
            pretty_print_to_file(obs.data, "obs_data.txt")
            print("Saved observation data to obs_data.txt")

    return obs

def print_observation_data_to_console(obs):
    weather_stations = list(sorted(obs.data.keys()))
    weather_stations_count = len(weather_stations)

    for station in weather_stations:
        print("-"*100)
        location = obs.location_metadata[station]
        fmisd = location['fmisid']
        latitude = location['latitude']
        longitude = location['longitude']
        print(f"{station}, FMISID: {fmisd}, lat: {latitude}, lon: {longitude}")

        timesteps = obs.data[station]['times']
        count_observations = len(timesteps)

        for parametri in sorted(obs.data[station].keys())[:-1]:  # Exclude the 'times' key at the end
            unit = obs.data[station][parametri]['unit']
            print(f"  {parametri:30} Observations {count_observations}, latest: {timesteps[-1]}  {obs.data[station][parametri]['values'][-1]} {unit}")

            if do_print_all_observation_times:
                for idx, ts in enumerate(timesteps):
                    value = obs.data[station][parametri]['values'][idx]
                    # check that value is not None or NaN. 'is Not None' does not catch NaN values.
                    if value is not None and not (isinstance(value, float) and isnan(value)):
                        print(f"    {ts}, {value} {unit}")
        
    print("=" * 100)
    print(f"Total weather stations: {weather_stations_count}")
    return

# helper: return True only if series contains at least one numeric, finite value
def _has_numeric_value(series):
    def _is_numeric_and_finite(v):
        try:
            f = float(v)
        except Exception:
            return False
        # import of isnan is at top; protects against non-float input
        return not (isinstance(f, float) and isnan(f))
    return series.apply(_is_numeric_and_finite).any()
    


print("Hello from weatherapp!")
obs = get_data_from_file_or_download()

if do_print_observation_data_to_console:
    print_observation_data_to_console(obs)

# obs = get_data_from_file_or_download()
# # MultiPoint.data  # The observation data
# # MultiPoint.location_metadata  # Location information for the observation locations

# weather_stations = list(sorted(obs.data.keys()))
# weather_stations_count = len(weather_stations)

# for station in weather_stations:
#     print("-"*100)
#     location = obs.location_metadata[station]
#     fmisd = location['fmisid']
#     latitude = location['latitude']
#     longitude = location['longitude']
#     print(f"{station}, FMISID: {fmisd}, lat: {latitude}, lon: {longitude}")

#     timesteps = obs.data[station]['times']
#     count_observations = len(timesteps)

#     for parametri in sorted(obs.data[station].keys())[:-1]:  # Exclude the 'times' key at the end
#         unit = obs.data[station][parametri]['unit']
#         print(f"  {parametri:30} Observations {count_observations}, latest: {timesteps[-1]}  {obs.data[station][parametri]['values'][-1]} {unit}")

#         if do_print_all_observations:
#             for idx, ts in enumerate(timesteps):
#                 value = obs.data[station][parametri]['values'][idx]
#                 # check that value is not None or NaN. 'is Not None' does not catch NaN values.
#                 if value is not None and not (isinstance(value, float) and isnan(value)):
#                     print(f"    {ts}, {value} {unit}")

# print("=" * 100)
# print(f"Total weather stations: {weather_stations_count}")
# return

st.set_page_config(layout="wide")
st.title("Weather Observations")
st.write("Observations from Finnish Meteorological Institute (FMI) weather stations \
             in the last 24 hours retrieved using Python package https://github.com/pnuu/fmiopendata \
             to handle request to FMI Open Data https://en.ilmatieteenlaitos.fi/open-data")
width_main_area_px = 920

# DataFrame for storing the only latest observation datapoint of each weather station

# Build a list of row dicts and construct the DataFrame once (avoid DataFrame.append)
rows = []
for station in obs.data.keys():
    location = obs.location_metadata[station]
    fmisid = location['fmisid']
    latitude = location['latitude']
    longitude = location['longitude']
    for parametri in obs.data[station].keys():
        if parametri == 'times':
            continue
        time_latest = obs.data[station]['times'][-1]  # Latest observation time in data as string
        unit = obs.data[station][parametri]['unit']
        value_latest = obs.data[station][parametri]['values'][-1]  # Latest observation value
        rows.append({
            "Station": station,
            "FMISID": fmisid,
            "Latitude": latitude,
            "Longitude": longitude,
            "Parameter": parametri,
            "Time": time_latest,
            "Value": value_latest,
            "Unit": unit
        })

df = pd.DataFrame(rows, columns=["Station", "FMISID", "Latitude", "Longitude", "Parameter", "Time", "Value", "Unit"])
# drop index  
df.reset_index(drop=True, inplace=True)



with st.container(width='stretch'):
    st.subheader(f"Observations during the last {hours_to_download} hours: {len(df)}")
    st.subheader("Number of weather stations: " + str(df['Station'].nunique()))
    # draw a horizontal line
    st.markdown("---")
    st.subheader("Latest observations for selected Parameter for all Stations")
    # ask user to select parameter to show
    parameter_options = df['Parameter'].unique().tolist() 
    parameter_options.sort() # sort options alphabetically
    # if there is "Air Temperature" in the options, select it by default
    if "Air Temperature" in parameter_options:
        default_index = parameter_options.index("Air Temperature")
    else:
        default_index = 0
    selected_parameter = st.selectbox("Select Parameter", parameter_options, index=default_index)

    # Filter the DataFrame based on the selected parameter
    filtered_df = df[df['Parameter'] == selected_parameter]

    # ask user to select sorting order by station name or latitude
    sort_order_options = ["Station Name", "Latitude"]
    selected_sort_order = st.selectbox("Select Sort Order", sort_order_options)
    if selected_sort_order == "Station Name":
        filtered_df = filtered_df.sort_values(by='Station', ascending=True)
    else:
        filtered_df = filtered_df.sort_values(by='Latitude', ascending=True)

    # with st.expander("Show all raw data"):
    #     st.dataframe(df)



    # Show the DataFrame in the Streamlit app
    st.write(filtered_df)

with st.container(width='stretch'):
    # user selects parameter to plot
    st.subheader("Observation of selected Parameter on selected Stations")
    parameter_options = df['Parameter'].unique().tolist()
    parameter_options.sort() # sort options alphabetically
    # if there is "Air Temperature" in the options, select it by default
    if "Air Temperature" in parameter_options:
        default_index = parameter_options.index("Air Temperature")
    else:
        default_index = 0
    selected_parameter = st.selectbox("Select Parameter to Plot", parameter_options, index=default_index)  #  key='parameter_plot'
    # select multiple stations
    station_options = df['Station'].unique().tolist()
    
    if "Porvoo Emäsalo" in station_options:
        # move "Porvoo Emäsalo" to the top if it exists and has a real numeric value for the selected parameter
        mask = (df['Station'] == "Porvoo Emäsalo") & (df['Parameter'] == selected_parameter)
        if _has_numeric_value(df.loc[mask, 'Value']):
            print("Porvoo Emäsalo has numeric value, moving to top of station options")
            print(df.loc[mask])
            station_options.remove("Porvoo Emäsalo")
            station_options.insert(0, "Porvoo Emäsalo")  # move to top
    
    if station_options[0] != 'Porvoo Emäsalo':
        if "Porvoo Kilpilahti satama" in station_options:
            mask = (df['Station'] == "Porvoo Kilpilahti satama") & (df['Parameter'] == selected_parameter)
            if _has_numeric_value(df.loc[mask, 'Value']):
                print("Porvoo Kilpilahti satama has numeric value, moving to top of station options")
                print(df.loc[mask])
                station_options.remove("Porvoo Kilpilahti satama")
                station_options.insert(0, "Porvoo Kilpilahti satama")

    if "Vantaa Helsinki-Vantaan lentoasema" in station_options:
        mask = (df['Station'] == "Vantaa Helsinki-Vantaan lentoasema") & (df['Parameter'] == selected_parameter)
        if _has_numeric_value(df.loc[mask, 'Value']):
            print("Vantaa Helsinki-Vantaan lentoasema has numeric value, moving to top of station options")
            print(df.loc[mask])
            station_options.remove("Vantaa Helsinki-Vantaan lentoasema")
            station_options.insert(0, "Vantaa Helsinki-Vantaan lentoasema")

    station_options_with_values = []
    for station in station_options:
        mask = (df['Station'] == station) & (df['Parameter'] == selected_parameter)
        if _has_numeric_value(df.loc[mask, 'Value']):
            if selected_parameter == "Snow depth":
                # only include stations with snow depth > 0
                # convert values robustly to numeric (None/strings -> NaN) and check any > 0
                vals = pd.to_numeric(df.loc[mask, 'Value'], errors='coerce')
                if (vals > 0).any():
                    station_options_with_values.append(station)
            else:
                station_options_with_values.append(station)

    selected_stations = st.multiselect("Select Stations to Plot", station_options_with_values, default=station_options_with_values[:5])
    # Filter the DataFrame based on the selected parameter and stations
    df = df[(df['Parameter'] == selected_parameter) & (df['Station'].isin(selected_stations))]
    if df.empty:
        st.write("No data available for the selected parameter and stations.")
        st.stop()

    # sort df by Value descending
    df = df.sort_values(by='Value', ascending=False)


##
with st.container(width='stretch'):
    # how much is the container width?
    width_bars = int(width_main_area_px * 0.67)
    width_labels = width_main_area_px - width_bars

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
        width=width_bars
    )

    # 3. Define the Label Chart (33% width)
    label_chart = alt.Chart(df).mark_text(
        align='left', 
        baseline='middle',
        color='white',
        fontSize=12 # <-- FIXED: fontSize property moved here
    ).encode(
        # Y-axis for alignment, must use the same sort and must NOT show an axis
        y=alt.Y('Station:N', title=None, sort=sort_order, axis=None), 
        
        # X-axis fixed position (value(5) places the text 5 pixels from the left edge)
        x=alt.value(5), 

        # The text itself is the Station name (no fontSize parameter here)
        text=alt.Text('Station:N') 
    ).properties(
        # Fixed width in pixels for the label column. 180px usually provides enough space
        # for long names, acting as the '33%' dedicated space.
        width=width_labels
    )

    # 4. Concatenate the two charts using alt.hconcat() and resolve shared scales
    final_chart = alt.hconcat(label_chart, bar_chart).resolve_scale(
        y='shared' # Crucial: ensures the Y scales and positions are perfectly aligned
    )

    # Display the chart in Streamlit (assuming you are running this within a Streamlit app)
    st.altair_chart(final_chart, width='stretch')
    # If not running in Streamlit, use .show() for testing:
    # final_chart.show()

with st.container(width='stretch'):
    st.subheader("Selected data")

    # Show the DataFrame in the Streamlit app
    st.write(df)
