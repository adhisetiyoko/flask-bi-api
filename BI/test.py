import requests
import os

API_KEY = "1c5157ab0c57a0a7ece4d6aa68064f04da5b9ab2ca0e54e868501f69cd70c258"

BASE_URL = "https://api.binderbyte.com/wilayah"


def get_provinsi():
    url = f"{BASE_URL}/provinsi?api_key={API_KEY}"
    return requests.get(url).json()["value"]


def get_kabupaten(id_prov):
    url = f"{BASE_URL}/kabupaten?api_key={API_KEY}&id_provinsi={id_prov}"
    return requests.get(url).json()["value"]


def get_kecamatan(id_kab):
    url = f"{BASE_URL}/kecamatan?api_key={API_KEY}&id_kabupaten={id_kab}"
    return requests.get(url).json()["value"]


def get_kelurahan(id_kec):
    url = f"{BASE_URL}/kelurahan?api_key={API_KEY}&id_kecamatan={id_kec}"
    return requests.get(url).json()["value"]


def clear():
    os.system("cls" if os.name == "nt" else "clear")


# ============================
# MAIN PROGRAM
# ============================

while True:
    clear()
    print("=== DAFTAR PROVINSI ===")
    provinsi = get_provinsi()

    for i, p in enumerate(provinsi, start=1):
        print(f"{i}. {p['id']} - {p['name']}")

    pilih = input("\nPilih nomor provinsi (0 untuk keluar): ")

    if pilih == "0":
        break

    if not pilih.isdigit() or not (1 <= int(pilih) <= len(provinsi)):
        input("Pilihan salah. Enter untuk lanjut...")
        continue

    prov = provinsi[int(pilih) - 1]

    # ============================
    # Kabupaten
    # ============================
    clear()
    print(f"=== KABUPATEN DI PROVINSI {prov['name']} ===")
    kabupaten = get_kabupaten(prov["id"])

    for i, k in enumerate(kabupaten, start=1):
        print(f"{i}. {k['id']} - {k['name']}")

    pilih_kab = input("\nPilih nomor kabupaten (enter untuk balik): ")
    if not pilih_kab.isdigit() or not (1 <= int(pilih_kab) <= len(kabupaten)):
        continue

    kab = kabupaten[int(pilih_kab) - 1]

    # ============================
    # Kecamatan
    # ============================
    clear()
    print(f"=== KECAMATAN DI {kab['name']} ===")
    kecamatan = get_kecamatan(kab["id"])

    for i, k in enumerate(kecamatan, start=1):
        print(f"{i}. {k['id']} - {k['name']}")

    pilih_kec = input("\nPilih nomor kecamatan (enter untuk balik): ")
    if not pilih_kec.isdigit() or not (1 <= int(pilih_kec) <= len(kecamatan)):
        continue

    kec = kecamatan[int(pilih_kec) - 1]

    # ============================
    # Kelurahan
    # ============================
    clear()
    print(f"=== KELURAHAN DI {kec['name']} ===")
    kelurahan = get_kelurahan(kec["id"])

    for i, kel in enumerate(kelurahan, start=1):
        print(f"{i}. {kel['id']} - {kel['name']}")

    input("\nTekan Enter untuk kembali...")
