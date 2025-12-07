from flask import Flask, request, jsonify, send_file
import math
import requests
from datetime import datetime
import os

app = Flask(__name__)

# ⚠️ PENTING: Ganti dengan API key GraphHopper kamu!
GRAPHHOPPER_API_KEY = "3fe24c19-ae88-408b-9290-670fedbe48f1"

class LocalDeliveryPricing:
    """
    Sistem perhitungan ongkir lokal dengan GraphHopper API
    Routing lebih akurat dari OSRM!
    """
    
    def __init__(self, config=None):
        self.config = config or {
            "base_price": 5000,
            "price_per_km": 2500,
            "min_distance_km": 0.5,
            "max_distance_km": 100,
            "min_charge": 7000,
            "platform_fee_percent": 10,
            "surge_hours": [7, 8, 12, 13, 18, 19],
            "surge_multiplier": 1.3,
            "rain_multiplier": 1.2,
            "peak_day_multiplier": 1.1,
            "price_tiers": [
                {"min_km": 0, "max_km": 5, "price_per_km": 2500},
                {"min_km": 5, "max_km": 15, "price_per_km": 2000},
                {"min_km": 15, "max_km": 30, "price_per_km": 1800},
                {"min_km": 30, "max_km": 999, "price_per_km": 1500},
            ]
        }
        self.graphhopper_url = "https://graphhopper.com/api/1/route"
        self.geocoding_url = "https://graphhopper.com/api/1/geocode"
    
    def geocode(self, query, limit=5):
        """
        Geocoding: Ubah nama tempat menjadi koordinat
        """
        try:
            params = {
                "q": query,
                "locale": "id",
                "limit": limit,
                "key": GRAPHHOPPER_API_KEY
            }
            
            response = requests.get(self.geocoding_url, params=params, timeout=10)
            data = response.json()
            
            if "hits" in data and len(data["hits"]) > 0:
                results = []
                for hit in data["hits"]:
                    results.append({
                        "name": hit.get("name", ""),
                        "full_address": hit.get("name", "") + ", " + hit.get("city", "") + ", " + hit.get("country", ""),
                        "lat": hit["point"]["lat"],
                        "lng": hit["point"]["lng"],
                        "city": hit.get("city", ""),
                        "country": hit.get("country", "")
                    })
                return {"success": True, "results": results}
            else:
                return {"success": False, "error": "Lokasi tidak ditemukan"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def reverse_geocode(self, lat, lng):
        """
        Reverse Geocoding: Ubah koordinat menjadi nama tempat
        """
        try:
            params = {
                "point": f"{lat},{lng}",
                "locale": "id",
                "key": GRAPHHOPPER_API_KEY,
                "reverse": "true"
            }
            
            response = requests.get(self.geocoding_url, params=params, timeout=10)
            data = response.json()
            
            if "hits" in data and len(data["hits"]) > 0:
                hit = data["hits"][0]
                return {
                    "success": True,
                    "name": hit.get("name", "Lokasi Tidak Dikenal"),
                    "full_address": hit.get("name", "") + ", " + hit.get("city", "") + ", " + hit.get("country", ""),
                    "city": hit.get("city", ""),
                    "country": hit.get("country", "")
                }
            else:
                return {"success": False, "error": "Alamat tidak ditemukan"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_route_graphhopper(self, origin_lat, origin_lng, dest_lat, dest_lng, route_preference="shortest"):
        """
        Dapatkan rute dari GraphHopper API
        """
        try:
            params = {
                "point": [f"{origin_lat},{origin_lng}", f"{dest_lat},{dest_lng}"],
                "vehicle": "car",
                "locale": "id",
                "key": GRAPHHOPPER_API_KEY,
                "points_encoded": False,
                "instructions": True,
                "algorithm": "alternative_route",
                "alternative_route.max_paths": 3
            }
            
            if route_preference == "shortest":
                params["weighting"] = "shortest"
            else:
                params["weighting"] = "fastest"
            
            print(f"🔄 Menghubungi GraphHopper API (mode: {route_preference})...")
            response = requests.get(self.graphhopper_url, params=params, timeout=15)
            data = response.json()
            
            if "paths" in data and len(data["paths"]) > 0:
                route = data["paths"][0]
                
                distance_m = route["distance"]
                distance_km = distance_m / 1000
                duration_ms = route["time"]
                duration_min = duration_ms / 60000
                
                route_coordinates = []
                if "points" in route and "coordinates" in route["points"]:
                    route_coordinates = route["points"]["coordinates"]
                
                road_names = []
                if "instructions" in route:
                    for instruction in route["instructions"]:
                        road_name = instruction.get("street_name", "")
                        if road_name and road_name not in road_names and road_name != "":
                            road_names.append(road_name)
                
                alternatives = []
                if len(data["paths"]) > 1:
                    for i, alt_route in enumerate(data["paths"][1:], start=2):
                        alt_distance_km = alt_route["distance"] / 1000
                        alt_duration_min = alt_route["time"] / 60000
                        alternatives.append({
                            "route_number": i,
                            "distance_km": round(alt_distance_km, 2),
                            "duration_minutes": int(alt_duration_min),
                            "distance_diff": round(alt_distance_km - distance_km, 2)
                        })
                
                print(f"✅ Berhasil! Jarak: {distance_km:.2f} km, Waktu: {int(duration_min)} menit")
                
                return {
                    "success": True,
                    "distance_km": round(distance_km, 2),
                    "duration_minutes": int(duration_min),
                    "distance_meters": int(distance_m),
                    "route_coordinates": route_coordinates,
                    "road_names": road_names[:5],
                    "total_roads": len(road_names),
                    "alternatives": alternatives,
                    "service": "GraphHopper"
                }
            else:
                error_msg = data.get("message", "Tidak dapat menghitung rute")
                print(f"⚠️  GraphHopper Error: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            print(f"⚠️  Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def calculate_price(self, origin_lat, origin_lng, dest_lat, dest_lng, 
                       is_raining=False, vehicle_type="motor", route_preference="shortest"):
        """
        Hitung ongkir berdasarkan koordinat dengan GraphHopper
        """
        route_data = self.get_route_graphhopper(origin_lat, origin_lng, dest_lat, dest_lng, route_preference)
        
        if not route_data["success"]:
            return route_data
        
        distance_km = route_data["distance_km"]
        duration_minutes = route_data["duration_minutes"]
        
        if distance_km > self.config["max_distance_km"]:
            return {
                "success": False,
                "error": f"Jarak terlalu jauh! Maksimal {self.config['max_distance_km']} km"
            }
        
        if distance_km < self.config["min_distance_km"]:
            distance_km = self.config["min_distance_km"]
        
        base_price = self.config["base_price"]
        vehicle_multiplier = 1.5 if vehicle_type == "mobil" else 1.0
        base_price = base_price * vehicle_multiplier
        
        selected_tier = None
        for tier in self.config["price_tiers"]:
            if tier["min_km"] <= distance_km < tier["max_km"]:
                selected_tier = tier
                break
        
        if selected_tier is None:
            selected_tier = self.config["price_tiers"][-1]
        
        price_per_km = selected_tier["price_per_km"] * vehicle_multiplier
        distance_charge = distance_km * price_per_km
        
        subtotal = base_price + distance_charge
        
        multiplier = 1.0
        surge_reasons = []
        
        current_hour = datetime.now().hour
        if current_hour in self.config["surge_hours"]:
            multiplier *= self.config["surge_multiplier"]
            surge_reasons.append(f"Jam sibuk (+{int((self.config['surge_multiplier']-1)*100)}%)")
        
        if is_raining:
            multiplier *= self.config["rain_multiplier"]
            surge_reasons.append(f"Cuaca hujan (+{int((self.config['rain_multiplier']-1)*100)}%)")
        
        if datetime.now().weekday() >= 5:
            multiplier *= self.config["peak_day_multiplier"]
            surge_reasons.append(f"Weekend (+{int((self.config['peak_day_multiplier']-1)*100)}%)")
        
        total_with_surge = subtotal * multiplier
        platform_fee = total_with_surge * (self.config["platform_fee_percent"] / 100)
        final_price = total_with_surge + platform_fee
        
        if final_price < self.config["min_charge"]:
            final_price = self.config["min_charge"]
        
        final_price = math.ceil(final_price / 100) * 100
        
        return {
            "success": True,
            "distance_km": distance_km,
            "distance_meters": route_data["distance_meters"],
            "duration_minutes": duration_minutes,
            "base_price": int(base_price),
            "distance_charge": int(distance_charge),
            "tier_range": f"{selected_tier['min_km']}-{selected_tier['max_km']} km",
            "rate_per_km": int(price_per_km),
            "subtotal": int(subtotal),
            "surge_multiplier": round(multiplier, 2),
            "surge_reasons": surge_reasons,
            "price_with_surge": int(total_with_surge),
            "platform_fee": int(platform_fee),
            "final_price": int(final_price),
            "vehicle_type": vehicle_type,
            "route_coordinates": route_data["route_coordinates"],
            "road_names": route_data["road_names"],
            "total_roads": route_data["total_roads"],
            "alternatives": route_data["alternatives"],
            "routing_service": route_data["service"]
        }

# Initialize pricing engine
pricing = LocalDeliveryPricing()

# Simple cache untuk geocoding (hindari request duplikat)
geocoding_cache = {}
route_cache = {}

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/geocode', methods=['POST'])
def geocode():
    """
    Endpoint untuk search lokasi (nama → koordinat)
    """
    try:
        data = request.json
        query = data.get('query', '')
        
        if not query:
            return jsonify({"success": False, "error": "Query tidak boleh kosong"})
        
        result = pricing.geocode(query)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/reverse-geocode', methods=['POST'])
def reverse_geocode():
    """
    Endpoint untuk reverse geocoding (koordinat → nama)
    """
    try:
        data = request.json
        lat = float(data.get('lat'))
        lng = float(data.get('lng'))
        
        result = pricing.reverse_geocode(lat, lng)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        if GRAPHHOPPER_API_KEY == "YOUR_API_KEY_HERE":
            return jsonify({
                "success": False, 
                "error": "⚠️ API Key GraphHopper belum diisi!"
            })
        
        data = request.json
        
        origin_lat = float(data['origin_lat'])
        origin_lng = float(data['origin_lng'])
        dest_lat = float(data['dest_lat'])
        dest_lng = float(data['dest_lng'])
        vehicle_type = data.get('vehicle_type', 'motor')
        is_raining = data.get('is_raining', False)
        route_preference = data.get('route_preference', 'shortest')
        
        result = pricing.calculate_price(
            origin_lat, origin_lng,
            dest_lat, dest_lng,
            is_raining=is_raining,
            vehicle_type=vehicle_type,
            route_preference=route_preference
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    print("="*60)
    print("🚀 Starting Delivery Pricing Web App (GraphHopper)")
    print("="*60)
    
    if GRAPHHOPPER_API_KEY == "YOUR_API_KEY_HERE":
        print("⚠️  WARNING: API Key GraphHopper belum diisi!")
    else:
        print("✅ API Key terdeteksi!")
    
    print("="*60)
    print("📍 URL: http://localhost:5000")
    print("📁 Make sure 'index.html' is in the same folder!")
    print("="*60)
    print("\n✨ Fitur:")
    print("   • Search lokasi (geocoding)")
    print("   • Gunakan lokasi GPS device")
    print("   • Klik peta untuk set lokasi")
    print("   • Reverse geocoding (koordinat → nama)")
    print("="*60)
    app.run(debug=True, port=5000)