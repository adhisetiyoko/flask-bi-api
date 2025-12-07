"""
app/routes/toko_routes.py
Routes untuk pendaftaran toko petani
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from app.extensions import mysql
import MySQLdb.cursors

toko_bp = Blueprint('toko', __name__, url_prefix='/toko')

UPLOAD_FOLDER = 'uploads/ktp'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# -------------------------------------------------
# 🔹 DAFTAR TOKO TANPA VERIFIKASI
# -------------------------------------------------
@toko_bp.route('/daftar', methods=['POST'])
def daftar_toko():
    try:
        id_user = request.form.get('id_user')
        jenis_usaha = request.form.get('jenis_usaha')
        nama_pemilik = request.form.get('nama_pemilik')
        nik = request.form.get('nik')
        nama_toko = request.form.get('nama_toko')
        email_toko = request.form.get('email_toko')
        alamat_toko = request.form.get('alamat_toko')
        jasa_pengiriman = request.form.get('jasa_pengiriman')

        # Validasi field wajib
        if not all([id_user, jenis_usaha, nama_pemilik, nik, nama_toko, alamat_toko]):
            return jsonify({"success": False, "error": "Semua field wajib diisi"}), 400

        if len(nik) != 16 or not nik.isdigit():
            return jsonify({"success": False, "error": "NIK harus 16 digit angka"}), 400

        # Upload KTP
        foto_ktp_path = None
        if 'foto_ktp' in request.files:
            file = request.files['foto_ktp']
            if file and file.filename and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = secure_filename(f"ktp_{id_user}_{int(datetime.now().timestamp())}.{ext}")
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                foto_ktp_path = filepath

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Cek apakah user sudah punya toko
        cursor.execute("SELECT id FROM toko WHERE id_user = %s", (id_user,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({"success": False, "error": "User sudah memiliki toko"}), 400

        # Insert toko tanpa kolom status_verifikasi
        cursor.execute("""
            INSERT INTO toko (
                id_user, nama_toko, email_toko, alamat_toko,
                jasa_pengiriman, jenis_usaha, foto_ktp,
                nama_pemilik, nik
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            id_user, nama_toko, email_toko, alamat_toko,
            jasa_pengiriman, jenis_usaha, foto_ktp_path,
            nama_pemilik, nik
        ))

        toko_id = cursor.lastrowid

        # Langsung ubah user jadi petani (tanpa verifikasi admin)
        cursor.execute("""
            UPDATE users
            SET role = 'petani',
                is_verified_seller = TRUE,
                tanggal_jadi_petani = NOW()
            WHERE id = %s
        """, (id_user,))

        mysql.connection.commit()
        cursor.close()

        return jsonify({
            "success": True,
            "message": "Toko berhasil didaftarkan",
            "data": {
                "toko_id": toko_id,
                "nama_toko": nama_toko
            }
        }), 201

    except Exception as e:
        print(f"[Toko Routes ERROR] {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------
# 🔹 GET TOKO BY USER
# -------------------------------------------------
@toko_bp.route('/user/<int:user_id>', methods=['GET'])
def get_toko_by_user(user_id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT t.*, u.nama AS nama_user, u.no_hp
            FROM toko t
            JOIN users u ON t.id_user = u.id
            WHERE t.id_user = %s
        """, (user_id,))

        toko = cursor.fetchone()
        cursor.close()

        if not toko:
            return jsonify({"success": False, "error": "Toko tidak ditemukan"}), 404

        return jsonify({"success": True, "data": toko}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------------------------------
# 🔹 CHECK TOKO
# -------------------------------------------------
@toko_bp.route('/check/<int:user_id>', methods=['GET'])
def check_toko(user_id):
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            SELECT id, nama_toko
            FROM toko
            WHERE id_user = %s
        """, (user_id,))

        toko = cursor.fetchone()
        cursor.close()

        return jsonify({
            "success": True,
            "has_toko": toko is not None,
            "data": toko
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
