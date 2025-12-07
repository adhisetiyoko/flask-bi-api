# file: model_trainer.py (Akan di-deploy sebagai Cloud Function)

import functions_framework
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error
from datetime import datetime

# --- Load Data dari Cloud Storage/Database ---
def load_data_from_storage():
    """Ganti ini dengan logika mengambil semua data historis terbaru."""
    # Contoh: df = pd.read_sql("SELECT * FROM prices", db_conn)
    # ATAU: df = pd.read_csv("gcs://bucket-anda/data_historis.csv")
    
    # Placeholder: Asumsi Anda punya CSV lokal di GCF environment
    try:
        df = pd.read_csv("data_historis.csv") 
        return df
    except FileNotFoundError:
        raise Exception("Data historis tidak ditemukan di storage.")

# --- Bagian pelatihan model dari kode Anda ---
def train_and_save_model(df_raw):
    # Logika preprocessing dan feature engineering dari kode Anda...
    # (Misal: df_clean = preprocessing_pipeline(df_raw))
    
    # [Anda perlu menyertakan semua langkah preprocessing dan training dari kode Anda di sini]
    
    # Contoh sederhana:
    df_clean = df_raw.dropna(subset=['harga'])
    le_komoditas = LabelEncoder().fit(df_clean['komoditas'])
    
    X = pd.DataFrame({
        'komoditas_encoded': le_komoditas.transform(df_clean['komoditas']),
        'year': pd.to_datetime(df_clean['tanggal_parsed']).dt.year
        # ... tambahkan semua features Anda
    })
    y = df_clean['harga']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # === Save Model ke Cloud Storage ===
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_filename = f"model_harga_pangan_{timestamp}.pkl"
    
    joblib.dump({
        'model': model,
        'le_komoditas': le_komoditas,
        # ... simpan semua encoders dan features
    }, model_filename)
    
    # LOGIKA BARU: Unggah file .pkl ke Cloud Storage (GCS)
    # storage_client = storage.Client()
    # bucket = storage_client.bucket('bucket-model-anda')
    # blob = bucket.blob(model_filename)
    # blob.upload_from_filename(model_filename)
    
    print(f"✅ Model baru disimpan ke storage: {model_filename}")
    
@functions_framework.http
def weekly_model_trainer(request):
    """Fungsi utama yang dipicu oleh Cloud Scheduler mingguan."""
    print("--- Mulai Pelatihan Model Mingguan ---")
    try:
        df = load_data_from_storage()
        train_and_save_model(df)
        return 'Model Retraining Successful!', 200
    except Exception as e:
        print(f"❌ GAGAL PELATIHAN MODEL: {e}")
        return 'Model Retraining Failed!', 500

# requirements.txt untuk file ini:
# functions-framework
# pandas
# scikit-learn
# joblib
# # Tambahkan library storage (misal: google-cloud-storage)