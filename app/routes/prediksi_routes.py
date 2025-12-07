# routes/prediksi_routes.py

from flask import Blueprint, jsonify, request
from app.services.prediction_service import PredictionService

prediksi_bp = Blueprint('prediksi', __name__)
# Inisialisasi service saat Blueprint dibuat
prediction_service = PredictionService() 

@prediksi_bp.route('/prediksi/harga', methods=['GET'])
def get_prediksi_harga():
    komoditas = request.args.get('komoditas')
    provinsi = request.args.get('provinsi')
    tanggal = request.args.get('tanggal')

    # Panggil logika prediksi
    harga_prediksi = prediction_service.predict_price(komoditas, provinsi, tanggal)

    return jsonify({
        "status": "success",
        "komoditas": komoditas,
        "prediksi_harga": f"Rp {harga_prediksi:,.0f}"
    })