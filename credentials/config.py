import os

class Konfigurasi:
    """Konfigurasi global untuk aplikasi mesin kopi."""

    # File kredensial akun layanan Google
    FILE_AKUN_LAYANAN = os.path.join(
        os.getcwd(),
        "credentials",
        "coffee-machine-ct24-ab01b40294eb.json",
    )

    # ID Google Sheets
    ID_SHEET = "1aIdU_E6X5ZI0xcS6caC1SfajpIycn97aed0or6YxxXM"

    # Kode admin default (jika admin_code.txt belum ada)
    KODE_ADMIN_DEFAULT = 1234567890

    # Port untuk webservice Flask
    PORT = 5000

    # Durasi timeout untuk input (dalam detik)
    DURASI_TIMEOUT = 60

    # Interval sinkronisasi periodik ke Google Sheets (dalam detik)
    INTERVAL_SINKRONISASI = 300  # 5 menit

    # Batas waktu pembayaran QRIS (dalam detik)
    QRIS_TIMEOUT = 300  # 5 menit
