# File: app/routes/auth_routes.py

from flask import Blueprint, request, jsonify
import MySQLdb.cursors
import bcrypt
from app.extensions import mysql
from app.services.otp_service import create_user_with_phone  # ← Import fungsi baru

auth_bp = Blueprint('auth', __name__)

# 🔹 Register user (yang sudah ada - untuk register dengan email)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    nama = data.get('name') or data.get('nama')
    email = data.get('email')
    password = data.get('password')
    no_hp = data.get('no_hp', '')
    alamat = data.get('alamat', '')
    role = data.get('role', 'pembeli_rumah_tangga')
    
    if not all([nama, email, password]):
        return jsonify({'message': 'Data tidak lengkap'}), 400
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        cursor.close()
        return jsonify({'message': 'Email sudah terdaftar'}), 409
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute(
        'INSERT INTO users (nama, email, password, no_hp, alamat, role) VALUES (%s, %s, %s, %s, %s, %s)',
        (nama, email, hashed_password.decode('utf-8'), no_hp, alamat, role)
    )
    mysql.connection.commit()
    cursor.close()
    
    return jsonify({'message': 'Registrasi berhasil!'}), 201

# 🔹 Register dengan Phone (HANYA simpan no_hp dan password)
@auth_bp.route('/register-phone', methods=['POST'])
def register_phone():
    """
    Register user baru dengan nomor HP dan password
    Dipanggil SETELAH OTP berhasil diverifikasi dari create_password_screen
    """
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    
    print(f"📝 Register phone request: {phone}")  # Debug log
    
    if not phone or not password:
        return jsonify({
            'success': False,
            'message': 'Phone dan password diperlukan'
        }), 400
    
    try:
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        print(f"🔐 Password hashed successfully")  # Debug log
        
        # Panggil fungsi create user dari otp_service
        result = create_user_with_phone(phone, hashed_password)
        
        print(f"✅ Result: {result}")  # Debug log
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"❌ Error in register_phone: {str(e)}")  # Debug log
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# 🔹 Login user (yang sudah ada)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not all([email, password]):
        return jsonify({'message': 'Data tidak lengkap'}), 400
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    cursor.close()
    
    if not user:
        return jsonify({'message': 'Email tidak ditemukan!'}), 404
    
    if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        user.pop('password')  # Hapus password dari response
        return jsonify({'message': 'Login sukses!', 'user': user}), 200
    else:
        return jsonify({'message': 'Password salah!'}), 401

# 🔹 Login dengan Phone
@auth_bp.route('/login-phone', methods=['POST'])
def login_phone():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')
    
    if not all([phone, password]):
        return jsonify({
            'success': False,
            'message': 'Phone dan password diperlukan'
        }), 400
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE no_hp = %s', (phone,))
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'Nomor HP tidak ditemukan!'
            }), 404
        
        # Cek apakah user sudah terverifikasi
        if user.get('status_akun') == 'perlu_verifikasi':
            return jsonify({
                'success': False,
                'message': 'Akun belum diverifikasi. Silakan verifikasi OTP terlebih dahulu.'
            }), 403
        
        # Cek password
        if user.get('password') and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            user.pop('password')  # Hapus password dari response
            return jsonify({
                'success': True,
                'message': 'Login sukses!',
                'user': user
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Password salah!'
            }), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# 🔹 Test database connection
@auth_bp.route('/test-db', methods=['GET'])
def test_db():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        return jsonify({'message': 'Database connected!'}), 200
    except Exception as e:
        return jsonify({'message': f'Database error: {str(e)}'}), 500