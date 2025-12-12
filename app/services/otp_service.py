# File: app/services/otp_service.py
import random
import requests
import logging
import MySQLdb.cursors
from app.extensions import mysql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OTP_STORE = {}

def send_otp(phone):
    """Mengirim OTP ke WhatsApp menggunakan Fonnte"""
    
    otp = str(random.randint(100000, 999999))
    
    # Format nomor telepon
    formatted_phone = phone
    if phone.startswith('0'):
        formatted_phone = '62' + phone[1:]
    elif phone.startswith('+62'):
        formatted_phone = phone[1:]
    elif not phone.startswith('62'):
        formatted_phone = '62' + phone
    
    logger.info(f"Sending OTP to: {formatted_phone}")
    logger.info(f"OTP Code: {otp}")
    
    OTP_STORE[formatted_phone] = otp
    
    url = "https://api.fonnte.com/send"
    token = "vXLoBGZjP7BsqrWEF1hB"
    
    payload = {
        "target": formatted_phone,
        "message": f"""*Kode Verifikasi OTP*
Kode OTP Anda: *{otp}*
Kode ini berlaku selama 5 menit.
Jangan bagikan kode ini kepada siapapun."""
    }
    
    headers = {"Authorization": token}
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        result = response.json()
        
        logger.info(f"Response: {result}")
        
        if response.status_code == 200 and result.get("status") == True:
            return {
                "success": True,
                "message": "OTP berhasil dikirim ke WhatsApp",
                "otp": otp,
                "phone": formatted_phone
            }
        else:
            return {
                "success": False,
                "message": f"Gagal: {result.get('detail', 'Unknown error')}",
                "otp": None
            }
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "otp": None
        }


def verify_otp(phone, otp_input):
    """Verifikasi OTP"""
    formatted_phone = phone
    if phone.startswith('0'):
        formatted_phone = '62' + phone[1:]
    elif phone.startswith('+62'):
        formatted_phone = phone[1:]
    elif not phone.startswith('62'):
        formatted_phone = '62' + phone
    
    if formatted_phone not in OTP_STORE:
        return {
            "success": False,
            "message": "OTP tidak ditemukan atau sudah kadaluarsa"
        }
    
    stored_otp = OTP_STORE[formatted_phone]
    
    if stored_otp == str(otp_input):
        del OTP_STORE[formatted_phone]
        return {
            "success": True,
            "message": "OTP valid"
        }
    else:
        return {
            "success": False,
            "message": "OTP tidak valid"
        }


# ✅ TAMBAHKAN FUNGSI INI
def create_user_with_phone(phone, password_hash):
    """
    Buat user baru dengan nomor HP dan password
    Dipanggil SETELAH OTP berhasil diverifikasi dari /register-phone
    
    INSERT: no_hp, password, nama (NULL), email (NULL), role, status_akun
    """
    try:
        # Format nomor telepon
        formatted_phone = phone
        if phone.startswith('0'):
            formatted_phone = '62' + phone[1:]
        elif phone.startswith('+62'):
            formatted_phone = phone[1:]
        elif not phone.startswith('62'):
            formatted_phone = '62' + phone
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Cek apakah nomor HP sudah terdaftar
        cursor.execute('SELECT * FROM users WHERE no_hp = %s', (formatted_phone,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            logger.warning(f"Phone {formatted_phone} already registered")
            return {
                'success': False,
                'message': 'Nomor HP sudah terdaftar'
            }
        
        # ✅ Insert user dengan nama dan email NULL
        cursor.execute(
            '''INSERT INTO users (no_hp, password, nama, email, role, status_akun) 
               VALUES (%s, %s, %s, %s, %s, %s)''',
            (
                formatted_phone,
                password_hash,
                None,                   # nama = NULL
                None,                   # email = NULL
                'pembeli_rumah_tangga',
                'aktif'
            )
        )
        mysql.connection.commit()
        
        user_id = cursor.lastrowid
        
        # Get user data yang baru dibuat (termasuk nama dan email)
        cursor.execute(
            'SELECT id, no_hp, nama, email, role, status_akun FROM users WHERE id = %s', 
            (user_id,)
        )
        new_user = cursor.fetchone()
        
        cursor.close()
        
        logger.info(f"User created successfully: {formatted_phone}")
        
        return {
            'success': True,
            'message': 'User berhasil dibuat',
            'user': new_user
        }
        
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return {
            'success': False,
            'message': f'Gagal membuat user: {str(e)}'
        }