# app/routes/commodity_routes.py
from flask import Blueprint, jsonify
import requests

commodity_bp = Blueprint('commodity_bp', __name__)

@commodity_bp.route('/master/commodities', methods=['GET'])
def get_commodities():
    try:
        url = "https://www.bi.go.id/hargapangan/WebSite/Home/GetCommodityAll"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        commodities = data.get("data", {}).get("data", [])

        clean_data = [
            {"id": item["TreeID"], "name": item["TreeName"]}
            for item in commodities
        ]

        return jsonify({"success": True, "commodities": clean_data})
    except requests.RequestException as e:
        return jsonify({"success": False, "error": str(e)})
