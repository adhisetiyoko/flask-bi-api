# File: app/__init__.py
from flask import Flask, send_from_directory
from app.extensions import mysql, cors
import os

def create_app(config_name=None):
    """Application factory function"""
    app = Flask(__name__)

    # Detect environment
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')

    print(f"🚀 Loading config: {config_name}")

    # Load configuration - FIX: Import Config langsung
    from config import Config
    app.config.from_object(Config)

    # Debug config (tanpa password)
    print(f"📦 MYSQL_HOST: {app.config.get('MYSQL_HOST')}")
    print(f"📦 MYSQL_USER: {app.config.get('MYSQL_USER')}")
    print(f"📦 MYSQL_DB: {app.config.get('MYSQL_DB')}")
    print(f"📦 MYSQL_PORT: {app.config.get('MYSQL_PORT')}")

    # Initialize extensions
    try:
        mysql.init_app(app)
        print("✅ MySQL initialized")
    except Exception as e:
        print(f"⚠️ MySQL init warning: {e}")

    # CORS origins - tambahkan default value
    cors_origins = app.config.get('CORS_ORIGINS', '*')
    cors.init_app(app, resources={r"/*": {"origins": cors_origins}})

    # Import and register blueprints
    try:
        from app.routes.harga_routes import harga_bp
        from app.routes.master_routes import master_bp
        from app.routes.test_routes import test_bp
        from app.routes.auth_routes import auth_bp
        from app.routes.otp_routes import otp_bp
        from app.routes.produk_routes import produk_bp
        from app.routes.toko_routes import toko_bp

        app.register_blueprint(harga_bp, url_prefix="/harga")
        app.register_blueprint(master_bp, url_prefix="/master")
        app.register_blueprint(test_bp, url_prefix="/test")
        app.register_blueprint(auth_bp)
        app.register_blueprint(otp_bp)
        app.register_blueprint(produk_bp, url_prefix="/api")
        app.register_blueprint(toko_bp, url_prefix="/toko")
        print("✅ All blueprints registered")
    except Exception as e:
        print(f"❌ Blueprint registration error: {e}")
        import traceback
        traceback.print_exc()

    # Create upload folders
    os.makedirs('uploads/produk', exist_ok=True)
    os.makedirs('uploads/bukti_pembayaran', exist_ok=True)
    os.makedirs('uploads/ktp', exist_ok=True)

    # Static routes
    @app.route('/uploads/<filename>')
    def uploaded_files(filename):
        return send_from_directory('uploads', filename)

    @app.route('/uploads/produk/<filename>')
    def produk_image(filename):
        base_path = os.path.abspath(os.path.join(app.root_path, ".."))
        folder_path = os.path.join(base_path, 'uploads', 'produk')
        return send_from_directory(folder_path, filename)

    # Root route
    @app.route('/')
    def home():
        return {
            "message": "Server Flask SIMBOK aktif!",
            "status": "running",
            "environment": config_name,
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

    @app.route('/health')
    def health():
        return {"status": "healthy", "environment": config_name}, 200

    return app