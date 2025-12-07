# app/routes/master_routes.py
from flask import Blueprint, jsonify, request
from app.services.bi_service import get_provinces, get_commodities, get_regencies

master_bp = Blueprint('master', __name__)

@master_bp.route('/provinces')
def provinces():
    return get_provinces()

@master_bp.route('/commodities')
def commodities():
    return get_commodities()

@master_bp.route('/regencies')
def regencies():
    return get_regencies(request)
    
