# services/prediction_service.py

import joblib
# Import modul GCS untuk mengambil model .pkl
# from google.cloud import storage 

class PredictionService:
    def __init__(self):
        # 1. Saat server Flask jalan, muat model terbaru
        self.model, self.encoders = self._load_model_from_storage()
        print("✅ Model ML telah dimuat dan siap melayani prediksi.")

    def _load_model_from_storage(self):
        # LOGIKA INI MEMBUTUHKAN KONEKSI KE GCS DI LINGKUNGAN FLASK
        # Contoh: download file .pkl terbaru dari GCS
        # model_data = joblib.load('lokal_cache_model_terbaru.pkl')

        # --- Placeholder untuk demo ---
        try:
            # Asumsi model sudah didownload ke dalam folder app/models/
            model_data = joblib.load('app/models/model_harga_pangan_terbaru.pkl') 
            return model_data['model'], model_data
        except FileNotFoundError:
             raise Exception("Model file not found. Run model_trainer first!")

    def predict_price(self, komoditas_name, prov_name, target_date):
        # 2. Logika Prediksi
        # Menggunakan encoders (le_komoditas, dll.) dari self.encoders
        # Membuat feature (harga_ma7, harga_lag1, dll.)
        # X_pred = ... (buat DataFrame input)
        # prediction = self.model.predict(X_pred)[0]

        # --- Placeholder ---
        return 65000
    