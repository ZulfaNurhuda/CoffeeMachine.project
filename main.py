import sys # Modul untuk mengakses fungsi-fungsi yang terkait dengan interpreter Python

sys.path.append("./") # Menambahkan direktori utama ke path agar modul dapat diimpor
sys.dont_write_bytecode = True # Menghentikan pembuatan file .pyc

import time 
import socket 
import threading 

from apps.database.manajer_database import ManajerDatabase
from apps.coffee_machine.mesin_kopi import MesinKopi
from apps.webservice.app import AplikasiWeb
from credentials.config import Konfigurasi

def cek_webservice(host: str, port: int) -> bool:
    """
    Mengecek apakah webservice sudah berjalan.
    Mencoba terhubung ke host dan port tertentu.

    Args:
        host (str): Host webservice.
        port (int): Port webservice.

    Returns:
        bool: True jika webservice sudah berjalan, False jika tidak.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(10)
        try:
            s.connect((host, port))
            return True
        except (socket.timeout, socket.error):
            return False

def main():
    """
    Fungsi utama untuk menjalankan mesin kopi dan webservice secara bersamaan.
    """
    manajer_db = ManajerDatabase()

    host, check_host, port = "0.0.0.0", "127.0.0.1", Konfigurasi.PORT

    def jalankan_webservice():
        aplikasi_web = AplikasiWeb(manajer_db)
        aplikasi_web.run(host=host, port=port)

    t = threading.Thread(target=jalankan_webservice, daemon=True)
    t.start()

    webservice_berjalan = False
    while True:
        if cek_webservice(host=check_host, port=port):
            webservice_berjalan = True
            break
        else:
            time.sleep(3)

    if webservice_berjalan:
        mesin_kopi = MesinKopi(manajer_db)
        try:
            mesin_kopi.simulasi()
        except KeyboardInterrupt:
            print("\nCTRL+C ditekan. Menyimpan perubahan dan keluar...")
            manajer_db.simpan_perubahan_sebelum_keluar()
            sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
