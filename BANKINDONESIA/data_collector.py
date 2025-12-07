# file: data_collector.py (Akan di-deploy sebagai Cloud Function)

import requests
import pandas as pd
from datetime import datetime
import functions_framework
import os

BASE = "https://www.bi.go.id/hargapangan/WebSite/Home"
# Tentukan komoditas, provinsi, dan kabupaten yang Anda inginkan
# Misalnya, Komoditas ID (TreeID) Cabai Merah: 1, Provinsi DKI Jakarta: 1
COMMODITY_ID = 1 # ID Cabai Merah
PROV_ID = 1      # ID DKI Jakarta
REG_ID = 0       # 0 = Semua Kota/Kabupaten

def get_json(url, params=None):
    """Helper untuk ambil data JSON"""
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"⚠️ Gagal akses {url}: {e}")
        return None

def fetch_and_save_data(tanggal_str):
    """Mengambil satu hari data dan menambahkannya ke file/DB"""
    
    # === Ambil Data Master (Komoditas, Provinsi) - Sederhanakan ===
    # Dalam implementasi nyata, data master ini sudah disimpan
    
    # === Ambil Data Harga ===
    params = {
        "tanggal": tanggal_str,
        "commodity": COMMODITY_ID,
        "priceType": 1, # Rata-rata
        "isPasokan": 0,
        "jenis": 1,
        "periode": 1,
        "provId": PROV_ID,
        "regId": REG_ID 
    }
    
    data = get_json(f"{BASE}/GetHistogramData", params)
    
    if data and isinstance(data, list) and len(data) > 0:
        item = data[0]
        harga = item.get('Nilai') or item.get('value')
        
        if harga:
            # === Siapkan Data untuk Disimpan ===
            new_record = {
                'tanggal_parsed': datetime.now().strftime('%Y-%m-%d'),
                'komoditas': "Cabai Merah", # Ganti dengan nama komoditas yang benar
                'provinsi': "DKI Jakarta",  # Ganti dengan nama provinsi
                'kabupaten': "Semua Kota",
                'harga': harga,
                # Tambahkan fitur lain jika tersedia
                'harga_nasional': item.get('SemuaProvinsi'),
                'std_dev': item.get('stdDev')
            }
            
            # === Logika Penyimpanan Data (Harus diubah ke Cloud Storage/Database) ===
            # DI LINGKUNGAN GCF: Anda tidak bisa langsung menulis ke CSV lokal!
            # Anda harus menulis ke Cloud Storage (GCS) atau Cloud SQL/Firestore.
            
            # Jika menggunakan Database:
            # db.insert(new_record)
            
            print(f"✅ Data {tanggal_str} berhasil diambil: Rp {harga:,.0f}")
            return new_record
        
    print(f"❌ Data harga tidak tersedia untuk {tanggal_str}")
    return None

@functions_framework.http
def daily_data_collector(request):
    """Fungsi utama yang dipicu oleh Cloud Scheduler."""
    
    # Ambil tanggal hari ini
    today_str = datetime.now().strftime("%d %b %Y")
    
    print(f"--- Mulai Pengambilan Data untuk {today_str} ---")
    fetch_and_save_data(today_str)
    
    # PENTING: Tambahkan logika notifikasi jika gagal
    return 'Data Collection Completed!', 200

# requirements.txt untuk file ini:
# functions-framework
# requests
# pandas
# # Tambahkan library database Anda (misal: google-cloud-storage, psycopg2)