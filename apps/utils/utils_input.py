from inputimeout import inputimeout, TimeoutOccurred
from credentials.config import Konfigurasi
from apps.database.manajer_database import ManajerDatabase

def input_dengan_timeout(manajer_db: ManajerDatabase, teks: str, batas_waktu: int = Konfigurasi.DURASI_TIMEOUT) -> str:
    """
    Mengambil input dari pengguna dengan batas waktu.

    Args:
        teks (str): Teks yang akan ditampilkan sebagai prompt input.
        batas_waktu (int): Batas waktu dalam detik (default: Konfigurasi.DURASI_TIMEOUT).

    Returns:
        str: Input dari pengguna atau 'timeout' jika waktu habis.
    """
    try:
        return inputimeout(prompt=teks, timeout=batas_waktu)
    except TimeoutOccurred:
        print(
            "\n⏳ - Waktu habis! Tidak ada aktivitas selama 1 menit. Kembali ke menu utama!.\n"
        )
        from apps.coffee_machine.mesin_kopi import MesinKopi
        MesinKopi(manajer_db).simulasi()
