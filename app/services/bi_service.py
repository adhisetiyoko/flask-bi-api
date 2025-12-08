"""
app/services/bi_service.py
Service untuk mengakses API Bank Indonesia (PIHPS)
FIXED: Date sorting untuk selalu ambil tanggal terbaru
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from typing import Dict, Optional, List

BASE_URL = "https://www.bi.go.id/hargapangan/WebSite"

# -------------------------------------------------
# 🔧 HELPER FUNCTIONS
# -------------------------------------------------

def create_session():
    """Buat session dengan retry mechanism"""
    session = requests.Session()
    
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def _date_sort_key(date_str: str) -> str:
    """
    ✅ FUNGSI BARU: Convert DD/MM/YYYY atau D/M/YYYY ke YYYY-MM-DD untuk sorting
    Contoh: "7/12/2025" → "2025-12-07"
    Ini fix masalah: "7/12/2025" dianggap lebih besar dari "06/12/2025" saat sort string
    """
    try:
        parts = date_str.split('/')
        day = parts[0].zfill(2)    # Tambah leading zero: "7" → "07"
        month = parts[1].zfill(2)  # Tambah leading zero: "6" → "06"
        year = parts[2]
        return f"{year}-{month}-{day}"
    except:
        return "0000-00-00"  # Fallback untuk tanggal invalid

def _get_date_range(start_date: Optional[str] = None, 
                    end_date: Optional[str] = None) -> tuple:
    """Generate date range jika tidak ada parameter tanggal"""
    if not start_date or not end_date:
        today = datetime.now()
        start_date_obj = today - timedelta(days=30)
        start_date = start_date_obj.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    return start_date, end_date

def _parse_price(price_str: str) -> Optional[float]:
    """Convert string harga ke float"""
    try:
        if price_str == "-" or not price_str:
            return None
        # Format: "13,950" atau "13.950"
        return float(price_str.replace(',', '').replace('.', ''))
    except:
        return None

def _calculate_trend(current_price: float, prev_price: float) -> tuple:
    """Hitung trend dan perubahan harga"""
    if prev_price > 0:
        price_change = ((current_price - prev_price) / prev_price) * 100
    else:
        price_change = 0
    
    # Tentukan trend
    if price_change > 0.1:
        trend = "naik"
    elif price_change < -0.1:
        trend = "turun"
    else:
        trend = "stabil"
    
    return trend, round(price_change, 2)

# -------------------------------------------------
# 🔹 FUNGSI UTAMA UNTUK HARGA PANGAN
# -------------------------------------------------

def get_harga_data(province_id: str = '14',
                   regency_id: str = '',
                   price_type_id: str = '1',
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   commodity_filter: Optional[str] = None) -> Dict:
    """
    Ambil data harga pangan dengan auto-fallback ke tanggal sebelumnya
    """
    
    try:
        # Auto-detect tanggal
        if not start_date or not end_date:
            today = datetime.now()
            # Coba 90 hari terakhir untuk memastikan ada data
            start_date_obj = today - timedelta(days=90)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        
        url = f"{BASE_URL}/TabelHarga/GetGridDataDaerah"
        params = {
            "price_type_id": price_type_id,
            "comcat_id": "",
            "province_id": province_id,
            "regency_id": regency_id,
            "market_id": "",
            "tipe_laporan": "1",
            "start_date": start_date,
            "end_date": end_date
        }
        
        print(f"[BI Service] Fetching data from BI API...")
        print(f"[BI Service] Province: {province_id}, Regency: {regency_id}, Price Type: {price_type_id}")
        print(f"[BI Service] Date range: {start_date} to {end_date}")
        if commodity_filter:
            print(f"[BI Service] Filter: {commodity_filter}")
        
        session = create_session()
        r = session.get(url, params=params, timeout=15)
        r.raise_for_status()
        raw_data = r.json()
        
        # Parse response
        if isinstance(raw_data, dict) and 'data' in raw_data:
            data_list = raw_data['data']
        elif isinstance(raw_data, list):
            data_list = raw_data
        else:
            return {
                "success": False,
                "error": "Format data tidak sesuai"
            }
        
        # Transform data
        transformed_data = []
        actual_date = None
        
        for item in data_list:
            commodity_name = item.get('name', 'Unknown')
            level = item.get('level', 0)
            
            # Skip header/kategori (level 1)
            if level == 1:
                continue
            
            # Filter komoditas (case-insensitive)
            if commodity_filter:
                if commodity_filter.lower() not in commodity_name.lower():
                    continue
            
            # Ambil date keys
            date_keys = [k for k in item.keys() if '/' in str(k)]
            if not date_keys:
                continue
            
            # ✅ FIXED: Sort tanggal dengan benar menggunakan _date_sort_key
            sorted_dates = sorted(date_keys, key=_date_sort_key, reverse=True)
            
            # Debug: Print untuk cabai
            if commodity_filter and 'cabai' in commodity_filter.lower():
                print(f"[DEBUG] {commodity_name}: Top 3 dates = {sorted_dates[:3]}")
            
            # Ambil harga terbaru yang ada (bukan hanya hari ini)
            latest_price = None
            latest_date = None
            
            for date in sorted_dates:
                price_str = item.get(date, '0')
                parsed_price = _parse_price(price_str)
                if parsed_price and parsed_price > 0:
                    latest_price = parsed_price
                    latest_date = date
                    break
            
            if latest_price is None:
                continue
            
            if actual_date is None:
                actual_date = latest_date
            
            # Ambil harga sebelumnya untuk hitung trend
            prev_price = latest_price
            for i, date in enumerate(sorted_dates):
                if i > 0 and date != latest_date:
                    price_str = item.get(date, '0')
                    parsed = _parse_price(price_str)
                    if parsed and parsed > 0:
                        prev_price = parsed
                        break
            
            # Hitung trend
            trend, price_change = _calculate_trend(latest_price, prev_price)
            
            transformed_data.append({
                "commodity": commodity_name.strip(),
                "price": latest_price,
                "trend": trend,
                "price_change": price_change,
                "latest_date": latest_date
            })
        
        print(f"[BI Service] Total data berhasil: {len(transformed_data)}")
        print(f"[BI Service] Data date: {actual_date}")
        
        return {
            "success": True,
            "data": transformed_data,
            "total": len(transformed_data),
            "data_date": actual_date,
            "info": f"Data terbaru per {actual_date}",
            "filter_applied": commodity_filter if commodity_filter else None
        }
        
    except Exception as e:
        print(f"[BI Service] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


# -------------------------------------------------
# 🔹 KHUSUS KOMODITAS CABAI
# -------------------------------------------------

def get_cabai_data(province_id: str = '14',
                   regency_id: str = '',
                   price_type_id: str = '1',
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None) -> Dict:
    """
    Ambil data khusus 4 jenis cabai dengan auto-fallback
    """
    
    cabai_list = [
        "Cabai Merah Besar",
        "Cabai Merah Keriting ",
        "Cabai Rawit Hijau",
        "Cabai Rawit Merah"
    ]
    
    try:
        # Auto-detect tanggal dengan range lebih panjang
        if not start_date or not end_date:
            today = datetime.now()
            start_date_obj = today - timedelta(days=90)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        
        url = f"{BASE_URL}/TabelHarga/GetGridDataDaerah"
        params = {
            "price_type_id": price_type_id,
            "comcat_id": "",
            "province_id": province_id,
            "regency_id": regency_id,
            "market_id": "",
            "tipe_laporan": "1",
            "start_date": start_date,
            "end_date": end_date
        }
        
        print(f"[BI Service] Fetching CABAI data from BI API...")
        print(f"[BI Service] Province: {province_id}, Regency: {regency_id}")
        print(f"[BI Service] Date range: {start_date} to {end_date}")
        
        session = create_session()
        r = session.get(url, params=params, timeout=15)
        r.raise_for_status()
        raw_data = r.json()
        
        if isinstance(raw_data, dict) and 'data' in raw_data:
            data_list = raw_data['data']
        elif isinstance(raw_data, list):
            data_list = raw_data
        else:
            return {
                "success": False,
                "error": "Format data tidak sesuai"
            }
        
        transformed_data = []
        actual_date = None
        found_names = []
        
        for item in data_list:
            commodity_name = item.get('name', 'Unknown')
            level = item.get('level', 0)
            
            if level == 1:
                continue
            
            # Filter: Hanya ambil 4 jenis cabai
            if commodity_name not in cabai_list:
                continue
            
            found_names.append(commodity_name)
            
            # Ambil date keys
            date_keys = [k for k in item.keys() if '/' in str(k)]
            if not date_keys:
                continue
            
            # ✅ FIXED: Sort tanggal dengan benar menggunakan _date_sort_key
            sorted_dates = sorted(date_keys, key=_date_sort_key, reverse=True)
            
            # Debug: Print 5 tanggal teratas untuk setiap cabai
            print(f"[DEBUG] {commodity_name}: {sorted_dates[:5]}")
            
            # Cari harga terbaru yang tersedia
            latest_price = None
            latest_date = None
            
            for date in sorted_dates:
                price_str = item.get(date, '0')
                parsed_price = _parse_price(price_str)
                if parsed_price and parsed_price > 0:
                    latest_price = parsed_price
                    latest_date = date
                    break
            
            if latest_price is None:
                print(f"[WARNING] {commodity_name}: No valid price found in {len(sorted_dates)} dates")
                continue
            
            if actual_date is None:
                actual_date = latest_date
            
            # Ambil harga sebelumnya
            prev_price = latest_price
            for i, date in enumerate(sorted_dates):
                if i > 0 and date != latest_date:
                    price_str = item.get(date, '0')
                    parsed = _parse_price(price_str)
                    if parsed and parsed > 0:
                        prev_price = parsed
                        break
            
            # Hitung trend
            trend, price_change = _calculate_trend(latest_price, prev_price)
            
            transformed_data.append({
                "commodity": commodity_name.strip(),
                "price": latest_price,
                "trend": trend,
                "price_change": price_change,
                "latest_date": latest_date
            })
            
            print(f"[BI Service]   ✓ {commodity_name}: Rp {latest_price:,.0f} ({trend} {price_change:+.2f}%) - {latest_date}")
        
        missing = set(cabai_list) - set(found_names)
        
        print(f"[BI Service] Total cabai: {len(transformed_data)}/4")
        if missing:
            print(f"[BI Service] Missing: {', '.join(missing)}")
        
        return {
            "success": True,
            "data": transformed_data,
            "total": len(transformed_data),
            "requested": 4,
            "data_date": actual_date,
            "info": f"Data terbaru: {actual_date}",
            "missing": list(missing) if missing else None
        }
        
    except Exception as e:
        print(f"[BI Service] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

# -------------------------------------------------
# 🔹 DATA MASTER
# -------------------------------------------------

def get_provinces() -> Dict:
    """Ambil daftar provinsi"""
    try:
        url = f"{BASE_URL}/Home/GetProvinceAll"
        
        session = create_session()
        r = session.get(url, timeout=15)
        r.raise_for_status()
        raw_data = r.json()
        
        # Parse response
        if isinstance(raw_data, dict) and 'data' in raw_data:
            data = raw_data['data']
        else:
            data = raw_data
        
        return {
            "success": True,
            "data": data,
            "total": len(data) if isinstance(data, list) else 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_regencies(province_id: str) -> Dict:
    """Ambil daftar kabupaten/kota berdasarkan provinsi"""
    if not province_id:
        return {
            "success": False,
            "message": "Parameter province_id diperlukan"
        }
    
    try:
        url = f"{BASE_URL}/Home/GetRegencyAll"
        params = {"ref_prov_id": province_id}
        
        session = create_session()
        r = session.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        return {
            "success": True,
            "data": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_commodities() -> Dict:
    """Ambil daftar kategori komoditas"""
    try:
        url = f"{BASE_URL}/Home/GetCommoditiesTree"
        
        session = create_session()
        r = session.get(url, timeout=15)
        r.raise_for_status()
        raw_data = r.json()
        
        print(f"[BI Service] Raw commodities response type: {type(raw_data)}")
        
        # Parse tree structure
        commodities = []
        
        def parse_tree(node, parent_name=None):
            if isinstance(node, dict):
                node_id = node.get('TreeID')
                node_name = node.get('TreeName')
                parent_id = node.get('ParentID')
                
                # Hanya ambil yang punya TreeID dan TreeName
                if node_id and node_name:
                    commodities.append({
                        'id': node_id,
                        'name': node_name,
                        'parent_id': parent_id,
                        'category': parent_name
                    })
                
                # Rekursif ke children
                children = node.get('items') or node.get('children') or []
                for child in children:
                    parse_tree(child, node_name)
        
        # Handle berbagai format response
        if isinstance(raw_data, dict):
            # Cek jika ada key 'data'
            if 'data' in raw_data:
                data_content = raw_data['data']
                if isinstance(data_content, list):
                    for item in data_content:
                        parse_tree(item)
                elif isinstance(data_content, dict):
                    parse_tree(data_content)
            else:
                parse_tree(raw_data)
        elif isinstance(raw_data, list):
            for item in raw_data:
                parse_tree(item)
        
        print(f"[BI Service] Total commodities parsed: {len(commodities)}")
        
        return {
            "success": True,
            "commodities": commodities,
            "total": len(commodities)
        }
    except Exception as e:
        print(f"[BI Service] Error parsing commodities: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

def get_price_types() -> Dict:
    """Ambil daftar jenis pasar (Pasar Tradisional / Modern)"""
    try:
        url = f"{BASE_URL}/Home/GetType"
        
        session = create_session()
        r = session.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        
        clean_data = [
            {
                "id": item.get("price_type_id"),
                "name": item.get("price_type_name")
            }
            for item in data.get("data", [])
        ]
        
        return {
            "success": True,
            "data": clean_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_latest_date() -> Dict:
    """Ambil tanggal dengan fallback mechanism"""
    try:
        today = datetime.now()
        
        # Generate 30 hari terakhir
        available_dates = []
        for i in range(30):
            date = today - timedelta(days=i)
            available_dates.append({
                "date": date.strftime("%d/%m/%Y"),
                "day": date.strftime("%A"),
                "display": date.strftime("%d %B %Y")
            })
        
        # Default response (fallback)
        response_data = {
            "success": True,
            "latest_date": available_dates[0]["date"],
            "available_dates": available_dates,
            "source": "generated"
        }
        
        return response_data
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }