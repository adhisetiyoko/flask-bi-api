# app/routes/test_routes.py
from flask import Blueprint, jsonify

test_bp = Blueprint('test', __name__, url_prefix='/test')

@test_bp.route('/')
def test():
    return jsonify({
        "success": True,
        "message": "Flask backend modular berjalan!",
        "version": "1.0"
    })
