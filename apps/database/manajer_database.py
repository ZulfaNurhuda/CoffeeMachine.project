from typing import Dict, List

import threading 
import time  
import queue
import os

import gspread
from google.oauth2.service_account import Credentials

from apps.data_classes import DataKopi, DataRefID, CatatanPenjualan

from credentials.config import Konfigurasi

class ManajerDatabase:
    """
    Mengelola koneksi dan sinkronisasi data dengan Google Sheets.
    Melakukan caching lokal dan update ke Sheets secara periodik.
    """

    def __init__(self):
        """
        Inisialisasi ManajerDatabase.
        Mengatur koneksi ke Google Sheets, memuat data awal, dan memulai thread sinkronisasi.
        """
        # Mengatur kredensial dan otorisasi ke Google Sheets
        kredensial = Credentials.from_service_account_file(
            Konfigurasi.FILE_AKUN_LAYANAN,
            scopes=["https://www.googleapis.com/auth/spreadsheets"],
        )
        klien = gspread.authorize(kredensial)
        lembar_kerja = klien.open_by_key(Konfigurasi.ID_SHEET)

        # Worksheet yang digunakan
        self.worksheet_persediaan = lembar_kerja.worksheet("PersediaanKopi")
        self.worksheet_tambahan = lembar_kerja.worksheet("PersediaanTambahan")
        self.worksheet_qr = lembar_kerja.worksheet("ReferenceID")
        self.worksheet_penjualan = lembar_kerja.worksheet("DataPenjualan")
        self.worksheet_pesanan_online = lembar_kerja.worksheet("AntrianPesananQR")

        # Inisialisasi lock, queue, dan data lokal
        self.kunci = threading.Lock()
        self.antrian_update = queue.Queue()

        # Muat data awal
        self.daftar_kopi = self.muat_data_kopi()
        self.daftar_tambahan = self.muat_data_tambahan()
        self.daftar_qr = self.muat_daftar_qr()

        # Kode admin diambil dari file atau default
        self.kode_admin = self.muat_kode_admin()

        # Jalankan thread sinkronisasi periodik
        self.thread_sinkronisasi = threading.Thread(
            target=self.sinkronisasi_periodik, daemon=True
        )
        self.thread_sinkronisasi.start()

    def dapatkan_indeks_kolom(self, worksheet: gspread.Worksheet) -> Dict[str, int]:
        """Mendapatkan mapping nama kolom ke indeks kolom."""
        header = worksheet.row_values(1)
        return {nama: idx + 1 for idx, nama in enumerate(header)}

    def muat_kode_admin(self) -> int:
        """
        Memuat kode admin dari file admin_code.txt jika ada,
        jika tidak ada, gunakan kode default dan buat file tersebut.

        Returns:
            int: Kode admin.
        """
        file_admin = os.path.join(os.getcwd(), "credentials", "admin_code.txt")
        if os.path.exists(file_admin):
            with open(file_admin, "r") as f:
                kode = f.read().strip()
                try:
                    return int(kode)
                except ValueError:
                    # Jika file rusak, pakai default
                    return Konfigurasi.KODE_ADMIN_DEFAULT
        else:
            with open(file_admin, "w") as f:
                f.write(str(Konfigurasi.KODE_ADMIN_DEFAULT))
            return Konfigurasi.KODE_ADMIN_DEFAULT

    def simpan_kode_admin(self, kode_baru: int) -> None:
        """
        Menyimpan kode admin baru ke dalam admin_code.txt secara permanen.

        Args:
            kode_baru (int): Kode admin baru.
        """
        file_admin = os.path.join(os.getcwd(), "credentials", "admin_code.txt")
        with open(file_admin, "w") as f:
            f.write(str(kode_baru))
        self.kode_admin = kode_baru

    def muat_data_kopi(self) -> Dict[str, DataKopi]:
        """
        Memuat data kopi dari worksheet 'PersediaanKopi' ke cache lokal.

        Returns:
            Dict[str, DataKopi]: Dictionary dengan nama kopi sebagai kunci dan objek DataKopi sebagai nilai.
        """
        data_kopi = self.worksheet_persediaan.get_all_records()
        with self.kunci:
            return {
                baris["Jenis Kopi"]: DataKopi(
                    nama=baris["Jenis Kopi"],
                    harga=int(baris["Harga"]),
                    sisa=int(baris["Sisa Persediaan"]),
                    nomor_baris=i + 2,  # Header di baris 1
                )
                for i, baris in enumerate(data_kopi)
            }

    def muat_data_tambahan(self) -> Dict[str, int]:
        """
        Memuat data bahan tambahan dari worksheet 'PersediaanTambahan'.

        Returns:
            Dict[str, int]: Dictionary dengan nama bahan sebagai kunci dan sisa stok sebagai nilai.
        """
        data_tambahan = self.worksheet_tambahan.get_all_records()
        with self.kunci:
            return {
                baris["Jenis Bahan Tambahan"]: int(baris["Sisa Persediaan"])
                for baris in data_tambahan
            }

    def muat_daftar_qr(self) -> List[DataRefID]:
        """
        Memuat data QR dari worksheet 'ReferenceID' ke cache lokal.

        Returns:
            List[DataRefID]: Daftar objek DataRefID.
        """
        records = self.worksheet_qr.get_all_records()
        with self.kunci:
            daftar_qr = []
            for i, record in enumerate(records):
                daftar_qr.append(
                    DataRefID(
                        ref_id=record["Reference ID"],
                        total_harga=int(record["Total Harga"]),
                        metode_pembayaran=record["Metode"],
                        timestamp=record["Timestamp"],
                        status=record["Status"],
                        nomor_baris=i + 2,
                    )
                )
            return daftar_qr

    def dapatkan_kopi_terlaris(self) -> str:
        """
        Menghitung kopi yang paling banyak terjual dari 'DataPenjualan'.

        Returns:
            str: Nama kopi dengan penjualan terbanyak, atau string kosong jika tidak ada penjualan.
        """
        data_penjualan = self.worksheet_penjualan.get_all_records()
        hitungan = {}
        for baris in data_penjualan:
            nama = baris["Data Pesanan"]
            if nama not in hitungan:
                hitungan[nama] = 0
            # Jumlah terjual ada di kolom 'Jumlah' dengan format 'x{angka}'
            jumlah_str = baris["Jumlah"].replace("x", "")
            try:
                jumlah_int = int(jumlah_str)
            except ValueError:
                jumlah_int = 0
            hitungan[nama] += jumlah_int
        if not hitungan:
            return ""
        # Cari kopi dengan penjualan terbanyak
        kopi_terlaris = max(hitungan, key=hitungan.get)
        return kopi_terlaris

    def sinkronisasi_periodik(self) -> None:
        """
        Sinkronisasi data periodik ke Google Sheets.
        Memproses antrian update secara batch dan kemudian mengupdate stok ke Sheets.
        """
        while True:
            try:
                # Proses semua operasi dalam antrian
                while not self.antrian_update.empty():
                    operasi = self.antrian_update.get_nowait()
                    tipe_operasi = operasi[0]
                    if tipe_operasi == "update_stok":
                        _, nama_kopi, jumlah_terjual = operasi
                        self.update_stok(nama_kopi, jumlah_terjual)
                    elif tipe_operasi == "restock_kopi":
                        _, nama_kopi, jumlah_restock = operasi
                        self.restock_kopi(nama_kopi, jumlah_restock)
                    elif tipe_operasi == "update_status_qr":
                        _, ref_id, status_baru = operasi
                        self.update_status_qr(ref_id, status_baru)
                    elif tipe_operasi == "catat_penjualan":
                        _, catatan_penjualan = operasi
                        self.catat_penjualan(catatan_penjualan)
                    elif tipe_operasi == "update_tambahan":
                        _, bahan, jumlah = operasi
                        self.update_tambahan(bahan, jumlah)

                # Sinkronisasi data kopi
                with self.kunci:
                    for kopi in self.daftar_kopi.values():
                        self.worksheet_persediaan.update_cell(
                            kopi.nomor_baris, 3, kopi.sisa
                        )

                # Sinkronisasi data bahan tambahan
                data_tambahan = self.worksheet_tambahan.get_all_records()
                peta_baris_bahan = {
                    baris["Jenis Bahan Tambahan"]: idx + 2
                    for idx, baris in enumerate(data_tambahan)
                }
                for bahan, sisa in self.daftar_tambahan.items():
                    nomor_baris = peta_baris_bahan.get(bahan)
                    if nomor_baris:
                        self.worksheet_tambahan.update_cell(nomor_baris, 2, sisa)

                # Sinkronisasi data QR
                for qr in self.daftar_qr:
                    self.worksheet_qr.update_cell(qr.nomor_baris, 5, qr.status)

                time.sleep(Konfigurasi.INTERVAL_SINKRONISASI)

            except Exception as e:
                print(f"⚠ - Terjadi kesalahan saat sinkronisasi periodik:\n{e}")
                time.sleep(Konfigurasi.INTERVAL_SINKRONISASI)

    def enqueue_update_stok(self, nama_kopi: str, jumlah_terjual: int) -> None:
        """
        Menambahkan operasi update stok kopi ke dalam antrian.

        Args:
            nama_kopi (str): Nama kopi yang akan diupdate stoknya.
            jumlah_terjual (int): Jumlah kopi yang terjual.
        """
        self.antrian_update.put(("update_stok", nama_kopi, jumlah_terjual))

    def enqueue_restock_kopi(self, nama_kopi: str, jumlah_restock: int) -> None:
        """
        Menambahkan operasi restock kopi ke dalam antrian.

        Args:
            nama_kopi (str): Nama kopi yang akan direstock.
            jumlah_restock (int): Jumlah kopi yang akan ditambahkan ke stok.
        """
        self.antrian_update.put(("restock_kopi", nama_kopi, jumlah_restock))

    def enqueue_update_status_qr(self, ref_id: str, status_baru: str) -> None:
        """
        Menambahkan operasi update status QR ke dalam antrian.

        Args:
            ref_id (str): Reference ID dari QR yang akan diupdate statusnya.
            status_baru (str): Status baru untuk QR.
        """
        self.antrian_update.put(("update_status_qr", ref_id, status_baru))

    def enqueue_catat_penjualan(self, catatan_penjualan: CatatanPenjualan) -> None:
        """
        Menambahkan operasi pencatatan penjualan ke dalam antrian.

        Args:
            catatan_penjualan (CatatanPenjualan): Objek CatatanPenjualan yang berisi data penjualan.
        """
        self.antrian_update.put(("catat_penjualan", catatan_penjualan))

    def enqueue_update_tambahan(self, bahan: str, jumlah: int) -> None:
        """
        Menambahkan operasi update stok bahan tambahan ke dalam antrian.

        Args:
            bahan (str): Nama bahan tambahan yang akan diupdate stoknya.
            jumlah (int): Jumlah bahan tambahan yang akan ditambahkan/dikurangi dari stok.
                        Nilai negatif untuk pengurangan stok.
        """
        self.antrian_update.put(("update_tambahan", bahan, jumlah))

    def update_stok(self, nama_kopi: str, jumlah_terjual: int) -> None:
        """
        Update stok kopi di cache lokal.

        Args:
            nama_kopi (str): Nama kopi yang akan diupdate stoknya.
            jumlah_terjual (int): Jumlah kopi yang terjual.
        """
        if nama_kopi in self.daftar_kopi:
            kopi = self.daftar_kopi[nama_kopi]
            kopi.sisa = max(0, kopi.sisa - jumlah_terjual)

    def restock_kopi(self, nama_kopi: str, jumlah_restock: int) -> None:
        """
        Restock kopi di cache lokal.

        Args:
            nama_kopi (str): Nama kopi yang akan direstock.
            jumlah_restock (int): Jumlah kopi yang akan ditambahkan ke stok.
        """
        if nama_kopi in self.daftar_kopi:
            kopi = self.daftar_kopi[nama_kopi]
            kopi.sisa += jumlah_restock

    def update_status_qr(self, ref_id: str, status_baru: str) -> None:
        """
        Update status QR Code di cache lokal.

        Args:
            ref_id (str): Reference ID dari QR yang akan diupdate statusnya.
            status_baru (str): Status baru untuk QR.
        """
        for qr in self.daftar_qr:
            if qr.ref_id == ref_id:
                qr.status = status_baru
                break

    def catat_penjualan(self, catatan_penjualan: CatatanPenjualan) -> None:
        """
        Mencatat penjualan ke worksheet 'DataPenjualan'.

        Args:
            catatan_penjualan (CatatanPenjualan): Objek CatatanPenjualan yang berisi data penjualan.
        """
        self.worksheet_penjualan.append_row(
            [
                catatan_penjualan.jenis_kopi,
                catatan_penjualan.suhu,
                catatan_penjualan.komposisi,
                catatan_penjualan.jumlah,
                catatan_penjualan.total_harga,
                catatan_penjualan.metode_pembayaran,
            ]
        )

    def update_tambahan(self, bahan: str, jumlah: int) -> None:
        """
        Update stok bahan tambahan di cache lokal.

        Args:
            bahan (str): Nama bahan tambahan yang akan diupdate stoknya.
            jumlah (int): Jumlah bahan tambahan yang akan ditambahkan/dikurangi dari stok.
                        Nilai negatif untuk pengurangan stok.
        """
        if bahan in self.daftar_tambahan:
            self.daftar_tambahan[bahan] = max(0, self.daftar_tambahan[bahan] + jumlah)

    def simpan_perubahan_sebelum_keluar(self) -> None:
        """
        Memaksa sinkronisasi terakhir sebelum program dimatikan.
        Dengan cara mengosongkan antrian bila ada.
        """
        try:
            while not self.antrian_update.empty():
                operasi = self.antrian_update.get_nowait()
                tipe_operasi = operasi[0]
                if tipe_operasi == "update_stok":
                    _, nama_kopi, jumlah_terjual = operasi
                    self.update_stok(nama_kopi, jumlah_terjual)
                elif tipe_operasi == "restock_kopi":
                    _, nama_kopi, jumlah_restock = operasi
                    self.restock_kopi(nama_kopi, jumlah_restock)
                elif tipe_operasi == "update_status_qr":
                    _, ref_id, status_baru = operasi
                    self.update_status_qr(ref_id, status_baru)
                elif tipe_operasi == "catat_penjualan":
                    _, catatan_penjualan = operasi
                    self.catat_penjualan(catatan_penjualan)
                elif tipe_operasi == "update_tambahan":
                    _, bahan, jumlah = operasi
                    self.update_tambahan(bahan, jumlah)

            # Update sheets kopi
            with self.kunci:
                for kopi in self.daftar_kopi.values():
                    self.worksheet_persediaan.update_cell(
                        kopi.nomor_baris, 3, kopi.sisa
                    )

            # Update sheets tambahan
            data_tambahan = self.worksheet_tambahan.get_all_records()
            peta_baris_bahan = {
                baris["Jenis Bahan Tambahan"]: idx + 2
                for idx, baris in enumerate(data_tambahan)
            }
            for bahan, sisa in self.daftar_tambahan.items():
                nomor_baris = peta_baris_bahan.get(bahan)
                if nomor_baris:
                    self.worksheet_tambahan.update_cell(nomor_baris, 2, sisa)

            # Sinkronisasi data QR
            for qr in self.daftar_qr:
                self.worksheet_qr.update_cell(qr.nomor_baris, 5, qr.status)

        except Exception as e:
            print(f"⚠ - Terjadi kesalahan saat menyimpan perubahan terakhir:\n{e}")
            time.sleep(Konfigurasi.INTERVAL_SINKRONISASI)

    def restock_kopi_sync(self, nama_kopi: str, jumlah_restock: int) -> None:
        """
        Restock kopi secara synchronous, mengupdate cache lokal dan Google Sheets langsung.

        Args:
            nama_kopi (str): Nama kopi yang akan direstock.
            jumlah_restock (int): Jumlah kopi yang akan ditambahkan ke stok.
        """
        with self.kunci:
            if nama_kopi in self.daftar_kopi:
                kopi = self.daftar_kopi[nama_kopi]
                kopi.sisa += jumlah_restock
                # Update Google Sheets
                self.worksheet_persediaan.update_cell(kopi.nomor_baris, 3, kopi.sisa)

    def restock_bahan_tambahan_sync(self, bahan: str, jumlah_restock: int) -> None:
        """
        Restock bahan tambahan secara synchronous, mengupdate cache lokal dan Google Sheets langsung.

        Args:
            bahan (str): Nama bahan tambahan yang akan direstock.
            jumlah_restock (int): Jumlah bahan tambahan yang akan ditambahkan ke stok.
        """
        with self.kunci:
            if bahan in self.daftar_tambahan:
                self.daftar_tambahan[bahan] += jumlah_restock
                # Update Google Sheets
                # Mendapatkan nomor baris bahan tambahan
                records = self.worksheet_tambahan.get_all_records()
                peta_baris_bahan = {
                    baris["Jenis Bahan Tambahan"]: idx + 2
                    for idx, baris in enumerate(records)
                }
                nomor_baris = peta_baris_bahan.get(bahan)
                if nomor_baris:
                    self.worksheet_tambahan.update_cell(
                        nomor_baris, 2, self.daftar_tambahan[bahan]
                    )
