from typing import Tuple, Optional

import socket
import time
import random
import string
from datetime import datetime

import qrcode
import qrcode.constants

from apps.database.manajer_database import ManajerDatabase

from apps.data_classes import DataRefID

from apps.utils.utils_input import input_dengan_timeout

from credentials.config import Konfigurasi

class ManajerPembayaran:
    """Kelas untuk mengelola proses pembayaran."""

    def __init__(self, manajer_db: ManajerDatabase):
        """
        Inisialisasi ManajerPembayaran dengan ManajerDatabase.

        Args:
            manajer_db (ManajerDatabase): Objek ManajerDatabase untuk berinteraksi dengan database.
        """
        self.manajer_db = manajer_db

    def tampilkan_metode_pembayaran(self) -> None:
        """
        Menampilkan metode pembayaran yang tersedia.
        """
        print("=== Metode Pembayaran Tersedia ===")
        print("1. Tunai")
        print("2. QRIS")
        print("==================================")

    def proses_pembayaran_tunai(self, total_harga: int) -> Tuple[bool, str]:
        """
        Menangani pembayaran tunai.

        Args:
            total_harga (int): Total harga yang harus dibayar.

        Returns:
            Tuple[bool, str]: Tuple yang berisi status pembayaran (bool) dan metode pembayaran (str).
        """
        total_dibayar = 0
        while total_dibayar < total_harga:
            uang_input = input_dengan_timeout(
                self.manajer_db, f"Masukkan uang pembayaran ('x' untuk batal): Rp"
            )
            if uang_input.lower() == "x":
                print("❌ - Membatalkan pembayaran tunai.\n")
                return False, "Tunai"
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
                    return True, "Tunai"
                else:
                    kurang = total_harga - total_dibayar
                    print(
                        f"ℹ - Uang kurang. Anda masih kurang Rp{kurang}. Silakan masukkan kembali."
                    )
            except ValueError:
                print("⚠ - Input tidak valid. Silakan masukkan angka.")
        return False, "Tunai"

    def generate_random_string(self, length: int = 10) -> str:
        """
        Menghasilkan string acak dengan panjang tertentu.

        Args:
            length (int): Panjang string yang diinginkan (default: 10).

        Returns:
            str: String acak dengan panjang yang ditentukan.
        """
        return "".join(random.choices(string.digits, k=length))

    def generate_qr(self, data: str) -> None:
        """
        Membuat QR code dan menampilkannya dalam format ASCII.

        Args:
            data (str): Data yang akan dikodekan menjadi QR code.
        """
        qr = qrcode.QRCode(
            version=1,  # Ukuran QR Code
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        qr.print_ascii()

    def proses_pembayaran_qris(self, total_harga: int) -> Tuple[bool, str]:
        """
        Menangani pembayaran QRIS dengan mencetak QR Code di terminal.

        Args:
            total_harga (int): Total harga yang harus dibayar.

        Returns:
            Tuple[bool, str]: Tuple yang berisi status pembayaran (bool) dan metode pembayaran (str).
        """
        print(
            f"\n🔃 - Memproses pembayaran QRIS untuk Rp{total_harga}, mohon tunggu sebentar!"
        )

        # Menghasilkan Reference ID unik
        ref_id = self.generate_random_string()
        ip_lokal = socket.gethostbyname(socket.gethostname())
        url_data_qr = f"http://{ip_lokal}:{Konfigurasi.PORT}/search?ref_id={ref_id}"

        # Membuat QR code
        self.generate_qr(url_data_qr)

        # Menambahkan data QR ke worksheet
        self.manajer_db.worksheet_qr.append_row(
            [
                ref_id,
                total_harga,
                "Pembayaran QRIS",
                datetime.now().strftime("%d-%m-%Y, %H:%M:%S"),
                "Pending",
            ]
        )
        # Menambahkan data QR ke dalam cache lokal
        with self.manajer_db.kunci:
            self.manajer_db.daftar_qr.append(
                DataRefID(
                    ref_id=ref_id,
                    total_harga=total_harga,
                    metode_pembayaran="Pembayaran QRIS",
                    timestamp=datetime.now().strftime("%d-%m-%Y, %H:%M:%S"),
                    status="Pending",
                    nomor_baris=len(self.manajer_db.daftar_qr) + 2,
                )
            )

        # Menunggu hingga pembayaran selesai atau timeout
        start_time = time.time()
        while True:
            time.sleep(5)  # Tunggu 5 detik sebelum memeriksa status

            # Periksa apakah waktu sudah lebih dari 5 menit
            if time.time() - start_time > Konfigurasi.QRIS_TIMEOUT:  # Timeout 5 menit
                self.manajer_db.enqueue_update_status_qr(ref_id, "Expired")
                print("⚠ - Pembayaran QRIS telah kadaluarsa.\n")
                return False, "QRIS"

            # Cek status QR dari database
            status = self.cek_status_qr(ref_id)
            if status == "Selesai":
                print("✅ - Pembayaran QRIS berhasil.\n")
                return True, "QRIS"
            elif status == "Expired":
                print("⚠ - Pembayaran QRIS kadaluarsa.\n")
                return False, "QRIS"

    def cek_status_qr(self, ref_id: str) -> str:
        """
        Memeriksa status QR Code dari cache lokal.

        Args:
            ref_id (str): Reference ID dari QR yang akan dicek statusnya.

        Returns:
            str: Status QR Code.
        """
        with self.manajer_db.kunci:
            for data in self.manajer_db.daftar_qr:
                if data.ref_id == ref_id:
                    return data.status
        return "Pending"

    def proses_pembayaran(self, total_harga: int) -> Tuple[bool, Optional[str]]:
        """
        Menangani proses pembayaran.

        Args:
            total_harga (int): Total harga yang harus dibayar.

        Returns:
            Tuple[bool, Optional[str]]: Tuple yang berisi status pembayaran (bool) dan metode pembayaran (str) jika berhasil, None jika dibatalkan.
        """
        print("\n*********** Pilih Metode Pembayaran ************")
        self.tampilkan_metode_pembayaran()
        print(f">>> Total yang harus dibayar: Rp{total_harga}")
        while True:
            metode_pembayaran_input = input_dengan_timeout(
                self.manajer_db,
                "Pilih metode pembayaran (1: Tunai | 2: QRIS | 'x' untuk batal): ",
            )
            if metode_pembayaran_input.lower() == "x":
                print("❌ - Membatalkan proses pembayaran.\n")
                return False, None
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
