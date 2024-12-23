from typing import List
from apps.database.manajer_database import ManajerDatabase
from apps.managers.manajer_menu import ManajerMenu
from apps.managers.manajer_pesanan import ManajerPesanan
from apps.managers.manajer_pembayaran import ManajerPembayaran
from apps.managers.manajer_pesanan_online import ManajerPesananOnline
from apps.managers.manajer_admin import ManajerAdmin
from apps.data_classes import CatatanPenjualan
from apps.utils.utils_input import input_dengan_timeout

class MesinKopi:
    """
    Kelas utama yang mensimulasikan mesin kopi.
    Menggabungkan seluruh alur: pemesanan, pembayaran, restock, scan QR, ganti kode admin, shutdown.
    """

    def __init__(self, manajer_db: ManajerDatabase):
        """
        Inisialisasi kelas MesinKopi.

        Args:
            manajer_db (ManajerDatabase): Instance dari kelas ManajerDatabase untuk mengelola database.
        """
        self.manajer_db = manajer_db
        self.daftar_kopi = manajer_db.daftar_kopi
        self.daftar_tambahan = manajer_db.daftar_tambahan

        # Tentukan kopi terlaris
        kopi_terlaris = self.manajer_db.dapatkan_kopi_terlaris()

        self.manajer_menu = ManajerMenu(self.daftar_kopi, kopi_terlaris)
        self.manajer_menu.tetapkan_nomor_kopi()

        self.manajer_pesanan = ManajerPesanan(
            self.manajer_db, self.daftar_kopi, self.manajer_menu, self.daftar_tambahan
        )
        self.manajer_scan_qr = ManajerPesananOnline(
            self.manajer_db, self.manajer_pesanan
        )
        self.manajer_admin = ManajerAdmin(self.manajer_db)
        self.manajer_pembayaran = ManajerPembayaran(self.manajer_db)

    def simulasi(self) -> None:
        """
        Fungsi utama yang menampilkan menu dan menangani pilihan pengguna.
        """
        print("\n=== Selamat datang di Mesin Kopi Virtual! ===\n")
        while True:
            print("======= Pilihan Menu =======")
            print("1. Mulai Pemesanan")
            print("2. Scan QR")
            print("3. Menu Admin")
            print("============================")
            pilihan = input("Pilih opsi (1, 2, 3): ")
            if pilihan == "1":
                self.mulai_pemesanan()
            elif pilihan == "2":
                self.manajer_scan_qr.scan_qr()
            elif pilihan == "3":
                self.menu_admin()
            else:
                print("⚠ - Pilihan tidak valid. Silakan pilih 1, 2, atau 3.")

    def menu_admin(self) -> None:
        """
        Menangani alur Menu Admin.
        """
        print("\n*********** Menu Admin ************")
        autentikasi = self.manajer_admin.autentikasi_admin()
        if not autentikasi:
            return

        while True:
            print("\n======= Submenu Admin =======")
            print("1. Restock Kopi")
            print("2. Restock Bahan Tambahan")
            print("3. Ganti Kode Admin")
            print("4. Matikan Program")
            print("5. Kembali ke Menu Utama")
            print("==============================")
            pilihan = input_dengan_timeout(
                self.manajer_db, "Pilih opsi admin (1, 2, 3, 4, 5): "
            )
            if pilihan == "1":
                self.manajer_admin.restock_kopi()
            elif pilihan == "2":
                self.manajer_admin.restock_bahan_tambahan()
            elif pilihan == "3":
                self.manajer_admin.ganti_kode_admin()
            elif pilihan == "4":
                self.manajer_admin.matikan_program()
            elif pilihan == "5":
                print("\n🔃 - Kembali ke menu utama.\n")
                break
            else:
                print("⚠ - Pilihan tidak valid. Silakan pilih 1, 2, 3, 4, atau 5.")

    def mulai_pemesanan(self) -> None:
        """
        Memulai proses pemesanan kopi.
        Mengecek stok dan bahan tambahan sebelum ke pembayaran.
        """
        if not self.daftar_kopi:
            print("\n💔 - Mohon maaf, tidak ada kopi yang tersedia saat ini.\n")
            return
        pesanan = self.manajer_pesanan.pilih_kopi()
        if pesanan:
            # Cek stok kopi dan bahan sekali lagi (redundan tapi aman)
            stok_cukup = True
            for item in pesanan:
                if item.kopi.sisa < item.jumlah:
                    print(
                        f"☕ - Stok {item.kopi.nama} tidak cukup. Tersisa {item.kopi.sisa}."
                    )
                    stok_cukup = False
                    break
                # Cek bahan tambahan
                if not self.manajer_pesanan.cek_stok_tambahan(
                    item.komposisi, item.jumlah
                ):
                    stok_cukup = False
                    break

            if not stok_cukup:
                print("🔃 - Silakan ulangi pemesanan.\n")
                return

            total_harga = self.manajer_pesanan.ringkasan_pesanan(pesanan)
            pembayaran_sukses, metode = self.manajer_pembayaran.proses_pembayaran(
                total_harga
            )

            if pembayaran_sukses:
                print("☕ - Terima kasih! Silakan ambil kopi Anda.\n")
                # Update stok kopi dan bahan, catat penjualan
                for item in pesanan:
                    # Catat penjualan
                    catatan_penjualan = CatatanPenjualan(
                        jenis_kopi=item.kopi.nama,
                        suhu=item.suhu,
                        komposisi=f"Gula ({item.komposisi.gula} takaran), "
                        f"Susu ({item.komposisi.susu} takaran), "
                        f"Krimer ({item.komposisi.krimer} takaran), "
                        f"Cokelat ({item.komposisi.cokelat} takaran)",
                        jumlah=f"x{item.jumlah}",
                        total_harga=item.kopi.harga * item.jumlah,
                        metode_pembayaran=metode,
                    )
                    self.manajer_db.enqueue_catat_penjualan(catatan_penjualan)

                    # Update stok kopi
                    self.manajer_db.enqueue_update_stok(item.kopi.nama, item.jumlah)

                    # Update stok bahan tambahan
                    self.manajer_db.enqueue_update_tambahan(
                        "Gula", -(item.komposisi.gula * item.jumlah)
                    )
                    self.manajer_db.enqueue_update_tambahan(
                        "Krimer", -(item.komposisi.krimer * item.jumlah)
                    )
                    self.manajer_db.enqueue_update_tambahan(
                        "Susu", -(item.komposisi.susu * item.jumlah)
                    )
                    self.manajer_db.enqueue_update_tambahan(
                        "Cokelat", -(item.komposisi.cokelat * item.jumlah)
                    )

                # Update data lokal setelah enqueue
                self.daftar_kopi = self.manajer_db.daftar_kopi
                self.daftar_tambahan = self.manajer_db.daftar_tambahan
                kopi_terlaris = self.manajer_db.dapatkan_kopi_terlaris()
                self.manajer_menu = ManajerMenu(self.daftar_kopi, kopi_terlaris)
                self.manajer_menu.tetapkan_nomor_kopi()
            else:
                if metode is None:
                    print("💰 - Pembayaran dibatalkan.\n")
                else:
                    print("📉 - Pembayaran gagal.\n")
        else:
            print("📃 - Tidak ada pesanan. Kembali ke menu utama.\n")
