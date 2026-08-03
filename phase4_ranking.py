from math import radians, sin, cos, sqrt, atan2
import requests
from phase2_geocode import add_coordinates

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    lat1_r, lon1_r = radians(lat1), radians(lon1)
    lat2_r, lon2_r = radians(lat2), radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def get_road_distance(lat1, lon1, lat2, lon2):
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
    try:
        response = requests.get(url, params={"overview": "false"}, timeout=5)
        data = response.json()
        if data.get("code") == "Ok":
            route = data["routes"][0]
            return route["distance"] / 1000, route["duration"] / 60
        return None, None
    except Exception as e:
        print(f"Error getting road distance: {e}")
        return None, None


def rank_nearest_vehicles_two_stage(incident_lat, incident_lon, off_vehicles_df, top_n=3, prefilter_n=8):
    df = off_vehicles_df.copy()
    df["straight_line_km"] = df.apply(
        lambda row: haversine_distance(incident_lat, incident_lon, row["off_lat"], row["off_lon"]),
        axis=1
    )
    shortlist = df.sort_values("straight_line_km").head(prefilter_n).copy()

    def get_distance_with_fallback(row):
        dist, eta = get_road_distance(incident_lat, incident_lon, row["off_lat"], row["off_lon"])
        if dist is None:
            # OSRM unreachable — fall back to straight-line distance, rough ETA estimate
            dist = row["straight_line_km"]
            eta = (dist / 30) * 60  # assume ~30 km/h average city speed as a rough estimate
        return dist, eta

    results = shortlist.apply( get_distance_with_fallback,
        axis=1)

    shortlist["distance_km"] = results.apply(lambda x: x[0])
    shortlist["eta_min"] = results.apply(lambda x: x[1])
    TRAFFIC_FACTOR = 2.1  # rough adjustment for typical Karachi congestion
    shortlist["eta_min_adjusted"] = shortlist["eta_min"] * TRAFFIC_FACTOR
    shortlist = shortlist.dropna(subset=["distance_km"])

    return shortlist.sort_values("distance_km").head(top_n)[
        ["Grouping", "last_off_location", "distance_km","eta_min", "eta_min_adjusted", "off_lat", "off_lon"]
    ]



if __name__ == "__main__":

    off_vehicles = add_coordinates()
    off_vehicles = off_vehicles.dropna(subset=["off_lat", "off_lon"]).reset_index(drop=True)

    # test incident location — use a known real coordinate from earlier testing
    test_lat, test_lon = 24.8607, 67.0011  # example Karachi coordinate

    ranked = rank_nearest_vehicles_two_stage(test_lat, test_lon, off_vehicles)
    print(ranked)