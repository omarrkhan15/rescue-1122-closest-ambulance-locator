from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="rescue_dispatch_project_omar")

# Paste in one REAL location string from your Excel data here
real_location = "tipu sultan road,,pechs,karachi,sindh,pakistan"  # <-- use the FULL actual string from your data, not shortened

print(repr(real_location))   # shows the exact raw text, hidden characters and all

result = geolocator.geocode(real_location)
print(result)