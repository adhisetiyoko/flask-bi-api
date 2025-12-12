# app/routes/otp_routes.py
from flask import Blueprint, request, jsonify
from app.services.otp_service import send_otp , verify_otp

otp_bp = Blueprint('otp', __name__)

@otp_bp.route('/send-otp', methods=['POST'])
def send_otp_route():
    data = request.get_json()
    phone = data.get("phone")

    if not phone:
        return jsonify({"error": "phone is required"}), 400

    result = send_otp(phone)

    return jsonify(result)

# TAMBAHKAN ROUTE INI ✅
@otp_bp.route('/verify-otp', methods=['POST'])
def verify_otp_route():
    data = request.get_json()
    phone = data.get("phone")
    otp = data.get("otp")
    
    if not phone or not otp:
        return jsonify({"error": "phone and otp are required"}), 400
    
    result = verify_otp(phone, otp)
    return jsonify(result)