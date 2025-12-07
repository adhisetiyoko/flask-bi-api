# file: BI/data_preprocessing.py

import pandas as pd
from datetime import datetime
from sklearn.preprocessing import LabelEncoder
import numpy as np

# Inisialisasi Encoders Global
# Encoders ini HARUS dilatih di model_trainer.py dan kemudian dimuat
# kembali saat preprocessing dan prediksi.
# Untuk sementara, kita definisikan fungsi untuk membuatnya.
le_komoditas = LabelEncoder()
le_provinsi = LabelEncoder()
le_kabupaten = LabelEncoder()


def create_encoders(df_raw):
    """
    Melatih LabelEncoder dari data historis yang lengkap.
    Fungsi ini HANYA dipanggil saat model pertama kali dilatih (di model_trainer.py).
    """
    global le_komoditas, le_provinsi, le_kabupaten
    
    # Pastikan kolom ada
    df_clean = df_raw.dropna(subset=['komoditas', 'provinsi', 'kabupaten'])
    
    # Latih encoders
    le_komoditas.fit(df_clean['komoditas'].astype(str))
    le_provinsi.fit(df_clean['provinsi'].astype(str))
    le_kabupaten.fit(df_clean['kabupaten'].astype(str))
    
    # Kembalikan objek encoder
    return le_komoditas, le_provinsi, le_kabupaten


def apply_preprocessing(df_raw, le_komoditas, le_provinsi, le_kabupaten):
    """
    Menerapkan semua langkah preprocessing dan feature engineering pada DataFrame.
    
    Args:
        df_raw (pd.DataFrame): DataFrame mentah (historis atau 1 baris input prediksi).
        le_komoditas, le_provinsi, le_kabupaten: Objek LabelEncoder yang sudah dilatih.
        
    Returns:
        pd.DataFrame: DataFrame yang sudah bersih dan memiliki semua feature.
    """
    
    df_clean = df_raw.copy()
    
    # 1. Cleaning dan Konversi
    df_clean = df_clean.dropna(subset=['harga'])
    df_clean['tanggal_dt'] = pd.to_datetime(df_clean['tanggal_parsed'])
    df_clean = df_clean.sort_values(['komoditas', 'provinsi', 'tanggal_dt'])
    
    # Mengisi nilai yang hilang untuk harga nasional dan std_dev jika ada
    if 'harga_nasional' in df_clean.columns:
        df_clean['harga_nasional'] = df_clean['harga_nasional'].fillna(df_clean['harga'])
    if 'std_dev' in df_clean.columns:
        df_clean['std_dev'] = df_clean['std_dev'].fillna(0)
    
    # 2. Pembuatan Feature Tanggal
    df_clean['year'] = df_clean['tanggal_dt'].dt.year
    df_clean['month'] = df_clean['tanggal_dt'].dt.month
    df_clean['day'] = df_clean['tanggal_dt'].dt.day
    df_clean['day_of_week'] = df_clean['tanggal_dt'].dt.dayofweek
    df_clean['day_of_year'] = df_clean['tanggal_dt'].dt.dayofyear

    # 3. Encoding Kategorikal
    
    # Fungsi transform perlu penanganan error (handle_unknown='ignore'
    # hanya tersedia di OneHotEncoder/OrdinalEncoder, di LabelEncoder harus dicek)
    
    def safe_transform(le, series):
        """Transformasi yang menangani nilai baru/tidak dikenal saat prediksi."""
        return series.apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
        
    df_clean['komoditas_encoded'] = safe_transform(le_komoditas, df_clean['komoditas'].astype(str))
    df_clean['provinsi_encoded'] = safe_transform(le_provinsi, df_clean['provinsi'].astype(str))
    df_clean['kabupaten_encoded'] = safe_transform(le_kabupaten, df_clean['kabupaten'].astype(str))

    # 4. Pembuatan Feature Time Series (Moving Average & Lag Features)
    
    # Fitur ini sensitif terhadap urutan data dan grouping.
    # Untuk prediksi 1 baris (real-time), Anda harus menyediakan data historis
    # yang cukup (misal 30 hari terakhir) di baris sebelum data target.
    
    # Moving average 7 hari
    df_clean['harga_ma7'] = df_clean.groupby(['komoditas', 'provinsi'])['harga'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )

    # Moving average 30 hari
    df_clean['harga_ma30'] = df_clean.groupby(['komoditas', 'provinsi'])['harga'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )

    # Lag features (harga kemarin dan 7 hari lalu)
    df_clean['harga_lag1'] = df_clean.groupby(['komoditas', 'provinsi'])['harga'].shift(1)
    df_clean['harga_lag7'] = df_clean.groupby(['komoditas', 'provinsi'])['harga'].shift(7)
    
    return df_clean.dropna()

def create_prediction_input(komoditas, provinsi, kabupaten, target_date, df_historis_terbaru, le_data):
    """
    Fungsi khusus untuk membuat input 1 baris untuk prediksi real-time.
    Ini menggantikan kebutuhan untuk memanggil apply_preprocessing pada seluruh dataset.
    
    Args:
        komoditas (str), provinsi (str), kabupaten (str): Input lokasi.
        target_date (datetime): Tanggal yang ingin diprediksi.
        df_historis_terbaru (pd.DataFrame): 30 hari data historis terakhir.
        le_data (dict): Dictionary berisi semua encoders yang dimuat dari model.
        
    Returns:
        pd.DataFrame: Satu baris input siap untuk model.
    """
    
    # Gabungkan data historis terbaru dengan baris target prediksi (harga diisi NaN)
    latest_data = df_historis_terbaru[
        (df_historis_terbaru['komoditas'] == komoditas) &
        (df_historis_terbaru['provinsi'] == provinsi) &
        (df_historis_terbaru['kabupaten'] == kabupaten)
    ].sort_values('tanggal_dt')
    
    # 1. Siapkan baris data target (besok)
    target_row = pd.DataFrame([{
        'tanggal_parsed': target_date.strftime('%Y-%m-%d'),
        'tanggal_dt': target_date,
        'komoditas': komoditas,
        'provinsi': provinsi,
        'kabupaten': kabupaten,
        'harga': np.nan, # Harga yang akan diprediksi
        'harga_nasional': latest_data['harga_nasional'].iloc[-1] if 'harga_nasional' in latest_data.columns else np.nan,
        'std_dev': latest_data['std_dev'].iloc[-1] if 'std_dev' in latest_data.columns else 0
    }])
    
    # 2. Gabungkan untuk menghitung MA dan Lag
    df_temp = pd.concat([latest_data, target_row], ignore_index=True)
    
    # 3. Terapkan Preprocessing
    df_features = apply_preprocessing(
        df_temp, 
        le_data['le_komoditas'], 
        le_data['le_provinsi'], 
        le_data['le_kabupaten']
    )
    
    # 4. Ambil baris terakhir (baris prediksi)
    X_pred = df_features.iloc[-1].to_frame().T
    
    # 5. Filter kolom yang sesuai dengan feature_columns model
    return X_pred[le_data['feature_columns']]