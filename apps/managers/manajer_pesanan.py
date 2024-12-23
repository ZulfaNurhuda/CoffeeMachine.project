from typing import Dict, List, Optional

from apps.managers.manajer_menu import ManajerMenu
from apps.database.manajer_database import ManajerDatabase

from apps.data_classes import DataKopi, DataKomposisi, ItemPesanan

from apps.utils.utils_input import input_dengan_timeout

class ManajerPesanan:
    """
    Mengelola proses pemesanan kopi oleh pengguna.
    Mengecek stok kopi dan bahan tambahan sebelum mengkonfirmasi pesanan.
    """

    def __init__(
        self,
        manajer_db: ManajerDatabase,
        daftar_kopi: Dict[str, DataKopi],
        manajer_menu: ManajerMenu,
        daftar_tambahan: Dict[str, int],
    ):
        """
        Inisialisasi ManajerPesanan.

        Args:
            manajer_db (ManajerDatabase): Objek ManajerDatabase untuk berinteraksi dengan database.
            daftar_kopi (Dict[str, DataKopi]): Dictionary yang memetakan nama kopi ke objek DataKopi.
            manajer_menu (ManajerMenu): Objek ManajerMenu untuk mengelola tampilan menu.
            daftar_tambahan (Dict[str, int]): Dictionary yang memetakan nama bahan tambahan ke sisa stok.
        """
        self.manajer_db = manajer_db
        self.daftar_kopi = daftar_kopi
        self.manajer_menu = manajer_menu
        self.daftar_tambahan = daftar_tambahan

    def pilih_suhu(self, nama_kopi: str) -> Optional[str]:
        """
        Memilih suhu kopi.
        1 = Hangat, 2 = Dingin.

        Args:
            nama_kopi (str): Nama kopi yang dipilih.

        Returns:
            Optional[str]: 'hangat' atau 'dingin', None jika batal.
        """
        while True:
            suhu_input = input_dengan_timeout(
                self.manajer_db,
                f"🌡 - Tentukan suhu untuk {nama_kopi}? (1. Hangat | 2. Dingin | 'x' untuk batal): ",
            )
            if suhu_input.lower() == "x":
                print("❌ - Membatalkan pemilihan suhu.")
                return None
            elif suhu_input == "1":
                return "hangat"
            elif suhu_input == "2":
                return "dingin"
            else:
                print("⚠ - Input tidak valid. Silakan masukkan '1' atau '2'.")

    def atur_jumlah(self, tipe_bahan: str) -> Optional[int]:
        """
        Mengatur jumlah takaran bahan tambahan (0-5).

        Args:
            tipe_bahan (str): Tipe bahan tambahan yang akan diatur jumlahnya.

        Returns:
            Optional[int]: Jumlah takaran bahan tambahan, None jika batal.
        """
        while True:
            # Menampilkan stok bahan tambahan sebelum meminta input
            stok_tersedia = self.daftar_tambahan.get(tipe_bahan, 0)
            print(f"📦 - Stok {tipe_bahan}: {stok_tersedia} takaran")

            jumlah_input = input_dengan_timeout(
                self.manajer_db,
                f"> 🎨 - Atur kadar {tipe_bahan} (0-5 takaran | 'x' untuk batal): ",
            )
            if jumlah_input.lower() == "x":
                print("❌ - Membatalkan pengaturan komposisi.")
                return None
            try:
                jumlah = int(jumlah_input)
                if 0 <= jumlah <= 5:
                    # Validasi apakah jumlah yang dipilih tidak melebihi stok
                    if jumlah > stok_tersedia:
                        print(
                            f"⚠ - Jumlah takaran {tipe_bahan} melebihi stok yang tersedia ({stok_tersedia})."
                        )
                        continue
                    return jumlah
                else:
                    print("⚠ - Jumlah harus antara 0 hingga 5.")
            except ValueError:
                print("⚠ - Input tidak valid. Masukkan angka.")

    def pilih_komposisi(self) -> Optional[DataKomposisi]:
        """
        Memilih komposisi gula, krimer, susu, cokelat.

        Returns:
            Optional[DataKomposisi]: Objek DataKomposisi yang berisi komposisi bahan tambahan, None jika batal.
        """
        gula = self.atur_jumlah("Gula")
        if gula is None:
            return None
        krimer = self.atur_jumlah("Krimer")
        if krimer is None:
            return None
        susu = self.atur_jumlah("Susu")
        if susu is None:
            return None
        cokelat = self.atur_jumlah("Cokelat")
        if cokelat is None:
            return None
        return DataKomposisi(gula, krimer, susu, cokelat)

    def pesan_jumlah(self) -> Optional[int]:
        """
        Menentukan jumlah kopi yang dipesan.

        Returns:
            Optional[int]: Jumlah kopi yang dipesan (> 0), None jika batal.
        """
        while True:
            jumlah_input = input_dengan_timeout(
                self.manajer_db,
                "Pesan berapa kopi dengan komposisi ini? ('x' untuk batal): ",
            )
            if jumlah_input.lower() == "x":
                print("❌ - Membatalkan pemesanan.\n")
                return None
            try:
                jumlah = int(jumlah_input)
                if jumlah > 0:
                    return jumlah
                else:
                    print("⚠ - Jumlah kopi harus lebih dari 0.")
            except ValueError:
                print("⚠ - Input tidak valid. Masukkan angka.")

    def komposisi_sama(self, komp1: DataKomposisi, komp2: DataKomposisi) -> bool:
        """
        Membandingkan dua komposisi bahan tambahan.

        Args:
            komp1 (DataKomposisi): Komposisi pertama.
            komp2 (DataKomposisi): Komposisi kedua.

        Returns:
            bool: True jika kedua komposisi sama, False jika berbeda.
        """
        return komp1 == komp2

    def tambah_pesanan(
        self,
        data_pesanan: List[ItemPesanan],
        kopi: DataKopi,
        suhu: str,
        komposisi: DataKomposisi,
        jumlah: int,
    ) -> List[ItemPesanan]:
        """
        Menambah item pesanan ke dalam daftar pesanan.
        Jika item dengan komposisi sama sudah ada, jumlahnya akan ditambahkan.

        Args:
            data_pesanan (List[ItemPesanan]): Daftar pesanan saat ini.
            kopi (DataKopi): Objek DataKopi yang dipesan.
            suhu (str): Suhu kopi yang dipesan.
            komposisi (DataKomposisi): Komposisi bahan tambahan yang dipesan.
            jumlah (int): Jumlah kopi yang dipesan.

        Returns:
            List[ItemPesanan]: Daftar pesanan yang sudah diperbarui.
        """
        existing = next(
            (
                item
                for item in data_pesanan
                if item.kopi.nama == kopi.nama
                and item.suhu == suhu
                and self.komposisi_sama(item.komposisi, komposisi)
            ),
            None,
        )
        if existing:
            existing.jumlah += jumlah
        else:
            data_pesanan.append(ItemPesanan(kopi, jumlah, suhu, komposisi))
        return data_pesanan

    def ringkasan_pesanan(self, pesanan: List[ItemPesanan]) -> int:
        """
        Menampilkan ringkasan pesanan dan menghitung total harga.

        Args:
            pesanan (List[ItemPesanan]): Daftar pesanan.

        Returns:
            int: Total harga pesanan.
        """
        print("========== Ringkasan Pesanan ==========")
        total_harga = 0
        for idx, item in enumerate(pesanan, 1):
            harga_kopi = item.kopi.harga * item.jumlah
            total_harga += harga_kopi
            print(
                f"{idx}. {item.kopi.nama} ({item.suhu}) x{item.jumlah} - Rp{harga_kopi}"
            )
            print(
                f"   Gula: {item.komposisi.gula} takaran, "
                f"Krimer: {item.komposisi.krimer} takaran, "
                f"Susu: {item.komposisi.susu} takaran, "
                f"Cokelat: {item.komposisi.cokelat} takaran"
            )
        print(f">>> Total Harga: Rp{total_harga}")
        print("=======================================")
        return total_harga

    def cek_stok_tambahan(self, komposisi: DataKomposisi, jumlah: int) -> bool:
        """
        Mengecek ketersediaan bahan tambahan.

        Args:
            komposisi (DataKomposisi): Komposisi bahan tambahan yang diinginkan.
            jumlah (int): Jumlah kopi yang dipesan.

        Returns:
            bool: True jika stok bahan tambahan cukup, False jika tidak.
        """
        butuh_gula = komposisi.gula * jumlah
        butuh_krimer = komposisi.krimer * jumlah
        butuh_susu = komposisi.susu * jumlah
        butuh_cokelat = komposisi.cokelat * jumlah

        if self.daftar_tambahan.get("Gula", 0) < butuh_gula:
            print(
                f"☕ - Stok Gula tidak mencukupi. Tersisa {self.daftar_tambahan.get('Gula', 0)}."
            )
            return False
        if self.daftar_tambahan.get("Krimer", 0) < butuh_krimer:
            print(
                f"☕ - Stok Krimer tidak mencukupi. Tersisa {self.daftar_tambahan.get('Krimer', 0)}."
            )
            return False
        if self.daftar_tambahan.get("Susu", 0) < butuh_susu:
            print(
                f"☕ - Stok Susu tidak mencukupi. Tersisa {self.daftar_tambahan.get('Susu', 0)}."
            )
            return False
        if self.daftar_tambahan.get("Cokelat", 0) < butuh_cokelat:
            print(
                f"☕ - Stok Cokelat tidak mencukupi. Tersisa {self.daftar_tambahan.get('Cokelat', 0)}."
            )
            return False

        return True

    def pilih_kopi(self) -> List[ItemPesanan]:
        """
        Menangani proses pemilihan kopi oleh pengguna.

        Returns:
            List[ItemPesanan]: Daftar pesanan, atau list kosong jika batal.
        """
        kopi_nama_by_nomor = {
            kopi.nomor: kopi for kopi in self.daftar_kopi.values() if kopi.sisa > 0
        }
        data_pesanan: List[ItemPesanan] = []
        pesanan_ke = 1
        while True:
            print(f"\n*********** Pesanan ke-{pesanan_ke}: Pilih Kopi ************")
            self.manajer_menu.tampilkan_menu_kopi()
            pilihan = input_dengan_timeout(
                self.manajer_db, "Pilih nomor kopi ('x' untuk batal): "
            )
            if pilihan.lower() == "x":
                print("❌ - Membatalkan proses pemesanan.\n")
                if (len(data_pesanan) > 0):
                    for item in data_pesanan:
                        self.daftar_kopi[item.kopi.nama].sisa += item.jumlah
                        self.daftar_tambahan["Gula"] += item.komposisi.gula * item.jumlah
                        self.daftar_tambahan["Krimer"] += item.komposisi.krimer * item.jumlah
                        self.daftar_tambahan["Susu"] += item.komposisi.susu * item.jumlah
                        self.daftar_tambahan["Cokelat"] += item.komposisi.cokelat * item.jumlah
                data_pesanan = []
                break
            elif pilihan.isdigit():
                pilihan_int = int(pilihan)
                if pilihan_int in kopi_nama_by_nomor:
                    kopi = kopi_nama_by_nomor[pilihan_int]
                    print(f"\nAnda memilih {kopi.nama}".upper())
                    suhu = self.pilih_suhu(kopi.nama)
                    if suhu is None:
                        continue
                    komposisi = self.pilih_komposisi()
                    if komposisi is None:
                        continue
                    jumlah = self.pesan_jumlah()
                    if jumlah is None:
                        continue

                    # Cek stok kopi
                    if kopi.sisa < jumlah:
                        print(
                            f"☕ - Stok {kopi.nama} tidak mencukupi. Tersisa {kopi.sisa}."
                        )
                        print(
                            "🔃 - Silakan ulangi pemesanan dengan jumlah yang tersedia.\n"
                        )
                        continue

                    # Cek stok tambahan
                    if not self.cek_stok_tambahan(komposisi, jumlah):
                        print(
                            "🔃 - Silakan ulangi pemesanan dengan komposisi yang tersedia.\n"
                        )
                        continue

                    # Jika stok cukup, masukkan ke data pesanan
                    data_pesanan = self.tambah_pesanan(
                        data_pesanan, kopi, suhu, komposisi, jumlah
                    )

                    print("\nApakah Anda ingin memesan kopi lagi?")
                    lagi = input_dengan_timeout(
                        self.manajer_db, "Ketik 'y' untuk Ya atau 'n' untuk Tidak: "
                    ).lower()

                    if lagi in ["n", "no", "tidak", "gak"]:
                        print("\nMelanjutkan ke proses pembayaran...")
                        break
                    else:
                        pesanan_ke += 1
            
                    # Update stok kopi setelah semua pesanan dikonfirmasi
                    for item in data_pesanan:
                        self.daftar_kopi[item.kopi.nama].sisa -= item.jumlah
                        self.daftar_tambahan["Gula"] -= item.komposisi.gula * item.jumlah
                        self.daftar_tambahan["Krimer"] -= item.komposisi.krimer * item.jumlah
                        self.daftar_tambahan["Susu"] -= item.komposisi.susu * item.jumlah
                        self.daftar_tambahan["Cokelat"] -= item.komposisi.cokelat * item.jumlah
                else:
                    print("⚠ - Pilihan tidak tersedia. Silakan pilih lagi.")
            else:
                print("⚠ - Input tidak valid. Silakan masukkan angka atau 'x'.")
        return data_pesanan
