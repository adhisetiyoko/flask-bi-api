import googlemaps

gmaps = googlemaps.Client(key="API_KEY_KAMU")

origin = "Jakarta"
destination = "Bandung"

result = gmaps.directions(
    origin,
    destination,
    mode="driving",
    units="metric"
)

distance = result[0]['legs'][0]['distance']['text']
duration = result[0]['legs'][0]['duration']['text']

print("Jarak:", distance)
print("Waktu tempuh:", duration)
