# --- Imports ---
import json          # for saving/loading the location cache to/from a file
import os             # for checking whether the cache file already exists
import re             # for pattern-matching text, used to clean up messy address strings
import pandas as pd    # for working with tables (DataFrames)
from geopy.geocoders import Nominatim          # the actual free geocoding service (address text -> coordinates)
from geopy.extra.rate_limiter import RateLimiter  # slows down requests so we don't get blocked for going too fast
from phase1_data_extraction import load_status_df    # reuses the function you built in Phase 1

# --- Constant: name of the file where we save geocoding results ---
CACHE_FILE = "location_cache.json"

# --- Set up the geocoder ---
geolocator = Nominatim(user_agent="rescue_dispatch_project_omar")
# user_agent is just a required label identifying your app to the free service

geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
# wraps the geocoder so it automatically waits 1 second between each lookup

# --- Load previously-saved results, if any exist, so we don't redo work ---
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        location_cache = json.load(f)   # load saved address->coordinates pairs from disk
else:
    location_cache = {}   # otherwise start with an empty dictionary


def clean_location(raw):
    if not isinstance(raw, str):
        return raw
    parts = [p.strip() for p in raw.split(",")]
    # Always keep just Road, City, Province, Country — drop everything after
    cleaned = ", ".join(parts[:4])
    return cleaned

def get_coords(address):
    address = clean_location(address)
    print(f"[DEBUG] Sending to geocoder: {repr(address)}")
    if address in location_cache:
        return location_cache[address]
    try:
        result = geocode(address)
        coords = (result.latitude, result.longitude) if result else (None, None)
    except Exception as e:
        print(f"Error geocoding '{address}': {e}")
        coords = (None, None)
    location_cache[address] = coords
    return coords

def get_coords_with_fallback(address):
    coords = get_coords(address)
    if coords != (None, None):   # now a fair comparison, tuple vs tuple
        return coords

    parts = [p.strip() for p in clean_location(address).split(",")]
    if len(parts) > 1:
        broader = ", ".join(parts[1:])
        return get_coords(broader)
    return (None, None)


def save_cache():
    """Writes the current cache to disk, so results persist between runs."""
    with open(CACHE_FILE, "w") as f:
        json.dump(location_cache, f)


def add_coordinates():
    """Main function for Phase 2: returns the currently-off vehicles, with coordinates added."""
    status_df = load_status_df()   # run Phase 1's full pipeline, get the merged status table back

    off_vehicles = status_df[status_df["current_status"] == "off"].copy()
    # keep only vehicles currently marked "off" — these are your free-vehicle candidates
    # .copy() avoids a pandas warning about modifying a "view" of the original table

    unique_locations = off_vehicles["last_off_location"].dropna().unique()
    # get the distinct location strings among these vehicles, ignoring missing values

    for loc in unique_locations:
        get_coords_with_fallback(loc)   # geocode each unique address once, filling up the cache

    save_cache()   # write all newly-geocoded results to disk immediately

    off_vehicles["off_lat"] = off_vehicles["last_off_location"].map(
        lambda x: location_cache.get(clean_location(x), (None, None))[0]
    )
    # for each row, look up its cleaned address in the cache and pull out the latitude

    off_vehicles["off_lon"] = off_vehicles["last_off_location"].map(
        lambda x: location_cache.get(clean_location(x), (None, None))[1]
    )
    # same as above, but for longitude

    return off_vehicles   # final table: off vehicles + their real coordinates


if __name__ == "__main__":
    result = add_coordinates()
    print(result[["Grouping", "last_off_location", "off_lat", "off_lon"]])

    total = len(result)
    failed = result["off_lat"].isna().sum()
    succeeded = total - failed
    print(f"Total vehicles: {total}")
    print(f"Successfully geocoded: {succeeded}")
    print(f"Failed to geocode: {failed}")

    failed_locations = result[result["off_lat"].isna()]["last_off_location"].unique()
    for loc in failed_locations:
        print(repr(loc))
