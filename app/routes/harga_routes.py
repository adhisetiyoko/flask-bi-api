"""
app/routes/harga_routes.py
Routes untuk endpoint harga pangan
"""

from flask import Blueprint, jsonify, request
from app.services import bi_service

harga_bp = Blueprint('harga', __name__, url_prefix='/harga')

# -------------------------------------------------
# 🔹 RUTE UTAMA: Ambil data harga komoditas
# -------------------------------------------------

@harga_bp.route('/', methods=['GET'])
def harga():
    """
    Endpoint untuk mendapatkan data harga pangan
    
    Query Parameters:
        - province_id (str): ID provinsi (default: '14')
        - regency_id (str): ID kabupaten/kota (optional)
        - price_type_id (str): Jenis harga 1-4 (default: '1')
        - start_date (str): Tanggal mulai YYYY-MM-DD (optional)
        - end_date (str): Tanggal akhir YYYY-MM-DD (optional)
        - commodity_filter (str): Filter nama komoditas (optional)
    
    Returns:
        JSON response dengan data harga
    """
    
    # Ambil parameter dari request
    province_id = request.args.get('province_id', '14')
    regency_id = request.args.get('regency_id', '')
    price_type_id = request.args.get('price_type_id', '1')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    commodity_filter = request.args.get('commodity_filter', '')
    
    # Call service
    result = bi_service.get_harga_data(
        province_id=province_id,
        regency_id=regency_id,
        price_type_id=price_type_id,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
        commodity_filter=commodity_filter if commodity_filter else None
    )
    
    return jsonify(result)


# -------------------------------------------------
# 🔹 RUTE KHUSUS CABAI
# -------------------------------------------------

@harga_bp.route('/cabai', methods=['GET'])
def cabai():
    """
    Endpoint khusus untuk 4 jenis cabai
    
    Query Parameters:
        - province_id (str): ID provinsi (default: '14')
        - regency_id (str): ID kabupaten/kota (optional)
        - price_type_id (str): Jenis harga 1-4 (default: '1')
        - start_date (str): Tanggal mulai YYYY-MM-DD (optional)
        - end_date (str): Tanggal akhir YYYY-MM-DD (optional)
    
    Returns:
        JSON response dengan data 4 jenis cabai
    """
    
    # Ambil parameter dari request
    province_id = request.args.get('province_id', '14')
    regency_id = request.args.get('regency_id', '')
    price_type_id = request.args.get('price_type_id', '1')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Call service
    result = bi_service.get_cabai_data(
        province_id=province_id,
        regency_id=regency_id,
        price_type_id=price_type_id,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None
    )
    
    return jsonify(result)


# -------------------------------------------------
# 🔹 DATA MASTER
# -------------------------------------------------

@harga_bp.route('/provinces', methods=['GET'])
def provinces():
    """
    Endpoint untuk mendapatkan daftar provinsi
    
    Returns:
        JSON response dengan list provinsi
    """
    result = bi_service.get_provinces()
    return jsonify(result)


@harga_bp.route('/regencies', methods=['GET'])
def regencies():
    """
    Endpoint untuk mendapatkan daftar kabupaten/kota
    
    Query Parameters:
        - province_id (str): ID provinsi (required)
    
    Returns:
        JSON response dengan list kabupaten/kota
    """
    province_id = request.args.get('province_id', '0')
    result = bi_service.get_regencies(province_id)
    return jsonify(result)


@harga_bp.route('/commodities', methods=['GET'])
def commodities():
    """
    Endpoint untuk mendapatkan daftar komoditas
    
    Returns:
        JSON response dengan list komoditas
    """
    result = bi_service.get_commodities()
    return jsonify(result)


# -------------------------------------------------
# 🔹 UTILITY ENDPOINTS
# -------------------------------------------------

@harga_bp.route('/price-types', methods=['GET'])
def price_types():
    """
    Endpoint untuk mendapatkan jenis pasar (tradisional/modern)
    
    Returns:
        JSON response dengan list price types
    """
    result = bi_service.get_price_types()
    return jsonify(result)


@harga_bp.route('/tanggal', methods=['GET'])
def tanggal():
    """
    Endpoint untuk mendapatkan tanggal-tanggal yang tersedia
    
    Returns:
        JSON response dengan list tanggal
    """
    result = bi_service.get_latest_date()
    return jsonify(result)


@harga_bp.route('/test', methods=['GET'])
def test_harga():
    """
    Endpoint untuk testing harga routes
    
    Returns:
        JSON response test message
    """
    return jsonify({
        "success": True,
        "message": "Harga routes is working!",
        "available_endpoints": [
            "GET /harga/",
            "GET /harga/cabai",
            "GET /harga/provinces",
            "GET /harga/regencies?province_id=14",
            "GET /harga/commodities",
            "GET /harga/price-types",
            "GET /harga/tanggal",
            "GET /harga/test"
        ]
    })

# -------------------------------------------------
# 🔹 CACHE MANAGEMENT (BARU)
# -------------------------------------------------

@harga_bp.route('/clear-cache', methods=['POST'])
def clear_cache():
    """
    Endpoint untuk clear cache dan force refresh data
    
    Returns:
        JSON response dengan status clear cache
    """
    result = bi_service.clear_cache()
    return jsonify(result)