import requests
from dotenv import load_dotenv
import os

# Load file .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
RAJAONGKIR_BASE = "https://rajaongkir.komerce.id/api/v1"

def get_provinces():
    """Mendapatkan daftar provinsi"""
    url = f"{RAJAONGKIR_BASE}/destination/province"
    headers = {"Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data['meta']['status'] == 'success':
            return data['data']
        return []
    except Exception as e:
        print(f"❌ Error get provinces: {e}")
        return []

def get_cities(province_id):
    """Mendapatkan daftar kota berdasarkan province_id"""
    url = f"{RAJAONGKIR_BASE}/destination/city/{province_id}"
    headers = {"Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data['meta']['status'] == 'success':
            return data['data']
        return []
    except Exception as e:
        print(f"❌ Error get cities: {e}")
        return []

def get_districts(city_id):
    """Mendapatkan daftar district/kecamatan berdasarkan city_id"""
    url = f"{RAJAONGKIR_BASE}/destination/district/{city_id}"
    headers = {"Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data['meta']['status'] == 'success':
            return data['data']
        return []
    except Exception as e:
        print(f"❌ Error get districts: {e}")
        return []

def cari_kota_by_name(nama_kota):
    """Mencari kota berdasarkan nama (search di semua provinsi)"""
    print(f"🔍 Mencari '{nama_kota}' di seluruh Indonesia...")
    
    provinces = get_provinces()
    hasil = []
    
    for province in provinces:
        cities = get_cities(province['id'])
        for city in cities:
            if nama_kota.lower() in city['name'].lower():
                hasil.append({
                    'province_id': province['id'],
                    'province_name': province['name'],
                    'city_id': city['id'],
                    'city_name': city['name'],
                    'city_type': city['type']
                })
    
    return hasil

def cari_district_by_name(nama_district, city_id=None):
    """Mencari district berdasarkan nama"""
    hasil = []
    
    if city_id:
        # Cari di city tertentu
        districts = get_districts(city_id)
        for district in districts:
            if nama_district.lower() in district['name'].lower():
                hasil.append(district)
    else:
        # Cari di semua city (lebih lambat)
        print("⚠️  Pencarian district tanpa city_id akan memakan waktu...")
        provinces = get_provinces()
        for province in provinces:
            cities = get_cities(province['id'])
            for city in cities:
                districts = get_districts(city['id'])
                for district in districts:
                    if nama_district.lower() in district['name'].lower():
                        hasil.append({
                            **district,
                            'city_name': city['name'],
                            'province_name': province['name']
                        })
    
    return hasil

def pilih_dari_list(items, label="item"):
    """Helper untuk memilih dari list"""
    if not items:
        return None
    
    if len(items) == 1:
        print(f"✅ Ditemukan 1 {label}: {items[0]}")
        return items[0]
    
    print(f"\n📍 Ditemukan {len(items)} {label}:")
    for i, item in enumerate(items, 1):
        print(f"   {i}. {item}")
    
    while True:
        try:
            pilihan = int(input(f"\n Pilih nomor {label} (1-{len(items)}): "))
            if 1 <= pilihan <= len(items):
                return items[pilihan - 1]
            print(f"❌ Pilih nomor antara 1-{len(items)}")
        except ValueError:
            print("❌ Masukkan nomor yang valid")

def cek_ongkir(origin, destination, weight, courier="jne:sicepat:ide:sap:jnt:ninja:tiki:lion:anteraja:pos:ncs:rex:rpx:sentral:star:wahana:dse"):
    """Cek ongkir berdasarkan district ID"""
    url = BASE_URL
    payload = {
        "origin": origin,
        "destination": destination,
        "weight": weight,
        "courier": courier,
        "price": "lowest"
    }
    headers = {
        "key": API_KEY,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(url, data=payload, headers=headers)
    
    try:
        return response.json()
    except:
        return {"error": "Response bukan JSON", "raw": response.text[:200]}

def cek_ongkir_manual():
    """Cek ongkir dengan input manual (interaktif)"""
    print("\n" + "="*60)
    print("🚚 CEK ONGKIR RAJAONGKIR")
    print("="*60)
    
    # KOTA ASAL
    print("\n📦 KOTA ASAL")
    kota_asal = input("Masukkan nama kota asal (contoh: Jakarta): ").strip()
    
    cities_asal = cari_kota_by_name(kota_asal)
    if not cities_asal:
        print(f"❌ Kota '{kota_asal}' tidak ditemukan!")
        return None
    
    if len(cities_asal) > 1:
        print(f"\n📍 Ditemukan {len(cities_asal)} kota:")
        for i, city in enumerate(cities_asal, 1):
            print(f"   {i}. {city['city_type']} {city['city_name']}, {city['province_name']}")
        
        pilihan = int(input(f"\nPilih nomor (1-{len(cities_asal)}): ")) - 1
        city_asal = cities_asal[pilihan]
    else:
        city_asal = cities_asal[0]
        print(f"✅ Kota asal: {city_asal['city_type']} {city_asal['city_name']}, {city_asal['province_name']}")
    
    # District asal
    districts_asal = get_districts(city_asal['city_id'])
    print(f"\n📍 Ditemukan {len(districts_asal)} kecamatan di {city_asal['city_name']}")
    
    nama_district_asal = input("Masukkan nama kecamatan asal (atau tekan Enter untuk pilih kota saja): ").strip()
    
    if nama_district_asal:
        districts_asal_filtered = [d for d in districts_asal if nama_district_asal.lower() in d['name'].lower()]
        if districts_asal_filtered:
            if len(districts_asal_filtered) > 1:
                for i, d in enumerate(districts_asal_filtered, 1):
                    print(f"   {i}. {d['name']}")
                pilihan = int(input(f"\nPilih nomor (1-{len(districts_asal_filtered)}): ")) - 1
                district_asal_id = districts_asal_filtered[pilihan]['id']
            else:
                district_asal_id = districts_asal_filtered[0]['id']
                print(f"✅ Kecamatan asal: {districts_asal_filtered[0]['name']}")
        else:
            print("❌ Kecamatan tidak ditemukan, menggunakan kota saja")
            district_asal_id = districts_asal[0]['id'] if districts_asal else city_asal['city_id']
    else:
        district_asal_id = districts_asal[0]['id'] if districts_asal else city_asal['city_id']
    
    # KOTA TUJUAN
    print("\n📍 KOTA TUJUAN")
    kota_tujuan = input("Masukkan nama kota tujuan: ").strip()
    
    cities_tujuan = cari_kota_by_name(kota_tujuan)
    if not cities_tujuan:
        print(f"❌ Kota '{kota_tujuan}' tidak ditemukan!")
        return None
    
    if len(cities_tujuan) > 1:
        print(f"\n📍 Ditemukan {len(cities_tujuan)} kota:")
        for i, city in enumerate(cities_tujuan, 1):
            print(f"   {i}. {city['city_type']} {city['city_name']}, {city['province_name']}")
        
        pilihan = int(input(f"\nPilih nomor (1-{len(cities_tujuan)}): ")) - 1
        city_tujuan = cities_tujuan[pilihan]
    else:
        city_tujuan = cities_tujuan[0]
        print(f"✅ Kota tujuan: {city_tujuan['city_type']} {city_tujuan['city_name']}, {city_tujuan['province_name']}")
    
    # District tujuan
    districts_tujuan = get_districts(city_tujuan['city_id'])
    print(f"\n📍 Ditemukan {len(districts_tujuan)} kecamatan di {city_tujuan['city_name']}")
    
    nama_district_tujuan = input("Masukkan nama kecamatan tujuan (atau tekan Enter untuk pilih kota saja): ").strip()
    
    if nama_district_tujuan:
        districts_tujuan_filtered = [d for d in districts_tujuan if nama_district_tujuan.lower() in d['name'].lower()]
        if districts_tujuan_filtered:
            if len(districts_tujuan_filtered) > 1:
                for i, d in enumerate(districts_tujuan_filtered, 1):
                    print(f"   {i}. {d['name']}")
                pilihan = int(input(f"\nPilih nomor (1-{len(districts_tujuan_filtered)}): ")) - 1
                district_tujuan_id = districts_tujuan_filtered[pilihan]['id']
            else:
                district_tujuan_id = districts_tujuan_filtered[0]['id']
                print(f"✅ Kecamatan tujuan: {districts_tujuan_filtered[0]['name']}")
        else:
            print("❌ Kecamatan tidak ditemukan, menggunakan kota saja")
            district_tujuan_id = districts_tujuan[0]['id'] if districts_tujuan else city_tujuan['city_id']
    else:
        district_tujuan_id = districts_tujuan[0]['id'] if districts_tujuan else city_tujuan['city_id']
    
    # BERAT
    berat = int(input("\n⚖️  Masukkan berat paket (gram): "))
    
    # CEK ONGKIR
    print(f"\n🔄 Mengecek ongkir dari ID {district_asal_id} ke ID {district_tujuan_id}...")
    print(f"   Berat: {berat} gram")
    
    return cek_ongkir(district_asal_id, district_tujuan_id, berat)

# ---------------------------------------------------
# CONTOH PEMANGGILAN
# ---------------------------------------------------
if __name__ == "__main__":
    # Mode interaktif (direkomendasikan)
    hasil = cek_ongkir_manual()
    
    if hasil:
        print("\n" + "="*60)
        print("✅ HASIL CEK ONGKIR")
        print("="*60)
        
        # Tampilkan hasil dengan format yang lebih rapi
        if 'error' in hasil:
            print(f"❌ Error: {hasil['error']}")
        else:
            import json
            print(json.dumps(hasil, indent=2, ensure_ascii=False))
    
    # Atau gunakan langsung dengan ID (cara lama)
    # hasil = cek_ongkir(
    #     origin=1391,
    #     destination=1376,
    #     weight=1000
    # )
    # print("\nHASIL:", hasil)