import math
import requests
from datetime import datetime

class LocalDeliveryPricing:
    """
    Sistem perhitungan ongkir lokal dengan jarak real menggunakan OSRM
    Otomatis mencari rute jalan terdekat
    """
    
    def __init__(self, config=None):
        """
        Inisialisasi dengan konfigurasi harga
        """
        self.config = config or {
            "base_price": 5000,          # Harga dasar (Rp)
            "price_per_km": 2500,        # Harga per kilometer (Rp)
            "min_distance_km": 0.5,      # Jarak minimum (km)
            "max_distance_km": 100,      # Jarak maksimum (km)
            "min_charge": 7000,          # Biaya minimum (Rp)
            "platform_fee_percent": 10,  # Fee platform (%)
            "surge_hours": [7, 8, 12, 13, 18, 19],  # Jam sibuk
            "surge_multiplier": 1.3,     # Pengali saat surge (1.3 = +30%)
            "rain_multiplier": 1.2,      # Pengali saat hujan (1.2 = +20%)
            "peak_day_multiplier": 1.1,  # Weekend/hari libur (1.1 = +10%)
            # Tier harga berdasarkan TOTAL jarak (bukan per segmen)
            # Jika total jarak masuk range, SEMUA km pakai harga tier tsb
            "price_tiers": [
                {"min_km": 0, "max_km": 5, "price_per_km": 2500},      # 0-5 km total: Rp 2.500/km
                {"min_km": 5, "max_km": 15, "price_per_km": 2000},     # 5-15 km total: Rp 2.000/km
                {"min_km": 15, "max_km": 30, "price_per_km": 1800},    # 15-30 km total: Rp 1.800/km
                {"min_km": 30, "max_km": 999, "price_per_km": 1500},   # >30 km total: Rp 1.500/km
            ]
        }
        self.osrm_server = "http://router.project-osrm.org"
    
    def get_distance_osrm(self, origin_lat, origin_lng, dest_lat, dest_lng, vehicle_type="motor"):
        """
        Hitung jarak dan durasi menggunakan OSRM (otomatis cari rute jalan terdekat)
        
        Args:
            origin_lat: Latitude asal
            origin_lng: Longitude asal
            dest_lat: Latitude tujuan
            dest_lng: Longitude tujuan
            vehicle_type: 'motor' atau 'mobil'
        
        Returns:
            Dict dengan distance_km, duration_minutes, dan detail rute
        """
        try:
            # OSRM format: longitude,latitude (KEBALIK dari lat,lng!)
            # OSRM otomatis mencari rute jalan terdekat
            url = f"{self.osrm_server}/route/v1/driving/{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
            
            params = {
                "overview": "full",        # Ambil detail rute lengkap
                "alternatives": "true",    # Cari alternatif rute
                "steps": "true",          # Ambil step-by-step untuk detail
                "geometries": "geojson"   # Format geometri
            }
            
            print(f"🔄 Mencari rute jalan terdekat via OSRM...")
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data["code"] == "Ok" and len(data["routes"]) > 0:
                # Ambil rute terbaik (index 0)
                best_route = data["routes"][0]
                
                # Distance dalam meter, Duration dalam detik
                distance_m = best_route["distance"]
                distance_km = distance_m / 1000
                duration_s = best_route["duration"]
                duration_min = duration_s / 60
                
                # Ekstrak informasi jalan yang dilalui
                road_names = []
                if "legs" in best_route:
                    for leg in best_route["legs"]:
                        if "steps" in leg:
                            for step in leg["steps"]:
                                road_name = step.get("name", "Jalan tanpa nama")
                                if road_name and road_name not in road_names and road_name != "Jalan tanpa nama":
                                    road_names.append(road_name)
                
                # Info alternatif rute jika ada
                alternatives = []
                if len(data["routes"]) > 1:
                    for i, alt_route in enumerate(data["routes"][1:], start=2):
                        alt_distance_km = alt_route["distance"] / 1000
                        alt_duration_min = alt_route["duration"] / 60
                        alternatives.append({
                            "route_number": i,
                            "distance_km": round(alt_distance_km, 2),
                            "duration_minutes": int(alt_duration_min),
                            "time_diff": int(alt_duration_min - duration_min)
                        })
                
                print(f"✅ Berhasil! Ditemukan {len(data['routes'])} rute alternatif")
                
                return {
                    "success": True,
                    "distance_km": round(distance_km, 2),
                    "duration_minutes": int(duration_min),
                    "distance_meters": int(distance_m),
                    "road_names": road_names[:5],  # 5 jalan utama
                    "total_roads": len(road_names),
                    "alternatives": alternatives,
                    "method": "OSRM (rute jalan terdekat)"
                }
            else:
                error_msg = data.get('message', 'Unknown error')
                print(f"⚠️  OSRM Error: {data.get('code', 'Unknown')} - {error_msg}")
                return {"success": False, "error": f"Tidak dapat menghitung rute: {error_msg}"}
                
        except requests.exceptions.Timeout:
            print("⚠️  Timeout! OSRM server terlalu lama merespon.")
            return {"success": False, "error": "Timeout koneksi ke OSRM"}
        except requests.exceptions.ConnectionError:
            print("⚠️  Tidak dapat terhubung ke OSRM server.")
            return {"success": False, "error": "Tidak dapat terhubung ke server"}
        except Exception as e:
            print(f"⚠️  Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def calculate_price(self, origin_lat, origin_lng, dest_lat, dest_lng, 
                       is_raining=False, vehicle_type="motor"):
        """
        Hitung ongkir berdasarkan koordinat dengan jarak real (OSRM)
        Otomatis menggunakan rute jalan terdekat
        """
        # Dapatkan jarak real dari OSRM (otomatis cari rute terdekat)
        route_data = self.get_distance_osrm(origin_lat, origin_lng, dest_lat, dest_lng, vehicle_type)
        
        if not route_data["success"]:
            return route_data  # Return error
        
        distance_km = route_data["distance_km"]
        duration_minutes = route_data["duration_minutes"]
        
        # Validasi jarak
        if distance_km > self.config["max_distance_km"]:
            return {
                "success": False,
                "error": f"Jarak terlalu jauh! Maksimal {self.config['max_distance_km']} km",
                "distance_km": distance_km
            }
        
        if distance_km < self.config["min_distance_km"]:
            distance_km = self.config["min_distance_km"]
        
        # Hitung harga dasar
        base_price = self.config["base_price"]
        
        # Sesuaikan base price berdasarkan jenis kendaraan
        vehicle_multiplier = 1.5 if vehicle_type == "mobil" else 1.0
        base_price = base_price * vehicle_multiplier
        
        # Tentukan tier berdasarkan TOTAL jarak
        # Semua kilometer menggunakan harga tier yang sesuai total jarak
        selected_tier = None
        for tier in self.config["price_tiers"]:
            if tier["min_km"] <= distance_km < tier["max_km"]:
                selected_tier = tier
                break
        
        # Jika tidak ada tier yang cocok, pakai tier terakhir
        if selected_tier is None:
            selected_tier = self.config["price_tiers"][-1]
        
        # Hitung biaya jarak dengan harga tier yang dipilih
        price_per_km = selected_tier["price_per_km"] * vehicle_multiplier
        distance_charge = distance_km * price_per_km
        
        # Info tier yang digunakan
        tier_info = {
            "tier_range": f"{selected_tier['min_km']}-{selected_tier['max_km']} km",
            "total_distance": distance_km,
            "rate_per_km": int(price_per_km),
            "total_charge": int(distance_charge)
        }
        
        # Total sebelum multiplier
        subtotal = base_price + distance_charge
        
        # Apply surge pricing
        multiplier = 1.0
        surge_reasons = []
        
        # Cek jam sibuk
        current_hour = datetime.now().hour
        if current_hour in self.config["surge_hours"]:
            multiplier *= self.config["surge_multiplier"]
            surge_reasons.append(f"Jam sibuk (+{int((self.config['surge_multiplier']-1)*100)}%)")
        
        # Cek hujan
        if is_raining:
            multiplier *= self.config["rain_multiplier"]
            surge_reasons.append(f"Cuaca hujan (+{int((self.config['rain_multiplier']-1)*100)}%)")
        
        # Cek weekend
        if datetime.now().weekday() >= 5:  # Sabtu=5, Minggu=6
            multiplier *= self.config["peak_day_multiplier"]
            surge_reasons.append(f"Weekend (+{int((self.config['peak_day_multiplier']-1)*100)}%)")
        
        # Total setelah surge
        total_with_surge = subtotal * multiplier
        
        # Platform fee
        platform_fee = total_with_surge * (self.config["platform_fee_percent"] / 100)
        
        # Total akhir
        final_price = total_with_surge + platform_fee
        
        # Apply minimum charge
        if final_price < self.config["min_charge"]:
            final_price = self.config["min_charge"]
        
        # Bulatkan ke 100 terdekat
        final_price = math.ceil(final_price / 100) * 100
        
        return {
            "success": True,
            "distance_km": distance_km,
            "distance_meters": route_data["distance_meters"],
            "base_price": int(base_price),
            "distance_charge": int(distance_charge),
            "tier_info": tier_info,  # Info tier yang digunakan
            "subtotal": int(subtotal),
            "surge_multiplier": round(multiplier, 2),
            "surge_reasons": surge_reasons,
            "price_with_surge": int(total_with_surge),
            "platform_fee": int(platform_fee),
            "platform_fee_percent": self.config["platform_fee_percent"],
            "final_price": int(final_price),
            "vehicle_type": vehicle_type,
            "estimate_duration_minutes": duration_minutes,
            "calculation_method": route_data["method"],
            "road_names": route_data["road_names"],
            "total_roads": route_data["total_roads"],
            "alternatives": route_data["alternatives"]
        }
    
    def get_price_breakdown(self, result):
        """
        Format breakdown harga untuk ditampilkan
        """
        if not result["success"]:
            return f"❌ Error: {result['error']}"
        
        breakdown = f"""
╔══════════════════════════════════════════════════════════╗
║           🚚 RINCIAN ONGKIR PENGIRIMAN LOKAL            ║
╚══════════════════════════════════════════════════════════╝

📍 Jarak Tempuh     : {result['distance_km']} km ({result['distance_meters']} meter)
🏍️  Jenis Kendaraan  : {result['vehicle_type'].capitalize()}
⏱️  Estimasi Waktu   : {result['estimate_duration_minutes']} menit
🗺️  Metode Hitung    : {result['calculation_method']}
"""
        
        # Tampilkan jalan yang dilalui
        if result['road_names']:
            breakdown += f"\n🛣️  Jalan yang dilalui (5 utama dari {result['total_roads']} jalan):\n"
            for i, road in enumerate(result['road_names'], 1):
                breakdown += f"    {i}. {road}\n"
        
        # Tampilkan rute alternatif jika ada
        if result['alternatives']:
            breakdown += f"\n🔀 Rute alternatif tersedia: {len(result['alternatives'])} rute lain\n"
            for alt in result['alternatives'][:2]:  # Tampilkan max 2 alternatif
                time_info = f"+{alt['time_diff']} menit" if alt['time_diff'] > 0 else f"{alt['time_diff']} menit"
                breakdown += f"    Rute {alt['route_number']}: {alt['distance_km']} km, {alt['duration_minutes']} menit ({time_info})\n"
        
        breakdown += f"""
╭──────────────────────────────────────────────────────────╮
│ 💵 RINCIAN BIAYA                                         │
╰──────────────────────────────────────────────────────────╯
  Biaya Dasar          : Rp {result['base_price']:>10,}
  
  Biaya Jarak:
    Tier                : {result['tier_info']['tier_range']}
    Total Jarak         : {result['tier_info']['total_distance']} km
    Tarif               : Rp {result['tier_info']['rate_per_km']:,}/km
    ─────────────────────────────────────────────────────────
    Total Biaya Jarak   : Rp {result['tier_info']['total_charge']:>10,}
  
  ─────────────────────────────────────────────────────────
  Subtotal             : Rp {result['subtotal']:>10,}
"""
        
        if result['surge_multiplier'] > 1.0:
            breakdown += f"""
  🔥 Surge Pricing     : x{result['surge_multiplier']}
"""
            for reason in result['surge_reasons']:
                breakdown += f"     • {reason}\n"
            breakdown += f"  Harga + Surge        : Rp {result['price_with_surge']:>10,}\n"
        
        breakdown += f"""
  Platform Fee ({result['platform_fee_percent']}%)   : Rp {result['platform_fee']:>10,}
  ═════════════════════════════════════════════════════════
  💰 TOTAL ONGKIR      : Rp {result['final_price']:>10,}
  ═════════════════════════════════════════════════════════
"""
        return breakdown


# ============================================================
# FUNGSI HELPER
# ============================================================

def cek_ongkir_interaktif():
    """Mode interaktif untuk cek ongkir lokal"""
    print("\n" + "="*60)
    print("🏙️  CEK ONGKIR PENGIRIMAN LOKAL (AUTO ROUTE)")
    print("="*60)
    print("\n🌐 Menggunakan OSRM - Otomatis mencari rute jalan terdekat!")
    print("   ✓ Jarak dihitung via rute jalan real")
    print("   ✓ Estimasi waktu akurat")
    print("   ✓ Menampilkan jalan yang dilalui")
    print("   ✓ Menyediakan rute alternatif\n")
    
    # Inisialisasi pricing engine
    pricing = LocalDeliveryPricing()
    
    print("📍 KOORDINAT LOKASI PENJEMPUTAN")
    try:
        origin_lat = float(input("Latitude asal: "))
        origin_lng = float(input("Longitude asal: "))
        
        print("\n📍 KOORDINAT LOKASI TUJUAN")
        dest_lat = float(input("Latitude tujuan: "))
        dest_lng = float(input("Longitude tujuan: "))
        
        print("\n🚗 JENIS KENDARAAN")
        print("1. Motor")
        print("2. Mobil")
        vehicle_choice = input("Pilih (1/2) [default: 1]: ").strip() or "1"
        vehicle_type = "motor" if vehicle_choice == "1" else "mobil"
        
        print("\n🌧️  KONDISI CUACA")
        is_raining = input("Sedang hujan? (y/n) [default: n]: ").strip().lower() == 'y'
        
        # Hitung ongkir
        print("\n" + "="*60)
        result = pricing.calculate_price(
            origin_lat, origin_lng, 
            dest_lat, dest_lng,
            is_raining=is_raining,
            vehicle_type=vehicle_type
        )
        
        # Tampilkan hasil
        print(pricing.get_price_breakdown(result))
        
    except ValueError:
        print("❌ Input tidak valid! Koordinat harus berupa angka.")
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================
# CONTOH PENGGUNAAN
# ============================================================

if __name__ == "__main__":
    import sys
    
    # Mode 1: Interaktif
    if len(sys.argv) == 1:
        cek_ongkir_interaktif()
    
    # Mode 2: Command line
    # Contoh: python osrm.py -7.797068 110.370529 -7.780000 110.360000
    elif len(sys.argv) == 5:
        origin_lat = float(sys.argv[1])
        origin_lng = float(sys.argv[2])
        dest_lat = float(sys.argv[3])
        dest_lng = float(sys.argv[4])
        
        pricing = LocalDeliveryPricing()
        result = pricing.calculate_price(origin_lat, origin_lng, dest_lat, dest_lng)
        print(pricing.get_price_breakdown(result))
    
    else:
        print("=" * 60)
        print("🏙️  SISTEM ONGKIR LOKAL (AUTO ROUTE - OSRM)")
        print("=" * 60)
        print("\n✨ Fitur:")
        print("  • Otomatis cari rute jalan terdekat")
        print("  • Tier pricing (lebih jauh = lebih murah per km)")
        print("  • Surge pricing (jam sibuk, hujan, weekend)")
        print("  • Tampilkan jalan yang dilalui")
        print("  • Rute alternatif tersedia")
        print("\n📋 Cara Pakai:")
        print("Mode 1: python osrm.py (interaktif)")
        print("Mode 2: python osrm.py <lat1> <lng1> <lat2> <lng2>")
        print("\n📍 Contoh Koordinat:")
        print("Yogyakarta   : -7.7956, 110.3695")
        print("Temanggung   : -7.3167, 110.1667")
        print("Magelang     : -7.4706, 110.2178")
        print("\n💡 Contoh:")
        print("python osrm.py -7.7956 110.3695 -7.3167 110.1667")
        print("\n🌐 Catatan: Memerlukan koneksi internet untuk OSRM")