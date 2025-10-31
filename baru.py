# file: BI/baru.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# ✅ CORS untuk Flutter Web
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

BASE_URL = "https://www.bi.go.id/hargapangan/WebSite"


# ===============================================================
# 🔹 Endpoint utama: /harga
# ===============================================================
@app.route("/harga", methods=["GET"])
def get_harga():
    """Endpoint utama untuk Flutter - mendapatkan data harga pangan"""

    # Ambil parameter dari Flutter
    province_id = request.args.get('province_id', '14')  # default Jawa Tengah
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    commodity_filter = request.args.get('commodity_filter', '')
    price_type_id = request.args.get('price_type_id', '1')  # ✨ default harga konsumen

    # Jika tidak ada tanggal, gunakan hari ini & kemarin
    if not start_date or not end_date:
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
        print(f"Auto-detect tanggal: {start_date} s.d {end_date}")

    # Siapkan parameter untuk API BI
    url = f"{BASE_URL}/TabelHarga/GetGridDataDaerah"
    params = {
        "price_type_id": price_type_id,
        "comcat_id": "",
        "province_id": province_id,
        "regency_id": "",
        "market_id": "",
        "tipe_laporan": "1",
        "start_date": start_date,
        "end_date": end_date
    }

    try:
        print(f"\n🔎 Mengambil data dari BI API...")
        print(f"Provinsi: {province_id} | price_type_id={price_type_id}")
        print(f"Tanggal: {start_date} → {end_date}")
        if commodity_filter:
            print(f"Filter komoditas: {commodity_filter}")

        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        raw_data = r.json()

        # Validasi struktur response
        if isinstance(raw_data, dict) and 'data' in raw_data:
            data_list = raw_data['data']
        elif isinstance(raw_data, list):
            data_list = raw_data
        else:
            return jsonify({"success": False, "error": "Format data tidak sesuai"})

        # Transformasi untuk Flutter
        transformed_data = []
        actual_date = None

        for item in data_list:
            commodity_name = item.get('name', 'Unknown')
            level = item.get('level', 0)

            # Skip kategori utama (level 1)
            if level == 1:
                continue

            # Filter nama komoditas (jika diisi)
            if commodity_filter and commodity_filter.lower() not in commodity_name.lower():
                continue

            date_keys = [k for k in item.keys() if '/' in str(k)]
            if not date_keys:
                continue

            latest_date = sorted(date_keys, key=lambda x: x.split('/')[::-1])[-1]
            latest_price_str = item.get(latest_date, '0')

            if actual_date is None:
                actual_date = latest_date

            if len(date_keys) > 1:
                prev_date = sorted(date_keys, key=lambda x: x.split('/')[::-1])[-2]
                prev_price_str = item.get(prev_date, '0')
            else:
                prev_price_str = latest_price_str

            try:
                latest_price = float(latest_price_str.replace(',', '').replace('.', ''))
                prev_price = float(prev_price_str.replace(',', '').replace('.', ''))
            except:
                continue

            if latest_price == 0:
                continue

            price_change = ((latest_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
            trend = "naik" if price_change > 0.1 else "turun" if price_change < -0.1 else "stabil"

            transformed_data.append({
                "commodity": commodity_name,
                "price": latest_price,
                "trend": trend,
                "price_change": round(price_change, 2),
                "latest_date": latest_date
            })

        print(f"✅ Total data berhasil: {len(transformed_data)} | Data: {actual_date}")

        return jsonify({
            "success": True,
            "data": transformed_data,
            "total": len(transformed_data),
            "data_date": actual_date,
            "info": f"Data tanggal {actual_date}",
            "filter_applied": commodity_filter if commodity_filter else None,
            "price_type_id": price_type_id
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


# ===============================================================
# 🔹 Endpoint cabai khusus
# ===============================================================
@app.route("/harga/cabai", methods=["GET"])
def get_harga_cabai():
    """Endpoint khusus untuk 4 jenis cabai"""
    province_id = request.args.get('province_id', '14')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    price_type_id = request.args.get('price_type_id', '1')  # default konsumen

    cabai_list = [
        "Cabai Merah Besar",
        "Cabai Merah Keriting ",
        "Cabai Rawit Hijau",
        "Cabai Rawit Merah"
    ]

    if not start_date or not end_date:
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        start_date = yesterday.strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')

    url = f"{BASE_URL}/TabelHarga/GetGridDataDaerah"
    params = {
        "price_type_id": price_type_id,
        "comcat_id": "",
        "province_id": province_id,
        "regency_id": "",
        "market_id": "",
        "tipe_laporan": "1",
        "start_date": start_date,
        "end_date": end_date
    }

    try:
        print(f"\n🌶️ Fetching CABAI data (price_type_id={price_type_id}) ...")
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        raw_data = r.json()

        if isinstance(raw_data, dict) and 'data' in raw_data:
            data_list = raw_data['data']
        elif isinstance(raw_data, list):
            data_list = raw_data
        else:
            return jsonify({"success": False, "error": "Format data tidak sesuai"})

        transformed_data = []
        actual_date = None

        for item in data_list:
            commodity_name = item.get('name', 'Unknown')
            level = item.get('level', 0)
            if level == 1 or commodity_name not in cabai_list:
                continue

            date_keys = [k for k in item.keys() if '/' in str(k)]
            if not date_keys:
                continue

            latest_date = sorted(date_keys, key=lambda x: x.split('/')[::-1])[-1]
            latest_price_str = item.get(latest_date, '0')
            if actual_date is None:
                actual_date = latest_date

            if len(date_keys) > 1:
                prev_date = sorted(date_keys, key=lambda x: x.split('/')[::-1])[-2]
                prev_price_str = item.get(prev_date, '0')
            else:
                prev_price_str = latest_price_str

            try:
                latest_price = float(latest_price_str.replace(',', '').replace('.', ''))
                prev_price = float(prev_price_str.replace(',', '').replace('.', ''))
            except:
                continue

            if latest_price == 0:
                continue

            price_change = ((latest_price - prev_price) / prev_price) * 100 if prev_price > 0 else 0
            trend = "naik" if price_change > 0.1 else "turun" if price_change < -0.1 else "stabil"

            transformed_data.append({
                "commodity": commodity_name,
                "price": latest_price,
                "trend": trend,
                "price_change": round(price_change, 2),
                "latest_date": latest_date
            })

        print(f"✅ Cabai berhasil: {len(transformed_data)}/4")

        return jsonify({
            "success": True,
            "data": transformed_data,
            "total": len(transformed_data),
            "data_date": actual_date,
            "info": f"Data 4 jenis cabai - {actual_date}",
            "price_type_id": price_type_id
        })

    except Exception as e:
        print(f"❌ Error cabai: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})


# ===============================================================
# 🔹 Endpoint lain: provinsi, kabupaten, komoditas
# ===============================================================
@app.route("/provinces", methods=["GET"])
def get_provinces():
    try:
        url = f"{BASE_URL}/Home/GetProvinceAll"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return jsonify({"success": True, "data": r.json()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/commodities", methods=["GET"])
def get_commodities():
    try:
        url = f"{BASE_URL}/Home/GetCommoditiesTree"
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()
        commodities = []

        def parse_tree(node):
            if isinstance(node, dict):
                node_id = node.get('TreeID') or node.get('id')
                node_name = node.get('TreeName') or node.get('text')
                if node_id and node_name:
                    commodities.append({'id': node_id, 'name': node_name})
                for child in node.get('items') or node.get('children') or []:
                    parse_tree(child)
            elif isinstance(node, list):
                for child in node:
                    parse_tree(child)

        parse_tree(data)
        return jsonify({"success": True, "data": commodities})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/regencies", methods=["GET"])
def get_regencies():
    try:
        province_id = request.args.get('province_id', '0')
        url = f"{BASE_URL}/Home/GetRegencyAll"
        params = {'filter': f'["regency_id",{province_id}]'}
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return jsonify({"success": True, "data": r.json()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ===============================================================
# 🔹 Endpoint test
# ===============================================================
@app.route("/test", methods=["GET"])
def test():
    return jsonify({
        "success": True,
        "message": "Flask backend is running!",
        "version": "1.1"
    })


# ===============================================================
# 🚀 Run App
# ===============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Flask Backend untuk Flutter")
    print("=" * 70)
    print("📍 URL: http://127.0.0.1:5000")
    print("📍 Endpoints:")
    print("   - GET /harga?province_id=14&price_type_id=1 (konsumen)")
    print("   - GET /harga?province_id=14&price_type_id=4 (produsen)")
    print("   - GET /harga/cabai?province_id=14")
    print("   - GET /provinces")
    print("   - GET /regencies?province_id=14")
    print("   - GET /commodities")
    print("   - GET /test")
    print("=" * 70)
    app.run(host="0.0.0.0", port=5000, debug=True)
