import datetime as dt
from math import isnan
from fmiopendata.wfs import download_stored_query
import pickle
import json
import pprint

do_save_json = False
do_save_pretty_print = False
do_print_all_observations = True

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


def main():
    print("Hello from weatherapp!")

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
        start_time = end_time - dt.timedelta(hours=24)

        start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Retrieve the latest hour of data from a bounding box
        obs = download_stored_query("fmi::observations::weather::multipointcoverage",
                                    args=["bbox=18,55,35,75",
                                        "starttime=" + start_time,
                                        "endtime=" + end_time,
                                        "timeseries=True"])
        
        # --- Save the returned object to files (three options) ---

        # Save entire obs object with pickle (binary)
        save_pickle_file(obs, "obs_full.pickle")
        print("Saved full observation data to obs_full.pickle")

        if do_save_json:
            save_json_file(obs.data, "obs_data.json")
            print("Saved observation data to obs_data.json")

        if do_save_pretty_print:
            pretty_print_to_file(obs.data, "obs_data.txt")
            print("Saved observation data to obs_data.txt")

    # MultiPoint.data  # The observation data
    # MultiPoint.location_metadata  # Location information for the observation locations

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

            if do_print_all_observations:
                for idx, ts in enumerate(timesteps):
                    value = obs.data[station][parametri]['values'][idx]
                    # check that value is not None or NaN. 'is Not None' does not catch NaN values.
                    if value is not None and not (isinstance(value, float) and isnan(value)):
                        print(f"    {ts}, {value} {unit}")
    
    print("=" * 100)
    print(f"Total weather stations: {weather_stations_count}")
    return


if __name__ == "__main__":
    main()
