# File: app/routes/produk_routes.py

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import MySQLdb.cursors
import os
from datetime import datetime
from app.extensions import mysql

produk_bp = Blueprint('produk', __name__)

UPLOAD_FOLDER = 'uploads/produk'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ✅ HELPER FUNCTION YANG DIPERBAIKI
def get_current_user():
    """
    Ambil user berdasarkan X-User-Id header
    """
    user_id = request.headers.get('X-User-Id')
    
    print(f"🔍 Checking user_id from header: {user_id}")
    
    if not user_id:
        print("❌ No X-User-Id header found")
        return None
    
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        
        if user:
            print(f"✅ User found: {user['nama']} (role: {user['role']})")
        else:
            print(f"❌ No user found with id: {user_id}")
        
        return user
    except Exception as e:
        print(f"❌ Error in get_current_user: {e}")
        return None


# ==================== CREATE ====================
@produk_bp.route('/produk', methods=['POST'])
def tambah_produk():
    """
    Endpoint untuk menambah produk cabai baru
    """
    try:
        print("=" * 50)
        print("📥 REQUEST TAMBAH PRODUK")
        print("=" * 50)
        
        # ✅ Debug headers
        print("📋 Headers:", dict(request.headers))
        
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User tidak terautentikasi. Pastikan header X-User-Id dikirim.'
            }), 401

        # Validasi role petani
        if current_user['role'] != 'petani':
            return jsonify({
                'success': False,
                'message': f"Hanya petani yang dapat menambah produk. Role Anda: {current_user['role']}"
            }), 403

        # Ambil data dari form
        jenis_cabai = request.form.get('jenis_cabai')
        tingkat_kepedasan = request.form.get('tingkat_kepedasan', '')
        kondisi = request.form.get('kondisi', 'Segar')
        berat = request.form.get('berat')
        satuan = request.form.get('satuan', 'Kg')
        harga = request.form.get('harga')
        deskripsi = request.form.get('deskripsi', '')

        print(f"📝 Form Data:")
        print(f"   - Jenis Cabai: {jenis_cabai}")
        print(f"   - Tingkat Kepedasan: {tingkat_kepedasan}")
        print(f"   - Kondisi: {kondisi}")
        print(f"   - Berat: {berat} {satuan}")
        print(f"   - Harga: Rp {harga}")
        print(f"   - Deskripsi: {deskripsi[:50]}..." if len(deskripsi) > 50 else f"   - Deskripsi: {deskripsi}")

        # Validasi data wajib
        if not all([jenis_cabai, berat, harga]):
            return jsonify({
                'success': False,
                'message': 'Jenis cabai, berat, dan harga wajib diisi'
            }), 400

        # Validasi format angka
        try:
            berat = float(berat)
            harga = float(harga)
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Format berat atau harga tidak valid'
            }), 400

        # Proses upload foto (multiple)
        foto_paths = []
        if 'foto' in request.files:
            files = request.files.getlist('foto')
            print(f"📷 Jumlah foto yang diupload: {len(files)}")
            
            # Validasi maksimal 5 foto
            if len(files) > 5:
                return jsonify({
                    'success': False,
                    'message': 'Maksimal 5 foto'
                }), 400

            for idx, file in enumerate(files):
                if file and file.filename and allowed_file(file.filename):
                    # Generate unique filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = secure_filename(f"{current_user['id']}_{timestamp}_{idx}.{ext}")
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    
                    # Buat folder jika belum ada
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    
                    # Simpan file
                    file.save(filepath)
                    foto_paths.append(filepath)
                    print(f"   ✅ Foto {idx+1} disimpan: {filepath}")
                else:
                    print(f"   ⚠️ Foto {idx+1} tidak valid atau tidak ada filename")
        else:
            print("⚠️ Tidak ada foto yang diupload")

        # Gabungkan path foto dengan separator
        foto_string = ','.join(foto_paths) if foto_paths else None

        # Buat nama produk otomatis
        nama_produk = f"{jenis_cabai} - {kondisi} ({berat} {satuan})"

        # Konversi berat ke Kg untuk stok
        stok_kg = berat
        if satuan == 'Ons':
            stok_kg = berat / 10
        elif satuan == 'Gram':
            stok_kg = berat / 1000

        print(f"📦 Stok (dalam Kg): {stok_kg}")

        # Buat deskripsi lengkap
        deskripsi_lengkap = f"{deskripsi}\n\nJenis: {jenis_cabai}\nTingkat Kepedasan: {tingkat_kepedasan}\nKondisi: {kondisi}"

        # Simpan ke database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        query = """
            INSERT INTO produk 
            (id_petani, nama_produk, deskripsi, harga_per_kg, stok, foto, status_produk)
            VALUES (%s, %s, %s, %s, %s, %s, 'aktif')
        """
        
        cursor.execute(query, (
            current_user['id'],
            nama_produk,
            deskripsi_lengkap,
            harga,
            stok_kg,
            foto_string
        ))

        mysql.connection.commit()
        produk_id = cursor.lastrowid
        cursor.close()

        print(f"✅ Produk berhasil ditambahkan dengan ID: {produk_id}")
        print("=" * 50)

        return jsonify({
            'success': True,
            'message': 'Produk berhasil ditambahkan',
            'data': {
                'id': produk_id,
                'nama_produk': nama_produk,
                'jenis_cabai': jenis_cabai,
                'harga': harga,
                'stok': stok_kg,
                'foto_count': len(foto_paths)
            }
        }), 201

    except Exception as e:
        print(f"❌ Error in tambah_produk: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ==================== READ ALL ====================
@produk_bp.route('/produk', methods=['GET'])
def get_all_produk():
    """
    Endpoint untuk mendapatkan daftar semua produk cabai
    Query params: 
    - jenis_cabai: filter berdasarkan jenis
    - status: filter status (default: aktif)
    - petani_id: filter berdasarkan petani
    """
    try:
        # Ambil query parameters
        jenis_cabai = request.args.get('jenis_cabai')
        status = request.args.get('status', 'aktif')
        petani_id = request.args.get('petani_id')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Build query
        query = """
            SELECT p.*, 
                   u.nama as nama_petani,
                   u.no_hp as kontak_petani,
                   t.nama_toko,
                   t.alamat_toko
            FROM produk p
            LEFT JOIN users u ON p.id_petani = u.id
            LEFT JOIN toko t ON u.id = t.id_user
            WHERE p.status_produk = %s
        """
        params = [status]

        # Filter berdasarkan jenis cabai
        if jenis_cabai:
            query += " AND p.nama_produk LIKE %s"
            params.append(f"%{jenis_cabai}%")

        # Filter berdasarkan petani
        if petani_id:
            query += " AND p.id_petani = %s"
            params.append(petani_id)

        query += " ORDER BY p.tanggal_upload DESC"

        cursor.execute(query, params)
        produk_list = cursor.fetchall()
        cursor.close()

        # Format data
        for produk in produk_list:
            # Split foto paths
            if produk['foto']:
                produk['foto'] = produk['foto'].split(',')
            else:
                produk['foto'] = []

            # Format harga dan stok
            produk['harga_per_kg'] = float(produk['harga_per_kg'])
            produk['stok'] = float(produk['stok'])

        return jsonify({
            'success': True,
            'data': produk_list,
            'total': len(produk_list)
        }), 200

    except Exception as e:
        print(f"❌ Error in get_all_produk: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ==================== READ ONE ====================
@produk_bp.route('/produk/<int:produk_id>', methods=['GET'])
def get_produk_detail(produk_id):
    """
    Endpoint untuk mendapatkan detail produk cabai
    """
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        query = """
            SELECT p.*, 
                   u.nama as nama_petani,
                   u.no_hp as kontak_petani,
                   u.alamat as alamat_petani,
                   t.nama_toko,
                   t.alamat_toko,
                   t.jasa_pengiriman
            FROM produk p
            LEFT JOIN users u ON p.id_petani = u.id
            LEFT JOIN toko t ON u.id = t.id_user
            WHERE p.id = %s
        """

        cursor.execute(query, (produk_id,))
        produk = cursor.fetchone()
        cursor.close()

        if not produk:
            return jsonify({
                'success': False,
                'message': 'Produk tidak ditemukan'
            }), 404

        # Format data
        if produk['foto']:
            produk['foto'] = produk['foto'].split(',')
        else:
            produk['foto'] = []

        produk['harga_per_kg'] = float(produk['harga_per_kg'])
        produk['stok'] = float(produk['stok'])

        return jsonify({
            'success': True,
            'data': produk
        }), 200

    except Exception as e:
        print(f"❌ Error in get_produk_detail: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ==================== UPDATE ====================
# Ganti endpoint UPDATE di file: app/routes/produk_routes.py
@produk_bp.route('/produk/<int:produk_id>', methods=['PUT'])
def update_produk(produk_id):
    """
    Endpoint untuk mengupdate produk cabai
    Support multipart/form-data untuk upload foto baru
    """
    try:
        print("=" * 50)
        print(f"📝 UPDATE PRODUK ID: {produk_id}")
        print("=" * 50)
        
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User tidak terautentikasi'
            }), 401

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Cek kepemilikan produk
        cursor.execute("SELECT * FROM produk WHERE id = %s", (produk_id,))
        produk = cursor.fetchone()

        if not produk:
            cursor.close()
            return jsonify({
                'success': False,
                'message': 'Produk tidak ditemukan'
            }), 404

        if produk['id_petani'] != current_user['id'] and current_user['role'] != 'admin':
            cursor.close()
            return jsonify({
                'success': False,
                'message': 'Anda tidak memiliki akses untuk mengubah produk ini'
            }), 403

        # Ambil data dari form (bukan JSON karena ada file upload)
        nama_produk = request.form.get('nama_produk')
        tingkat_kepedasan = request.form.get('tingkat_kepedasan')
        kondisi = request.form.get('kondisi')
        stok = request.form.get('stok')
        satuan = request.form.get('satuan')
        harga = request.form.get('harga_per_kg')
        deskripsi = request.form.get('deskripsi')
        status_produk = request.form.get('status_produk')
        main_image_index = request.form.get('main_image_index', '0')

        print(f"📋 Data yang akan diupdate:")
        print(f"   - Nama: {nama_produk}")
        print(f"   - Tingkat Kepedasan: {tingkat_kepedasan}")
        print(f"   - Kondisi: {kondisi}")
        print(f"   - Stok: {stok} {satuan}")
        print(f"   - Harga: {harga}")
        print(f"   - Status: {status_produk}")

        # Handle foto lama yang dipertahankan
        existing_photos = []
        i = 0
        while True:
            photo = request.form.get(f'existing_photos[{i}]')
            if photo is None:
                break
            existing_photos.append(photo)
            i += 1
        
        print(f"📷 Foto lama yang dipertahankan: {len(existing_photos)} foto")
        for idx, photo in enumerate(existing_photos):
            print(f"   {idx+1}. {photo}")

        # Handle foto baru yang diupload
        new_photo_paths = []
        if 'new_photos' in request.files:
            new_files = request.files.getlist('new_photos')
            print(f"📸 Foto baru yang diupload: {len(new_files)} foto")
            
            for idx, file in enumerate(new_files):
                if file and file.filename and allowed_file(file.filename):
                    # Generate unique filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = secure_filename(f"{current_user['id']}_{timestamp}_{idx}.{ext}")
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    
                    # Buat folder jika belum ada
                    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                    
                    # Simpan file
                    file.save(filepath)
                    new_photo_paths.append(filepath)
                    print(f"   ✅ Foto baru {idx+1} disimpan: {filepath}")

        # Gabungkan foto lama + foto baru
        all_photos = existing_photos + new_photo_paths
        foto_string = ','.join(all_photos) if all_photos else None

        print(f"📦 Total foto setelah update: {len(all_photos)}")

        # Hapus foto lama yang tidak dipertahankan
        if produk['foto']:
            old_photos = produk['foto'].split(',')
            for old_photo in old_photos:
                if old_photo not in existing_photos:
                    if os.path.exists(old_photo):
                        try:
                            os.remove(old_photo)
                            print(f"🗑️ Foto lama dihapus: {old_photo}")
                        except Exception as e:
                            print(f"⚠️ Gagal hapus foto: {e}")

        # Build update query
        update_fields = []
        params = []

        if nama_produk:
            update_fields.append("nama_produk = %s")
            params.append(nama_produk)

        if deskripsi is not None:
            # Buat deskripsi lengkap jika ada data tambahan
            if tingkat_kepedasan or kondisi:
                deskripsi_lengkap = f"{deskripsi}\n\n"
                if tingkat_kepedasan:
                    deskripsi_lengkap += f"Tingkat Kepedasan: {tingkat_kepedasan}\n"
                if kondisi:
                    deskripsi_lengkap += f"Kondisi: {kondisi}"
                update_fields.append("deskripsi = %s")
                params.append(deskripsi_lengkap)
            else:
                update_fields.append("deskripsi = %s")
                params.append(deskripsi)

        if harga:
            update_fields.append("harga_per_kg = %s")
            params.append(float(harga))

        if stok:
            # Konversi ke Kg jika perlu
            stok_kg = float(stok)
            if satuan == 'Ons':
                stok_kg = stok_kg / 10
            elif satuan == 'Gram':
                stok_kg = stok_kg / 1000
            
            update_fields.append("stok = %s")
            params.append(stok_kg)

        if status_produk:
            update_fields.append("status_produk = %s")
            params.append(status_produk)

        if foto_string is not None:
            update_fields.append("foto = %s")
            params.append(foto_string)

        if not update_fields:
            cursor.close()
            return jsonify({
                'success': False,
                'message': 'Tidak ada data yang diupdate'
            }), 400

        # Execute update
        params.append(produk_id)
        query = f"UPDATE produk SET {', '.join(update_fields)} WHERE id = %s"
        
        print(f"🔄 Executing query: {query}")
        print(f"📊 Params: {params}")
        
        cursor.execute(query, params)
        mysql.connection.commit()
        
        # Get updated produk
        cursor.execute("SELECT * FROM produk WHERE id = %s", (produk_id,))
        updated_produk = cursor.fetchone()
        cursor.close()

        print(f"✅ Produk berhasil diupdate!")
        print("=" * 50)

        return jsonify({
            'success': True,
            'message': 'Produk berhasil diupdate',
            'data': updated_produk
        }), 200

    except Exception as e:
        print(f"❌ Error in update_produk: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

# ==================== DELETE ====================
@produk_bp.route('/produk/<int:produk_id>', methods=['DELETE'])
def delete_produk(produk_id):
    """
    Endpoint untuk menghapus produk cabai
    """
    try:
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User tidak terautentikasi'
            }), 401

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Cek kepemilikan produk
        cursor.execute("SELECT * FROM produk WHERE id = %s", (produk_id,))
        produk = cursor.fetchone()

        if not produk:
            cursor.close()
            return jsonify({
                'success': False,
                'message': 'Produk tidak ditemukan'
            }), 404

        if produk['id_petani'] != current_user['id'] and current_user['role'] != 'admin':
            cursor.close()
            return jsonify({
                'success': False,
                'message': 'Anda tidak memiliki akses untuk menghapus produk ini'
            }), 403

        # Hapus foto jika ada
        if produk['foto']:
            foto_paths = produk['foto'].split(',')
            for foto_path in foto_paths:
                if os.path.exists(foto_path):
                    try:
                        os.remove(foto_path)
                        print(f"🗑️ Foto dihapus: {foto_path}")
                    except Exception as e:
                        print(f"⚠️ Gagal hapus foto: {e}")

        # Hapus dari database
        cursor.execute("DELETE FROM produk WHERE id = %s", (produk_id,))
        mysql.connection.commit()
        cursor.close()

        print(f"✅ Produk ID {produk_id} berhasil dihapus")

        return jsonify({
            'success': True,
            'message': 'Produk berhasil dihapus'
        }), 200

    except Exception as e:
        print(f"❌ Error in delete_produk: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ==================== MY PRODUCTS ====================
@produk_bp.route('/produk/saya', methods=['GET'])
def get_my_produk():
    """
    Endpoint untuk mendapatkan daftar produk milik petani yang login
    """
    try:
        # Get current user
        current_user = get_current_user()
        if not current_user:
            return jsonify({
                'success': False,
                'message': 'User tidak terautentikasi'
            }), 401

        if current_user['role'] != 'petani':
            return jsonify({
                'success': False,
                'message': 'Endpoint ini hanya untuk petani'
            }), 403

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        query = """
            SELECT * FROM produk 
            WHERE id_petani = %s 
            ORDER BY tanggal_upload DESC
        """

        cursor.execute(query, (current_user['id'],))
        produk_list = cursor.fetchall()
        cursor.close()

        # Format data
        for produk in produk_list:
            if produk['foto']:
                produk['foto'] = produk['foto'].split(',')
            else:
                produk['foto'] = []

            produk['harga_per_kg'] = float(produk['harga_per_kg'])
            produk['stok'] = float(produk['stok'])

        return jsonify({
            'success': True,
            'data': produk_list,
            'total': len(produk_list)
        }), 200

    except Exception as e:
        print(f"❌ Error in get_my_produk: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ==================== POPULAR PRODUCTS ====================
@produk_bp.route('/popular-products', methods=['GET'])
def get_popular_products():
    """
    Endpoint untuk mendapatkan produk populer dari semua petani
    Untuk ditampilkan di homepage
    """
    try:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        query = """
            SELECT p.*, 
                   u.nama as nama_petani,
                   u.no_hp as kontak_petani,
                   t.nama_toko,
                   t.alamat_toko,
                   t.jasa_pengiriman
            FROM produk p
            LEFT JOIN users u ON p.id_petani = u.id
            LEFT JOIN toko t ON u.id = t.id_user
            WHERE p.status_produk = 'aktif'
            ORDER BY p.tanggal_upload DESC
            LIMIT 8
        """

        cursor.execute(query)
        produk_list = cursor.fetchall()
        cursor.close()

        # Format data
        for produk in produk_list:
            # Split foto paths
            if produk['foto']:
                produk['foto'] = produk['foto'].split(',')
            else:
                produk['foto'] = []

            # Format harga dan stok
            produk['harga_per_kg'] = float(produk['harga_per_kg'])
            produk['stok'] = float(produk['stok'])

        print(f"✅ Popular products loaded: {len(produk_list)} items")

        return jsonify({
            'success': True,
            'data': produk_list,
            'total': len(produk_list)
        }), 200

    except Exception as e:
        print(f"❌ Error in get_popular_products: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


# ==================== ALL PRODUCTS (PUBLIC) ====================
@produk_bp.route('/all-products', methods=['GET'])
def get_all_products_public():
    """
    Endpoint untuk mendapatkan semua produk aktif dari semua petani
    Untuk catalog/browse products
    """
    try:
        # Ambil query parameters untuk filtering
        jenis_cabai = request.args.get('jenis_cabai')
        min_price = request.args.get('min_price')
        max_price = request.args.get('max_price')
        sort_by = request.args.get('sort_by', 'terbaru')  # terbaru, termurah, termahal
        limit = int(request.args.get('limit', 20))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Build query
        query = """
            SELECT p.*, 
                   u.nama as nama_petani,
                   u.no_hp as kontak_petani,
                   t.nama_toko,
                   t.alamat_toko,
                   t.jasa_pengiriman
            FROM produk p
            LEFT JOIN users u ON p.id_petani = u.id
            LEFT JOIN toko t ON u.id = t.id_user
            WHERE p.status_produk = 'aktif'
        """
        params = []

        # Filter jenis cabai
        if jenis_cabai:
            query += " AND p.nama_produk LIKE %s"
            params.append(f"%{jenis_cabai}%")

        # Filter harga minimum
        if min_price:
            query += " AND p.harga_per_kg >= %s"
            params.append(float(min_price))

        # Filter harga maksimum
        if max_price:
            query += " AND p.harga_per_kg <= %s"
            params.append(float(max_price))

        # Sorting
        if sort_by == 'termurah':
            query += " ORDER BY p.harga_per_kg ASC"
        elif sort_by == 'termahal':
            query += " ORDER BY p.harga_per_kg DESC"
        else:  # terbaru (default)
            query += " ORDER BY p.tanggal_upload DESC"

        # Limit
        query += f" LIMIT {limit}"

        cursor.execute(query, params)
        produk_list = cursor.fetchall()
        cursor.close()

        # Format data
        for produk in produk_list:
            if produk['foto']:
                produk['foto'] = produk['foto'].split(',')
            else:
                produk['foto'] = []

            produk['harga_per_kg'] = float(produk['harga_per_kg'])
            produk['stok'] = float(produk['stok'])

        print(f"✅ All products loaded: {len(produk_list)} items")

        return jsonify({
            'success': True,
            'data': produk_list,
            'total': len(produk_list)
        }), 200

    except Exception as e:
        print(f"❌ Error in get_all_products_public: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500