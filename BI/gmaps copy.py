import googlemaps
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import os

# --- Konfigurasi Awal ---
app = Flask(__name__)

# Ganti dengan API Key Google Maps Anda yang sebenarnya
# API Key ini harus memiliki akses ke Distance Matrix API dan Places API
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "AIzaSyAqvr64aQeljD9lvukwnW9OipiRicXJ55I")
gmaps = googlemaps.Client(key=API_KEY)

# --- Logika Inti: Perhitungan Jarak dan Ongkir (Sama seperti sebelumnya) ---

def hitung_jarak_dan_waktu(asal, tujuan):
    """
    Mengambil data jarak dan waktu tempuh menggunakan Distance Matrix API.
    """
    try:
        result = gmaps.distance_matrix(
            origins=[asal],
            destinations=[tujuan],
            mode="driving",
            language="id"
        )

        if result['status'] == 'OK':
            element = result['rows'][0]['elements'][0]
            
            if element['status'] == 'OK':
                # Ekstraksi data
                jarak_meter = element['distance']['value']
                jarak_text = element['distance']['text']
                waktu_detik = element['duration']['value']
                waktu_text = element['duration']['text']

                return {
                    "status": "success",
                    "origin": asal,
                    "destination": tujuan,
                    "distance_meters": jarak_meter,
                    "distance_text": jarak_text,
                    "duration_seconds": waktu_detik,
                    "duration_text": waktu_text
                }
            else:
                return {
                    "status": "error",
                    "message": f"Gagal mendapatkan rute: {element['status']}",
                }
        else:
            return {
                "status": "error",
                "message": f"Gagal memanggil API: {result['status']}",
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Terjadi kesalahan saat memproses: {str(e)}",
        }

def hitung_ongkir_berdasarkan_jarak(jarak_meter, tarif_per_km=3000, tarif_dasar=5000):
    """
    Logika perhitungan ongkir sederhana. Ganti dengan aturan bisnis Anda.
    """
    jarak_km = jarak_meter / 1000
    ongkir = tarif_dasar + (jarak_km * tarif_per_km)
    return round(ongkir)

# --- Endpoint API untuk Perhitungan (Sama seperti sebelumnya) ---

@app.route('/api/check_ongkir', methods=['GET'])
def check_ongkir_api():
    """
    Endpoint backend untuk mengecek ongkir (mengembalikan JSON).
    """
    asal = request.args.get('asal')
    tujuan = request.args.get('tujuan')
    
    if not asal or not tujuan:
        return jsonify({
            "status": "error",
            "message": "Parameter 'asal' dan 'tujuan' wajib diisi."
        }), 400

    data_jarak = hitung_jarak_dan_waktu(asal, tujuan)
    
    if data_jarak['status'] != 'success':
        return jsonify(data_jarak), 500

    jarak_meter = data_jarak['distance_meters']
    ongkir_estimasi = hitung_ongkir_berdasarkan_jarak(jarak_meter)
    
    response_data = {
        "status": "success",
        "origin": data_jarak['origin'],
        "destination": data_jarak['destination'],
        "distance": {
            "meters": jarak_meter,
            "text": data_jarak['distance_text']
        },
        "duration": {
            "seconds": data_jarak['duration_seconds'],
            "text": data_jarak['duration_text']
        },
        "shipping_cost": {
            "amount_rp": ongkir_estimasi,
            "calculation_note": "Menggunakan tarif dasar Rp 5.000 + Rp 3.000/km (Tarif Asumsi)."
        }
    }
    
    return jsonify(response_data)

# --- Endpoint Frontend dengan Places Autocomplete ---

@app.route('/', methods=['GET'])
def index():
    """
    Endpoint untuk menampilkan halaman formulir input (HTML) yang sudah dilengkapi Places Autocomplete.
    """
    # Masukkan API_KEY ke dalam JavaScript
    global API_KEY
    
    html_content = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cek Estimasi Ongkir</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f4f7f6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
        h1 {{ color: #007bff; text-align: center; margin-bottom: 30px; }}
        form {{ display: grid; gap: 15px; }}
        label {{ font-weight: bold; margin-bottom: -5px; color: #555; }}
        input[type="text"] {{ width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
        button {{ padding: 12px 20px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; transition: background-color 0.3s; }}
        button:hover {{ background-color: #218838; }}
        #hasil {{ margin-top: 30px; padding: 20px; border: 1px solid #007bff; border-radius: 6px; background-color: #e6f7ff; }}
        .error {{ color: #dc3545; font-weight: bold; }}
        .success-text {{ color: #28a745; font-size: 1.2em; }}
        /* Gaya untuk saran Autocomplete Google Maps */
        .pac-container {{ z-index: 10000; }} 
    </style>
</head>
<body>
    <div class="container">
        <h1>📦 Kalkulator Ongkir Sederhana</h1>
        
        <form id="ongkirForm">
            <label for="asal">📍 Titik Asal:</label>
            <input type="text" id="asal" name="asal" placeholder="Mulai ketik alamat..." required>

            <label for="tujuan">🚩 Titik Tujuan:</label>
            <input type="text" id="tujuan" name="tujuan" placeholder="Mulai ketik alamat..." required>
            
            <button type="submit">Cek Estimasi Ongkir</button>
        </form>

        <div id="hasil">
            Masukkan alamat asal dan tujuan. Mulai ketik untuk melihat rekomendasi lokasi (Autocomplete).
        </div>
    </div>

    <script>
        const asalInput = document.getElementById('asal');
        const tujuanInput = document.getElementById('tujuan');
        const hasilDiv = document.getElementById('hasil');

        // --- Fungsi Inisialisasi Autocomplete ---
        function initAutocomplete() {{
            // Opsi untuk membatasi hasil ke Indonesia (opsional)
            const options = {{
                componentRestrictions: {{ country: "id" }},
                fields: ["formatted_address", "geometry"],
                types: ["geocode", "establishment"]
            }};

            const autocompleteAsal = new google.maps.places.Autocomplete(asalInput, options);
            const autocompleteTujuan = new google.maps.places.Autocomplete(tujuanInput, options);
        }}

        // --- Logika Pengiriman Form ---
        document.getElementById('ongkirForm').addEventListener('submit', function(e) {{
            e.preventDefault(); 
            
            const asal = asalInput.value;
            const tujuan = tujuanInput.value;
            hasilDiv.innerHTML = 'Memuat... Mohon Tunggu...';

            // Memanggil endpoint API Flask
            fetch(`/api/check_ongkir?asal=${{encodeURIComponent(asal)}}&tujuan=${{encodeURIComponent(tujuan)}}`)
                .then(response => response.json())
                .then(data => {{
                    if (data.status === 'success') {{
                        const ongkirFormatted = data.shipping_cost.amount_rp.toLocaleString('id-ID');
                        
                        hasilDiv.innerHTML = `
                            <h2>✅ Hasil Perhitungan</h2>
                            <p><strong>Asal:</strong> ${{data.origin}}</p>
                            <p><strong>Tujuan:</strong> ${{data.destination}}</p>
                            <hr>
                            <p><strong>Jarak Tempuh:</strong> ${{data.distance.text}}</p>
                            <p><strong>Estimasi Waktu:</strong> ${{data.duration.text}}</p>
                            <h3 class="success-text">💰 Estimasi Biaya Ongkir: Rp ${{ongkirFormatted}}</h3>
                            <small>(${{data.shipping_cost.calculation_note}})</small>
                        `;
                    }} else {{
                        hasilDiv.innerHTML = `<p class="error">❌ Error: ${{data.message}}</p>`;
                    }}
                }})
                .catch(error => {{
                    hasilDiv.innerHTML = `<p class="error">Terjadi kesalahan jaringan atau server: ${{error}}</p>`;
                }});
        }});
    </script>
    <script 
        src="https://maps.googleapis.com/maps/api/js?key={API_KEY}&libraries=places&callback=initAutocomplete" 
        async defer>
    </script>
</body>
</html>
    """
    return render_template_string(html_content)

if __name__ == '__main__':
    # Jalankan aplikasi Flask
    print("🚀 Aplikasi Web Cek Ongkir siap!")
    print("Akses di: http://127.0.0.1:5000/")
    app.run(debug=True)