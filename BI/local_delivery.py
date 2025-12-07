import math
from datetime import datetime

class LocalDeliveryPricing:
    """
    Sistem perhitungan ongkir lokal (dalam satu kota/kabupaten)
    Mirip dengan GrabFood, GrabExpress, GoFood, dll
    """
    
    def __init__(self, config=None):
        """
        Inisialisasi dengan konfigurasi harga
        """
        self.config = config or {
            "base_price": 5000,          # Harga dasar (Rp)
            "price_per_km": 2500,        # Harga per kilometer (Rp)
            "min_distance_km": 0.5,      # Jarak minimum (km)
            "max_distance_km": 15,       # Jarak maksimum (km)
            "min_charge": 7000,          # Biaya minimum (Rp)
            "platform_fee_percent": 10,  # Fee platform (%)
            "surge_hours": [7, 8, 12, 13, 18, 19],  # Jam sibuk
            "surge_multiplier": 1.3,     # Pengali saat surge (1.3 = +30%)
            "rain_multiplier": 1.2,      # Pengali saat hujan (1.2 = +20%)
            "peak_day_multiplier": 1.1,  # Weekend/hari libur (1.1 = +10%)
        }
    
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Hitung jarak antara dua koordinat menggunakan formula Haversine
        Returns: jarak dalam kilometer
        """
        # Radius bumi dalam kilometer
        R = 6371.0
        
        # Konversi derajat ke radian
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Perbedaan koordinat
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Formula Haversine
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return round(distance, 2)
    
    def calculate_price(self, origin_lat, origin_lng, dest_lat, dest_lng, 
                       is_raining=False, vehicle_type="motor"):
        """
        Hitung ongkir berdasarkan koordinat
        
        Args:
            origin_lat: Latitude asal
            origin_lng: Longitude asal
            dest_lat: Latitude tujuan
            dest_lng: Longitude tujuan
            is_raining: Apakah sedang hujan
            vehicle_type: Jenis kendaraan ('motor' atau 'mobil')
        
        Returns:
            Dict dengan detail harga
        """
        # Hitung jarak
        distance_km = self.haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
        
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
        if vehicle_type == "mobil":
            base_price = base_price * 1.5  # Mobil 50% lebih mahal
            price_per_km = self.config["price_per_km"] * 1.5
        else:
            price_per_km = self.config["price_per_km"]
        
        # Hitung biaya jarak
        distance_charge = distance_km * price_per_km
        
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
            "base_price": int(base_price),
            "distance_charge": int(distance_charge),
            "subtotal": int(subtotal),
            "surge_multiplier": round(multiplier, 2),
            "surge_reasons": surge_reasons,
            "price_with_surge": int(total_with_surge),
            "platform_fee": int(platform_fee),
            "platform_fee_percent": self.config["platform_fee_percent"],
            "final_price": int(final_price),
            "vehicle_type": vehicle_type,
            "estimate_duration_minutes": int(distance_km * 3) + 5  # Asumsi 20km/jam
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

📍 Jarak Tempuh     : {result['distance_km']} km
🏍️  Jenis Kendaraan  : {result['vehicle_type'].capitalize()}
⏱️  Estimasi Waktu   : {result['estimate_duration_minutes']} menit

╭──────────────────────────────────────────────────────────╮
│ 💵 RINCIAN BIAYA                                         │
╰──────────────────────────────────────────────────────────╯
  Biaya Dasar          : Rp {result['base_price']:>10,}
  Biaya Jarak          : Rp {result['distance_charge']:>10,}
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
    print("🏙️  CEK ONGKIR PENGIRIMAN LOKAL (DALAM KOTA)")
    print("="*60)
    
    # Inisialisasi pricing engine
    pricing = LocalDeliveryPricing()
    
    print("\n📍 KOORDINAT LOKASI PENJEMPUTAN")
    try:
        origin_lat = float(input("Latitude asal (contoh: -7.797068): "))
        origin_lng = float(input("Longitude asal (contoh: 110.370529): "))
        
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
        print("\n🔄 Menghitung ongkir...")
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
    # Contoh: py local_delivery.py -7.797068 110.370529 -7.780000 110.360000
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
        print("🏙️  SISTEM ONGKIR LOKAL (GRAB/GOJEK STYLE)")
        print("=" * 60)
        print("\n📋 Cara Pakai:")
        print("Mode 1: py local_delivery.py (interaktif)")
        print("Mode 2: py local_delivery.py <lat1> <lng1> <lat2> <lng2>")
        print("\n📍 Contoh Koordinat:")
        print("Magelang Kota : -7.47056, 110.21778")
        print("Temanggung    : -7.31667, 110.16667")
        print("Yogyakarta    : -7.7956, 110.3695")
        print("\n💡 Contoh:")
        print("py local_delivery.py -7.797068 110.370529 -7.780000 110.360000")