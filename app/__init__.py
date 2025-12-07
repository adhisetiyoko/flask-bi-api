# File: app/__init__.py

from flask import Flask, send_from_directory
from app.config.database import config
from app.extensions import mysql, cors
import os

def create_app(config_name='development'):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    mysql.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}})
    
    # Import blueprints
    from app.routes.harga_routes import harga_bp
    from app.routes.master_routes import master_bp
    from app.routes.test_routes import test_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.otp_routes import otp_bp
    from app.routes.produk_routes import produk_bp
    from app.routes.toko_routes import toko_bp
    
    # Register blueprints
    app.register_blueprint(harga_bp, url_prefix="/harga")
    app.register_blueprint(master_bp, url_prefix="/master")
    app.register_blueprint(test_bp, url_prefix="/test")
    app.register_blueprint(auth_bp)
    app.register_blueprint(otp_bp)
    app.register_blueprint(produk_bp, url_prefix="/api")
    app.register_blueprint(toko_bp, url_prefix="/toko")
    
    # Create upload folders
    os.makedirs('uploads/produk', exist_ok=True)
    os.makedirs('uploads/bukti_pembayaran', exist_ok=True)
    os.makedirs('uploads/ktp', exist_ok=True)

    # 🔥 STATIC ROUTE UNTUK FILE GAMBAR
    @app.route('/uploads/<filename>')
    def uploaded_files(filename):
        return send_from_directory('uploads', filename)
    
    @app.route('/uploads/produk/<filename>')
    def produk_image(filename):
        base_path = os.path.abspath(os.path.join(app.root_path, ".."))
        folder_path = os.path.join(base_path, 'uploads', 'produk')
        file_path = os.path.join(folder_path, filename)

        print("REQUEST FILE:", filename)
        print("FULL PATH :", file_path)
        print("EXISTS?   :", os.path.exists(file_path))

        if not os.path.exists(file_path):
            return {"error": "File tidak ditemukan", "path": file_path}, 404

        return send_from_directory(folder_path, filename)



    @app.route("/debug/list-uploads")
    def debug_list_uploads():
        folder_path = os.path.abspath("uploads/produk")
        print("DEBUG CEK FOLDER:", folder_path)

        if not os.path.exists(folder_path):
            return {"error": "Folder tidak ditemukan", "path": folder_path}

        return {
            "path": folder_path,
            "files": os.listdir(folder_path)
        }


    # Root route
    @app.route('/')
    def home():
        return {
            "message": "Server Flask SIMBOK aktif!",
            "status": "running",
            "endpoints": {
                "harga": "/harga",
                "master": "/master",
                "test": "/test",
                "auth": "/auth",
                "otp": "/otp",
                "produk": "/api/produk",
                "toko": "/toko"
            }
        }
    
    print("=== ROUTES TERDAFTAR ===")
    print(app.url_map)

    return app
