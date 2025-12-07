import googlemaps

API_KEY = "AIzaSyAqvr64aQeljD9lvukwnW9OipiRicXJ55I"

print(f"Testing API Key: {API_KEY[:20]}...")

try:
    gmaps = googlemaps.Client(key=API_KEY)
    
    # Test Distance Matrix
    result = gmaps.distance_matrix(
        origins=["Yogyakarta"],
        destinations=["Jakarta"],
        mode="driving"
    )
    
    if result['status'] == 'OK':
        print("✅ Distance Matrix API: BERHASIL!")
        print(f"   Jarak: {result['rows'][0]['elements'][0]['distance']['text']}")
    else:
        print(f"❌ Error: {result['status']}")
        
except Exception as e:
    print(f"❌ Error: {e}")