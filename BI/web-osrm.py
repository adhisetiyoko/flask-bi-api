from flask import Flask, request, jsonify, send_file
import math
import requests
from datetime import datetime
import os

app = Flask(__name__)

class LocalDeliveryPricing:
    """
    Sistem perhitungan ongkir lokal dengan jarak real menggunakan OSRM
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
        self.osrm_server = "http://router.project-osrm.org"
    
    def get_route_osrm(self, origin_lat, origin_lng, dest_lat, dest_lng, route_preference="fastest"):
        """
        Dapatkan rute lengkap dari OSRM (untuk ditampilkan di peta)
        
        Args:
            route_preference: "fastest" (tercepat) atau "shortest" (terpendek)
        """
        try:
            url = f"{self.osrm_server}/route/v1/driving/{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
            
            params = {
                "overview": "full",
                "geometries": "geojson",
                "steps": "true",
                "alternatives": "true"  # Minta rute alternatif
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data["code"] == "Ok" and len(data["routes"]) > 0:
                # Pilih rute berdasarkan preferensi
                if route_preference == "shortest" and len(data["routes"]) > 1:
                    # Cari rute dengan jarak terpendek
                    selected_route = min(data["routes"], key=lambda r: r["distance"])
                else:
                    # Default: rute tercepat (index 0)
                    selected_route = data["routes"][0]
                
                route = selected_route
                
                # Ekstrak koordinat rute untuk peta
                route_coordinates = route["geometry"]["coordinates"]
                
                # Distance & Duration
                distance_m = route["distance"]
                distance_km = distance_m / 1000
                duration_s = route["duration"]
                duration_min = duration_s / 60
                
                # Ekstrak nama jalan
                road_names = []
                if "legs" in route:
                    for leg in route["legs"]:
                        if "steps" in leg:
                            for step in leg["steps"]:
                                road_name = step.get("name", "")
                                if road_name and road_name not in road_names:
                                    road_names.append(road_name)
                
                return {
                    "success": True,
                    "distance_km": round(distance_km, 2),
                    "duration_minutes": int(duration_min),
                    "distance_meters": int(distance_m),
                    "route_coordinates": route_coordinates,  # Untuk peta
                    "road_names": road_names[:5],
                    "total_roads": len(road_names)
                }
            else:
                return {"success": False, "error": "Tidak dapat menghitung rute"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def calculate_price(self, origin_lat, origin_lng, dest_lat, dest_lng, 
                       is_raining=False, vehicle_type="motor"):
        """
        Hitung ongkir berdasarkan koordinat
        """
        # Dapatkan rute dari OSRM
        route_data = self.get_route_osrm(origin_lat, origin_lng, dest_lat, dest_lng)
        
        if not route_data["success"]:
            return route_data
        
        distance_km = route_data["distance_km"]
        duration_minutes = route_data["duration_minutes"]
        
        # Validasi jarak
        if distance_km > self.config["max_distance_km"]:
            return {
                "success": False,
                "error": f"Jarak terlalu jauh! Maksimal {self.config['max_distance_km']} km"
            }
        
        if distance_km < self.config["min_distance_km"]:
            distance_km = self.config["min_distance_km"]
        
        # Hitung harga
        base_price = self.config["base_price"]
        vehicle_multiplier = 1.5 if vehicle_type == "mobil" else 1.0
        base_price = base_price * vehicle_multiplier
        
        # Tentukan tier berdasarkan total jarak
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
        
        # Surge pricing
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
            "total_roads": route_data["total_roads"]
        }

# Initialize pricing engine
pricing = LocalDeliveryPricing()

@app.route('/')
def index():
    # Pastikan file index.html ada di folder yang sama
    return send_file('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        
        origin_lat = float(data['origin_lat'])
        origin_lng = float(data['origin_lng'])
        dest_lat = float(data['dest_lat'])
        dest_lng = float(data['dest_lng'])
        vehicle_type = data.get('vehicle_type', 'motor')
        is_raining = data.get('is_raining', False)
        
        result = pricing.calculate_price(
            origin_lat, origin_lng,
            dest_lat, dest_lng,
            is_raining=is_raining,
            vehicle_type=vehicle_type
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    print("="*60)
    print("🚀 Starting Delivery Pricing Web App...")
    print("="*60)
    print("📍 URL: http://localhost:5000")
    print("📁 Make sure 'index.html' is in the same folder!")
    print("="*60)
    app.run(debug=True, port=5000)