"""
# ╒==================================================╕
# |          SIMULASI MESIN KOPI VIRTUAL!            |
# ╘==================================================╛

╭----------------╮
| LATAR BELAKANG |
╰----------------╯
Di era digital sekarang ini, computational thinking (atau berpikir komputasional) menjadi 
kemampuan penting yang perlu dimiliki mahasiswa. Kemampuan ini meliputi cara memecahkan masalah, 
merancang langkah-langkah sistematis, dan menyederhanakan proses yang kompleks.

Salah satu cara untuk menerapkan prinsip berpikir komputasional dalam kehidupan sehari-hari 
adalah dengan membuat simulasi algoritma coffee machine. Coffee machine memiliki proses yang
terstruktur, seperti memilih jenis kopi, menentukan komposisi, jumlah pesanan, dan menangani
pembayaran secara otomatis.

╭---------------------------╮
| FITUR-FITUR DALAM PROGRAM |
╰---------------------------╯
Berbagai fitur yang tersedia didalam algoritma coffee machine ini antara lain, sebagai berikut
1.  Terhubung dengan Google Spreadsheet sebagai basis data,
2.  Dapat menangani banyak pesanan sekaligus dari pengguna,
3.	Menu yang dapat dikustomisasi sesuai data yang tersedia,
4.	Dapat memilih suhu kopi yang diinginkan,
5.	Dapat memilih sendiri komposisi dari bahan tambahan (mencakup gula, susu, krimer, dan cokelat),
6.	Mendukung dua metode pembayaran, yaitu secara tunai dan QRIS (simulasi),
7.	Dapat membuat simulasi, ketika pengguna telah memesan kopi daring, 
    pengguna hanya tinggal menunjukkan kode QR untuk konfirmasi,
8.	Pencatatan pesanan yang detail dan akurat,
9.	Error handling yang tertata rapi,
10.	Informasi untuk user di setiap langkah cukup jelas,
11.	Terdapat validasi untuk setiap masukan pengguna,
12.	Terdapat menu khusus admin yang diamankan dengan kode admin, menu admin mencakup shutdown program 
    dan restock jenis kopi.

╭-----------------------------╮
| AUTHOR / PENYUSUN ALGORITMA |
╰-----------------------------╯
Seluruh anggota kelompok 13, kelas 31, mata kuliah Berpikir Komputasional ITB 2024, yaitu
1. Laurenisus Dani Rendragraha      (19624272)
2. Mineva Azzahra                   (19624227)
3. Muhammad Faiz Alfada Dharma	    (19624244)
4. Muhammad Zulfa Fauzan Nurhuda	(19624258)
"""

# ╒====================================╕
# |          IMPORT LIBRARY            |
# ╘====================================╛
import sys
import os
import random
import string

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from functools import lru_cache

# Library tambahan (pihak ketiga)
import gspread
from google.oauth2.service_account import Credentials
from inputimeout import inputimeout, TimeoutOccurred
import cv2
import qrcode_terminal


# ╒====================================╕
# |            KONFIGURASI             |
# ╘====================================╛
class Config:
    """Kelas konfigurasi untuk menyimpan pengaturan program."""

    SHEET_ID = "google_sheet_id"
    SERVICE_ACCOUNT_FILE = os.path.join(
        os.getcwd(),
        "path_to_key_file",
        "key_file.json",
    )
    KODE_ADMIN = 1234567890
    TIMEOUT_DURATION = 60  # Durasi timeout input dalam detik


# ╒====================================╕
# |            DATA CLASS              |
# ╘====================================╛
@dataclass
class KopiData:
    """Kelas untuk menyimpan data kopi."""

    nama: str
    harga: int
    sisa: int
    row_number: int
    nomor: int = 0


@dataclass
class Komposisi:
    """Kelas untuk menyimpan komposisi bahan tambahan."""

    gula: int
    krimer: int
    susu: int
    cokelat: int


@dataclass
class PesananItem:
    """Kelas untuk menyimpan item pesanan."""

    kopi: KopiData
    jumlah: int
    suhu: str
    komposisi: Komposisi


# ╒====================================╕
# |       MANAJEMEN BASIS DATA         |
# ╘====================================╛
class DatabaseManager:
    """Kelas untuk mengelola operasi database dengan Google Sheets."""

    def __init__(self):
        """Inisialisasi koneksi ke Google Sheets."""
        kredensial = Credentials.from_service_account_file(
            Config.SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        client = gspread.authorize(kredensial)
        lembar_kerja = client.open_by_key(Config.SHEET_ID)
        self.persediaan = lembar_kerja.worksheet("PersediaanKopi")
        self.penjualan = lembar_kerja.worksheet("DataPenjualan")
        self.antrian_qr = lembar_kerja.worksheet("AntrianPesananQR")

    def get_column_indices(self, worksheet: gspread.Worksheet) -> Dict[str, int]:
        """Mendapatkan mapping nama kolom ke indeks kolom."""
        header = worksheet.row_values(1)
        return {name: idx + 1 for idx, name in enumerate(header)}

    @lru_cache(maxsize=None)
    def ambil_data_kopi(self) -> Dict[str, KopiData]:
        """Mengambil data kopi dari lembar `PersediaanKopi`."""
        data_kopi = self.persediaan.get_all_records()
        return {
            baris["Jenis Kopi"]: KopiData(
                nama=baris["Jenis Kopi"],
                harga=int(baris["Harga"]),
                sisa=int(baris["Sisa Persediaan"]),
                row_number=i + 2,
            )
            for i, baris in enumerate(data_kopi)
        }

    def update_stok(self, kopi: KopiData, jumlah_terjual: int) -> None:
        """Mengupdate stok kopi di lembar `PersediaanKopi`."""
        stok_baru = max(0, kopi.sisa - jumlah_terjual)
        self.persediaan.update_cell(kopi.row_number, 3, stok_baru)
        kopi.sisa = stok_baru

    def catat_penjualan(
        self, item_pesanan: PesananItem, metode_pembayaran: str
    ) -> None:
        """Mencatat penjualan ke lembar `DataPenjualan`."""
        komposisi_all = (
            f"Gula ({item_pesanan.komposisi.gula} takaran), "
            f"Susu ({item_pesanan.komposisi.susu} takaran), "
            f"Krimer ({item_pesanan.komposisi.krimer} takaran), "
            f"Cokelat ({item_pesanan.komposisi.cokelat} takaran)"
        )
        self.penjualan.append_row(
            [
                item_pesanan.kopi.nama,
                item_pesanan.suhu.capitalize(),
                komposisi_all,
                f"x{item_pesanan.jumlah}",
                item_pesanan.kopi.harga * item_pesanan.jumlah,
                metode_pembayaran,
            ]
        )

    def restock_kopi(self, kopi: KopiData, jumlah_restock: int) -> None:
        """Melakukan restock kopi di lembar `PersediaanKopi`."""
        stok_baru = kopi.sisa + jumlah_restock
        self.persediaan.update_cell(kopi.row_number, 3, stok_baru)
        kopi.sisa = stok_baru


# ╒====================================╕
# |          UTILITAS INPUT            |
# ╘====================================╛
def input_dengan_timeout(teks: str, batas_waktu: int = Config.TIMEOUT_DURATION) -> str:
    """Fungsi untuk mengambil input dari pengguna dengan batas waktu."""
    try:
        return inputimeout(prompt=teks, timeout=batas_waktu)
    except TimeoutOccurred:
        print(
            "\n⏳ - Waktu habis! Tidak ada aktivitas selama 1 menit. Mesin kopi otomatis berhenti.\n\n"
        )
        mesin_kopi = MesinKopi()
        mesin_kopi.coffee_machine_simulasi()


# ╒====================================╕
# |          MANAJEMEN MENU            |
# ╘====================================╛
class MenuManager:
    """Kelas untuk mengelola tampilan dan pemilihan menu kopi."""

    def __init__(self, daftar_kopi: Dict[str, KopiData]):
        self.daftar_kopi = daftar_kopi

    def assign_kopi_numbers(self) -> None:
        """Memberikan nomor pada setiap kopi yang tersedia."""
        nomor = 1
        for kopi in self.daftar_kopi.values():
            if kopi.sisa > 0:
                kopi.nomor = nomor
                nomor += 1

    def tampilkan_menu_kopi(self) -> None:
        """Menampilkan menu kopi yang tersedia."""
        print("================ Menu Kopi =================")
        for kopi in self.daftar_kopi.values():
            if kopi.sisa > 0:
                print(
                    f"{kopi.nomor}. {kopi.nama} - Rp{kopi.harga} - Persediaan: {kopi.sisa}"
                )
        print("=============================================")


# ╒====================================╕
# |         MANAJEMEN PESANAN          |
# ╘====================================╛
class PesananManager:
    """Kelas untuk mengelola proses pemesanan kopi."""

    def __init__(self, daftar_kopi: Dict[str, KopiData], menu_manager: MenuManager):
        self.daftar_kopi = daftar_kopi
        self.menu_manager = menu_manager

    def pilih_suhu(self, nama_kopi: str) -> Optional[str]:
        """Memilih suhu kopi (hangat atau dingin)."""
        while True:
            suhu_input = input_dengan_timeout(
                f"🌡 - Tentukan suhu untuk {nama_kopi}? (1. Hangat | 2. Dingin | 'x' untuk batal): "
            )
            if suhu_input.lower() == "x":
                print("❌ - Membatalkan pemilihan suhu.")
                return None
            elif suhu_input == "1":
                return "hangat"
            elif suhu_input == "2":
                return "dingin"
            else:
                print(
                    "⚠ - Input tidak valid. Silakan masukkan '1' untuk hangat atau '2' untuk dingin."
                )

    def atur_jumlah(self, tipe_bahan: str) -> Optional[int]:
        """Mengatur jumlah komposisi bahan tambahan (0-5 takaran)."""
        while True:
            jumlah_input = input_dengan_timeout(
                f"> 🎨 - Atur kadar {tipe_bahan} (0-5 takaran | 'x' untuk batal): "
            )
            if jumlah_input.lower() == "x":
                print("❌ - Membatalkan pengaturan komposisi.")
                return None
            try:
                jumlah = int(jumlah_input)
                if 0 <= jumlah <= 5:
                    return jumlah
                else:
                    print("⚠ - Jumlah harus antara 0 hingga 5.")
            except ValueError:
                print("⚠ - Input tidak valid. Silakan masukkan angka.")

    def pilih_komposisi(self) -> Optional[Komposisi]:
        """Memilih komposisi bahan tambahan."""
        gula = self.atur_jumlah("gula")
        if gula is None:
            return None
        krimer = self.atur_jumlah("krimer")
        if krimer is None:
            return None
        susu = self.atur_jumlah("susu")
        if susu is None:
            return None
        cokelat = self.atur_jumlah("cokelat")
        if cokelat is None:
            return None
        return Komposisi(gula, krimer, susu, cokelat)

    def pesan_jumlah(self) -> Optional[int]:
        """Menentukan jumlah kopi yang akan dipesan."""
        while True:
            jumlah_input = input_dengan_timeout(
                "Pesan berapa kopi dengan komposisi ini? ('x' untuk batal): "
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
                print("⚠ - Input tidak valid. Silakan masukkan angka.")

    def komposisi_sama(self, komp1: Komposisi, komp2: Komposisi) -> bool:
        """Membandingkan dua komposisi bahan tambahan."""
        return komp1 == komp2

    def tambah_pesanan(
        self,
        data_pesanan: List[PesananItem],
        kopi: KopiData,
        suhu: str,
        komposisi: Komposisi,
        jumlah: int,
    ) -> List[PesananItem]:
        """Menambah atau menggabungkan pesanan ke dalam daftar pesanan."""
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
            data_pesanan.append(PesananItem(kopi, jumlah, suhu, komposisi))
        return data_pesanan

    def ringkasan_pesanan(self, pesanan: List[PesananItem]) -> int:
        """Menampilkan ringkasan pesanan dan menghitung total harga."""
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

    def pilih_kopi(self) -> List[PesananItem]:
        """Menangani proses pemilihan kopi oleh pengguna."""
        kopi_nama_by_nomor = {
            kopi.nomor: kopi for kopi in self.daftar_kopi.values() if kopi.sisa > 0
        }
        data_pesanan: List[PesananItem] = []
        pesanan_ke = 1
        while True:
            print(f"\n\n*********** Pesanan ke-{pesanan_ke}: Pilih Kopi ************")
            self.menu_manager.tampilkan_menu_kopi()
            pilihan = input_dengan_timeout("Pilih nomor kopi ('x' untuk batal): ")
            if pilihan.lower() == "x":
                print("❌ - Membatalkan proses pemesanan.\n")
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
                    data_pesanan = self.tambah_pesanan(
                        data_pesanan, kopi, suhu, komposisi, jumlah
                    )
                    print("\nApakah Anda ingin memesan kopi lagi?")
                    lagi = input_dengan_timeout(
                        "Ketik 'y' untuk Ya atau 'n' untuk Tidak: "
                    ).lower()
                    if lagi in ["n", "no", "tidak", "gak"]:
                        print("\nMelanjutkan ke proses pembayaran...")
                        break
                    else:
                        pesanan_ke += 1
                else:
                    print("⚠ - Pilihan tidak tersedia. Silakan pilih lagi.")
            else:
                print(
                    "⚠ - Input tidak valid. Silakan masukkan angka atau perintah yang benar."
                )
        return data_pesanan


# ╒====================================╕
# |        MANAJEMEN PEMBAYARAN        |
# ╘====================================╛
class PembayaranManager:
    """Kelas untuk mengelola proses pembayaran."""

    def tampilkan_metode_pembayaran(self) -> None:
        """Menampilkan metode pembayaran yang tersedia."""
        print("=== Metode Pembayaran Tersedia ===")
        print("1. Tunai")
        print("2. QRIS")
        print("===============================")

    def proses_pembayaran_tunai(self, total_harga: int) -> Tuple[bool, str]:
        """Menangani pembayaran tunai."""
        total_dibayar = 0
        while total_dibayar < total_harga:
            uang_input = input_dengan_timeout(
                f"Masukkan uang pembayaran ('x' untuk batal): Rp"
            )
            if uang_input.lower() == "x":
                print("❌ - Membatalkan pembayaran tunai.\n")
                return (False, "Tunai")
            try:
                uang = int(uang_input)
                if uang <= 0:
                    print(
                        "⚠ - Jumlah uang harus lebih besar dari Rp0. Silakan masukkan kembali."
                    )
                    continue
                total_dibayar += uang
                if total_dibayar >= total_harga:
                    kembalian = total_dibayar - total_harga
                    print(
                        f"\n✅ - Pembayaran berhasil. Kembalian Anda: Rp{kembalian}\n"
                    )
                    return (True, "Tunai")
                else:
                    kurang = total_harga - total_dibayar
                    print(
                        f"ℹ - Uang kurang. Anda masih kurang Rp{kurang}. Silakan masukkan kembali."
                    )
            except ValueError:
                print("⚠ - Input tidak valid. Silakan masukkan angka.")
        return (False, "Tunai")

    def generate_random_string(self, length: int = 10) -> str:
        """Menghasilkan string angka acak sepanjang 'length' karakter."""
        return "".join(random.choices(string.digits, k=length))

    def generate_qr_terminal(self, data: str) -> None:
        """Menampilkan QR Code di terminal."""
        qrcode_terminal.draw(data)

    def proses_pembayaran_qris(self, total_harga: int) -> Tuple[bool, str]:
        """Menangani pembayaran QRIS."""
        code_to_qr = self.generate_random_string()
        print("\n=== Scan QRIS di bawah ini untuk melakukan pembayaran ===")
        self.generate_qr_terminal(code_to_qr)
        print(
            "\nMasukkan kode konfirmasi yang Anda terima setelah melakukan pembayaran.\n"
        )
        attempts = 5
        for _ in range(1, attempts + 1):
            code_from_user = input_dengan_timeout(
                f"Masukkan kode konfirmasi ('x' untuk batal): "
            )
            if code_from_user.lower() == "x":
                print("❌ - Membatalkan pembayaran QRIS.\n")
                return (False, "QRIS")
            if code_to_qr == code_from_user:
                print("\n✅ - Pembayaran berhasil.\n")
                return (True, "QRIS")
            else:
                print("⚠ - Kode konfirmasi salah, silakan coba lagi.")
        print("⚠ - Kesempatan memasukkan kode telah habis.")
        return (False, "QRIS")

    def proses_pembayaran(self, total_harga: int) -> Tuple[bool, Optional[str]]:
        """Menangani proses pembayaran."""
        print("\n\n*********** Pilih Metode Pembayaran ************")
        self.tampilkan_metode_pembayaran()
        print(f">>> Total yang harus dibayar: Rp{total_harga}")
        while True:
            metode_pembayaran_input = input_dengan_timeout(
                "Pilih metode pembayaran ( 1 | 2 | 'x' untuk batal): "
            )
            if metode_pembayaran_input.lower() == "x":
                print("❌ - Membatalkan proses pembayaran.\n")
                return (False, None)
            try:
                metode_pembayaran = int(metode_pembayaran_input)
                if metode_pembayaran == 1:
                    return self.proses_pembayaran_tunai(total_harga)
                elif metode_pembayaran == 2:
                    return self.proses_pembayaran_qris(total_harga)
                else:
                    print(
                        "⚠ - Metode pembayaran tidak tersedia. Silakan pilih 1 atau 2."
                    )
            except ValueError:
                print("⚠ - Input tidak valid. Silakan masukkan angka.")


# ╒====================================╕
# |       MANAJEMEN PINDAI QR          |
# ╘====================================╛
class ScanQR:
    """Kelas untuk mengelola proses pemindaian QR Code."""

    def __init__(self, db_manager: DatabaseManager, pesanan_manager: PesananManager):
        self.db_manager = db_manager
        self.pesanan_manager = pesanan_manager
        self.daftar_kopi = pesanan_manager.daftar_kopi
        self.menu_manager = pesanan_manager.menu_manager

    def scan_qr(self) -> None:
        """Fungsi untuk memindai QR dan mengonfirmasi pesanan dengan status `Pending`."""
        detector = cv2.QRCodeDetector()
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("\n⚠ - Tidak dapat membuka pemindai QR.\n\n")
            return
        print("\n\n*********** Pindai QR Code ************")
        print("Dekatkan QR Code ke alat pemindai QR")

        qr_code = ""
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("⚠ - Tidak dapat membaca frame dari pemindai QR.\n\n")
                    break
                data, _, _ = detector.detectAndDecode(frame)
                if data:
                    qr_code = data
                    break
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("❌ - Pemindaian QR Code dibatalkan.\n\n")
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()
        if not qr_code:
            print("⚠ - Tidak ada QR Code yang dipindai.\n\n")
            return

        data_qr = self.db_manager.antrian_qr.get_all_records()
        antrian_qr_columns = self.db_manager.get_column_indices(
            self.db_manager.antrian_qr
        )
        persediaan_columns = self.db_manager.get_column_indices(
            self.db_manager.persediaan
        )
        self.daftar_kopi = self.db_manager.ambil_data_kopi()
        self.menu_manager.assign_kopi_numbers()

        pesanan = []
        habis = False
        valid = False
        for index, baris in enumerate(data_qr, start=2):
            if str(baris["QR"]) == qr_code and baris["Status"] == "Pending":
                kopi_nama = baris["Jenis kopi"]
                jumlah_dipesan = int(baris["Jumlah"])
                if kopi_nama not in self.daftar_kopi:
                    print(f"ℹ - Maaf, {kopi_nama} tidak tersedia di mesin ini")
                    continue
                kopi = self.daftar_kopi[kopi_nama]
                stok_saat_ini = kopi.sisa
                if stok_saat_ini <= 0:
                    habis = True
                    print(f"ℹ - Stok {kopi_nama} habis, silahkan coba di mesin lain")
                    continue
                if stok_saat_ini < jumlah_dipesan:
                    print(
                        f"ℹ - Stok {kopi_nama} tidak mencukupi. Tersisa {stok_saat_ini} cup."
                    )
                    jumlah_dapat_diproses = stok_saat_ini
                else:
                    jumlah_dapat_diproses = jumlah_dipesan

                komposisi = Komposisi(
                    gula=int(baris.get("Gula", 0)),
                    krimer=int(baris.get("Krimer", 0)),
                    susu=int(baris.get("Susu", 0)),
                    cokelat=int(baris.get("Cokelat", 0)),
                )
                suhu = baris["Suhu"].lower()

                # Menambah pesanan ke daftar
                self.pesanan_manager.tambah_pesanan(
                    pesanan, kopi, suhu, komposisi, jumlah_dapat_diproses
                )

                # Memperbarui status pesanan di Google Sheets
                if jumlah_dapat_diproses == jumlah_dipesan:
                    self.db_manager.antrian_qr.update_cell(
                        index, antrian_qr_columns["Status"], "Selesai"
                    )
                    self.db_manager.antrian_qr.update_cell(
                        index, antrian_qr_columns["Jumlah"], 0
                    )
                else:
                    sisa_pesanan = jumlah_dipesan - jumlah_dapat_diproses
                    self.db_manager.antrian_qr.update_cell(
                        index, antrian_qr_columns["Jumlah"], sisa_pesanan
                    )

                stok_baru = kopi.sisa - jumlah_dapat_diproses
                self.db_manager.persediaan.update_cell(
                    kopi.row_number, persediaan_columns["Sisa Persediaan"], stok_baru
                )
                kopi.sisa = stok_baru

            elif str(baris["QR"]) == qr_code and baris["Status"] == "Selesai":
                valid = True

        if pesanan:
            print(" ")
            self.pesanan_manager.ringkasan_pesanan(pesanan)
            print("\n☕ - Terima kasih! Silakan ambil kopi Anda.\n\n")
            for item in pesanan:
                self.db_manager.catat_penjualan(item, "Pembelian Daring Website")
        else:
            if not habis:
                if valid:
                    print("ℹ - Semua pesanan dengan QR ini sudah selesai.\n\n")
                else:
                    print("⚠ - QR yang diberikan tidak valid.\n\n")


# ╒====================================╕
# |      MANAJEMEN RESTOCK KOPI        |
# ╘====================================╛
class RestockKopi:
    """Kelas untuk mengelola proses restock kopi."""

    def __init__(self, db_manager: DatabaseManager, menu_manager: MenuManager):
        self.db_manager = db_manager
        self.menu_manager = menu_manager
        self.daftar_kopi = menu_manager.daftar_kopi

    def restock_kopi(self) -> None:
        """Fitur khusus admin untuk restock kopi."""
        print("\n\n*********** Menu Restock Kopi ************")
        max_attempts = 5
        attempts = 0
        while attempts < max_attempts:
            kode_admin_input = input_dengan_timeout(
                "Masukkan kode admin ('x' untuk batal): "
            )
            if kode_admin_input.lower() == "x":
                print("❌ - Membatalkan restock kopi.\n\n")
                return
            try:
                kode_admin = int(kode_admin_input)
            except ValueError:
                print("⚠ - Kode admin harus berupa angka.")
                attempts += 1
                continue
            if kode_admin == Config.KODE_ADMIN:
                while True:
                    self.menu_manager.assign_kopi_numbers()
                    self.menu_manager.tampilkan_menu_kopi()
                    kopi_nama_by_nomor = {
                        kopi.nomor: kopi
                        for kopi in self.daftar_kopi.values()
                        if kopi.sisa >= 0
                    }
                    # Loop untuk memilih kopi yang akan di restock
                    while True:
                        pilihan_kopi_input = input_dengan_timeout(
                            "Pilih kopi untuk restock ('x' untuk batal): "
                        )
                        if pilihan_kopi_input.lower() == "x":
                            print("❌ - Membatalkan restock kopi.\n\n")
                            return
                        if not pilihan_kopi_input.isdigit():
                            print(
                                "⚠ - Input tidak valid. Silakan masukkan nomor kopi atau 'x' untuk batal."
                            )
                            continue
                        pilihan_kopi = int(pilihan_kopi_input)
                        if pilihan_kopi not in kopi_nama_by_nomor:
                            print(
                                "⚠ - Pilihan kopi tidak valid. Silakan pilih nomor yang tersedia."
                            )
                            continue
                        kopi = kopi_nama_by_nomor[pilihan_kopi]
                        break  # Keluar dari loop setelah memilih kopi yang valid

                    # Loop untuk memasukkan jumlah restock
                    while True:
                        jumlah_restock_input = input_dengan_timeout(
                            "Masukkan jumlah restock ('x' untuk batal): "
                        )
                        if jumlah_restock_input.lower() == "x":
                            print("❌ - Membatalkan restock kopi.\n\n")
                            return
                        try:
                            jumlah_restock = int(jumlah_restock_input)
                            if jumlah_restock <= 0:
                                print("⚠ - Jumlah restock harus lebih dari 0.")
                                continue
                            self.db_manager.restock_kopi(kopi, jumlah_restock)
                            print(
                                f"✅ - Berhasil restock {kopi.nama} sebanyak {jumlah_restock}. Stok baru: {kopi.sisa}.\n\n"
                            )
                            break  # Keluar dari loop setelah sukses restock
                        except ValueError:
                            print("⚠ - Masukkan harus berupa angka.")

                    # Pertanyaan apakah ingin melakukan restock lagi
                    while True:
                        lagi_input = input_dengan_timeout(
                            "\nApakah ingin melakukan restock lagi? ('y' untuk Ya | 'n' untuk Tidak): "
                        ).lower()
                        if lagi_input in ["y", "ya"]:
                            break  # Kembali ke awal loop restock
                        elif lagi_input in ["n", "tidak"]:
                            print("\n🔃 - Kembali ke menu utama.\n\n")
                            return
                        else:
                            print(
                                "⚠ - Input tidak valid. Silakan masukkan 'y' atau 'n'."
                            )
                    return
            else:
                attempts += 1
                print("⚠ - Kode admin salah! Coba lagi.")
        print("⚠ - Autentikasi administrator gagal.")


# ╒====================================╕
# |   MAIN: COFFEE MACHINE HANDLER     |
# ╘====================================╛
class MesinKopi:
    """Kelas utama untuk mengontrol operasi mesin kopi."""

    def __init__(self):
        """Inisialisasi mesin kopi dan memuat data awal."""
        self.db_manager = DatabaseManager()
        self.daftar_kopi: Dict[str, KopiData] = self.db_manager.ambil_data_kopi()
        self.menu_manager = MenuManager(self.daftar_kopi)
        self.pesanan_manager = PesananManager(self.daftar_kopi, self.menu_manager)
        self.pembayaran_manager = PembayaranManager()
        self.scan_qr_manager = ScanQR(self.db_manager, self.pesanan_manager)
        self.restock_manager = RestockKopi(self.db_manager, self.menu_manager)
        self.menu_manager.assign_kopi_numbers()

    def shutdown_program(self):
        """Fungsi untuk mematikan program setelah otentikasi admin dengan maksimal 5 percobaan."""
        print("\n\n*********** Menonaktifkan Program ************")
        max_attempts = 5
        attempts = 0
        while attempts < max_attempts:
            kode_admin_input = input_dengan_timeout(
                "Masukkan kode admin ('x' untuk batal): "
            )
            if kode_admin_input.lower() == "x":
                print("❌ - Membatalkan penonaktifan program.\n\n")
                return
            try:
                kode_admin = int(kode_admin_input)
            except ValueError:
                print("⚠ - Kode admin harus berupa angka.")
                attempts += 1
                continue

            if kode_admin == Config.KODE_ADMIN:
                print("💤 - Algoritma dimatikan. Program akan keluar.")
                sys.exit(0)
            else:
                attempts += 1
                print(
                    f"⚠ - Kode admin salah! {max_attempts - attempts} percobaan tersisa."
                )
        print("⚠ - Autentikasi administrator gagal. Kembali ke menu utama.")

    def coffee_machine_simulasi(self) -> None:
        """Fungsi utama yang menangani seluruh proses Mesin Kopi Virtual."""
        print("\n=== Selamat datang di Mesin Kopi Virtual! ===\n")
        while True:
            print("======= Pilihan Menu =======")
            print("1. Mulai Pemesanan")
            print("2. Scan QR")
            print("3. Restock Kopi (Admin)")
            print("4. Shutdown Program (Admin)")
            print("============================")
            pilihan = input("Pilih opsi (1, 2, 3, 4): ")
            if pilihan == "1":
                if not self.daftar_kopi:
                    print(
                        "\n💔 - Maaf, semua kopi telah habis. Silakan kembali lain waktu.\n\n"
                    )
                    continue
                pesanan = self.pesanan_manager.pilih_kopi()
                if pesanan:
                    stok_cukup = True
                    for item in pesanan:
                        if item.kopi.sisa < item.jumlah:
                            print(
                                f"☕ - Stok {item.kopi.nama} tidak mencukupi. Tersisa {item.kopi.sisa}."
                            )
                            stok_cukup = False
                    if not stok_cukup:
                        print(
                            "🔃 - Silakan ulangi pemesanan dengan jumlah yang tersedia.\n\n"
                        )
                        continue
                    print(" \n ")
                    total_harga = self.pesanan_manager.ringkasan_pesanan(pesanan, 2)
                    (
                        pembayaran_sukses,
                        metode,
                    ) = self.pembayaran_manager.proses_pembayaran(total_harga)
                    if pembayaran_sukses:
                        print("☕ - Terima kasih! Silakan ambil kopi Anda.\n\n")
                        for item in pesanan:
                            self.db_manager.catat_penjualan(item, metode)
                            self.db_manager.update_stok(item.kopi, item.jumlah)
                        self.daftar_kopi = self.db_manager.ambil_data_kopi()
                        self.menu_manager.assign_kopi_numbers()
                    else:
                        if metode is None:
                            print(
                                "💰 - Pembayaran dibatalkan. Kembali ke menu utama.\n\n"
                            )
                        else:
                            print("📉 - Pembayaran gagal. Kembali ke menu utama.\n\n")
                else:
                    print(
                        "📃 - Pemesanan dibatalkan atau tidak ada pesanan. Kembali ke menu utama.\n\n"
                    )
            elif pilihan == "2":
                self.scan_qr_manager.scan_qr()
            elif pilihan == "3":
                self.restock_manager.restock_kopi()
                self.daftar_kopi = self.db_manager.ambil_data_kopi()
                self.menu_manager.assign_kopi_numbers()
            elif pilihan == "4":
                self.shutdown_program()
            else:
                print("⚠ - Pilihan tidak valid. Silakan pilih 1, 2, 3, atau 4")


# ╒====================================╕
# |         JALANKAN PROGRAM           |
# ╘====================================╛
if __name__ == "__main__":
    mesin_kopi = MesinKopi()
    mesin_kopi.coffee_machine_simulasi()
