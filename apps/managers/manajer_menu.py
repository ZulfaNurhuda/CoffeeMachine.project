from typing import Dict

from apps.data_classes import DataKopi

class ManajerMenu:
    """
    Mengelola tampilan dan pemilihan menu kopi.
    Menampilkan kopi dengan stok > 0 serta memberikan tanda kopi terlaris.
    """

    def __init__(self, daftar_kopi: Dict[str, DataKopi], nama_kopi_terlaris: str = ""):
        """
        Inisialisasi ManajerMenu.

        Args:
            daftar_kopi (Dict[str, DataKopi]): Dictionary yang memetakan nama kopi ke objek DataKopi.
            nama_kopi_terlaris (str): Nama kopi terlaris (default: "").
        """
        self.daftar_kopi = daftar_kopi
        self.nama_kopi_terlaris = nama_kopi_terlaris

    def tetapkan_nomor_kopi(self) -> None:
        """
        Memberikan nomor urut pada setiap kopi yang memiliki stok > 0.
        """
        nomor = 1
        for kopi in self.daftar_kopi.values():
            if kopi.sisa > 0:
                kopi.nomor = nomor
                nomor += 1

    def tampilkan_menu_kopi(self) -> None:
        """
        Menampilkan menu kopi yang tersedia.
        Jika kopi termasuk kopi terlaris, tambahkan simbol ★.
        """
        print("================ Menu Kopi =================")
        for kopi in self.daftar_kopi.values():
            if kopi.sisa > 0:
                bintang = " ★" if kopi.nama == self.nama_kopi_terlaris else ""
                print(
                    f"{kopi.nomor}. {kopi.nama}{bintang} - Rp{kopi.harga} - Persediaan: {kopi.sisa}"
                )
        print("=============================================")
