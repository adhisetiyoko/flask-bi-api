# File: app/routes/keranjang_routes.py

from flask import Blueprint, request, jsonify
import MySQLdb.cursors
from app.extensions import mysql

keranjang_bp = Blueprint('keranjang', __name__)

# Helper function
def get_current_user():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        return None
    
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return user

# ========== TAMBAH KE KERANJANG ==========
@keranjang_bp.route('/keranjang', methods=['POST'])
def tambah_keranjang():
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User tidak terautentikasi'
            }), 401
        
        data = request.get_json()
        produk_id = data.get('produk_id')
        jumlah = data.get('jumlah')
        
        if not produk_id or not jumlah:
            return jsonify({
                'success': False,
                'message': 'Data tidak lengkap'
            }), 400
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Cek produk exists & get harga
        cursor.execute(
            'SELECT harga_per_kg, stok FROM produk WHERE id = %s',
            (produk_id,)
        )
        produk = cursor.fetchone()
        
        if not produk:
            cursor.close()
            return jsonify({
                'success': False,
                'message': 'Produk tidak ditemukan'
            }), 404
        
        # Cek stok
        if float(jumlah) > float(produk['stok']):
            cursor.close()
            return jsonify({
                'success': False,
                'message': f'Stok tidak cukup. Tersedia: {produk["stok"]} Kg'
            }), 400
        
        # Cek apakah sudah ada di keranjang
        cursor.execute(
            'SELECT * FROM keranjang WHERE user_id = %s AND produk_id = %s',
            (current_user['id'], produk_id)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Update jumlah
            new_jumlah = float(existing['jumlah']) + float(jumlah)
            cursor.execute(
                'UPDATE keranjang SET jumlah = %s WHERE id = %s',
                (new_jumlah, existing['id'])
            )
        else:
            # Insert baru
            cursor.execute(
                '''INSERT INTO keranjang 
                   (user_id, produk_id, jumlah, harga_satuan) 
                   VALUES (%s, %s, %s, %s)''',
                (current_user['id'], produk_id, jumlah, produk['harga_per_kg'])
            )
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Produk berhasil ditambahkan ke keranjang'
        }), 201
        
    except Exception as e:
        print(f"Error tambah_keranjang: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# ========== GET KERANJANG ==========
@keranjang_bp.route('/keranjang', methods=['GET'])
def get_keranjang():
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User tidak terautentikasi'
            }), 401
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        query = '''
            SELECT 
                k.id as keranjang_id,
                k.jumlah,
                k.harga_satuan,
                p.id as produk_id,
                p.nama_produk,
                p.foto,
                p.stok,
                t.nama_toko
            FROM keranjang k
            JOIN produk p ON k.produk_id = p.id
            LEFT JOIN toko t ON p.id_petani = t.user_id
            WHERE k.user_id = %s
            ORDER BY k.tanggal_ditambahkan DESC
        '''
        
        cursor.execute(query, (current_user['id'],))
        items = cursor.fetchall()
        cursor.close()
        
        # Format data
        total = 0
        for item in items:
            if item['foto']:
                item['foto'] = item['foto'].split(',')
            else:
                item['foto'] = []
            
            subtotal = float(item['jumlah']) * float(item['harga_satuan'])
            item['subtotal'] = subtotal
            total += subtotal
        
        return jsonify({
            'success': True,
            'data': items,
            'total': total,
            'jumlah_item': len(items)
        }), 200
        
    except Exception as e:
        print(f"Error get_keranjang: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# ========== UPDATE JUMLAH ==========
@keranjang_bp.route('/keranjang/<int:keranjang_id>', methods=['PUT'])
def update_keranjang(keranjang_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User tidak terautentikasi'
            }), 401
        
        data = request.get_json()
        jumlah = data.get('jumlah')
        
        if not jumlah or float(jumlah) <= 0:
            return jsonify({
                'success': False,
                'message': 'Jumlah tidak valid'
            }), 400
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute(
            'UPDATE keranjang SET jumlah = %s WHERE id = %s AND user_id = %s',
            (jumlah, keranjang_id, current_user['id'])
        )
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Keranjang berhasil diupdate'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# ========== HAPUS ITEM ==========
@keranjang_bp.route('/keranjang/<int:keranjang_id>', methods=['DELETE'])
def hapus_keranjang(keranjang_id):
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User tidak terautentikasi'
            }), 401
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute(
            'DELETE FROM keranjang WHERE id = %s AND user_id = %s',
            (keranjang_id, current_user['id'])
        )
        
        mysql.connection.commit()
        cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Item berhasil dihapus'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500