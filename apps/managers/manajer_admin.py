from apps.database.manajer_database import ManajerDatabase

from apps.utils.utils_input import input_dengan_timeout

class ManajerAdmin:
    """
    Mengelola fitur admin: restock kopi, restock bahan tambahan, ganti kode admin, dan matikan program.
    Memastikan autentikasi admin sebelum melanjutkan.
    """

    def __init__(self, manajer_db: ManajerDatabase):
        """
        Inisialisasi ManajerAdmin.

        Args:
            manajer_db (ManajerDatabase): Objek ManajerDatabase untuk berinteraksi dengan database.
        """
        self.manajer_db = manajer_db

    def autentikasi_admin(self) -> bool:
        """
        Meminta kode admin dan melakukan autentikasi.
        Maksimal 5 percobaan.

        Returns:
            bool: True jika autentikasi berhasil, False jika gagal atau dibatalkan.
        """
        batas_percobaan = 5
        percobaan = 0
        while percobaan < batas_percobaan:
            kode_input = input_dengan_timeout(
                self.manajer_db, "Masukkan kode admin ('x' untuk batal): "
            )
            if kode_input.lower() == "x":
                print("❌ - Membatalkan aksi admin.\n")
                return False
            try:
                kode = int(kode_input)
            except ValueError:
                print("⚠ - Kode admin harus berupa angka.")
                percobaan += 1
                continue

            if kode == self.manajer_db.kode_admin:
                print("✅ - Autentikasi berhasil.\n")
                return True
            else:
                percobaan += 1
                print(
                    f"⚠ - Kode admin salah! {batas_percobaan - percobaan} percobaan tersisa."
                )
        print("⚠ - Autentikasi administrator gagal.\n")
        return False

    def restock_kopi(self) -> None:
        """
        Admin melakukan restock kopi.
        Menambah stok kopi sesuai input.
        """
        print("\n*********** Menu Restock Kopi ************")
        # Autentikasi sudah dilakukan sebelum memasuki submenu admin
        daftar_kopi = self.manajer_db.daftar_kopi
        while True:
            print("==== Daftar Kopi ====")
            peta_nomor = {}
            nomor = 1
            for kopi in daftar_kopi.values():
                if kopi.sisa >= 0:
                    print(f"{nomor}. {kopi.nama} - Stok: {kopi.sisa}")
                    peta_nomor[nomor] = kopi
                    nomor += 1
            print("=====================")

            pilihan_kopi_input = input_dengan_timeout(
                self.manajer_db, "Pilih kopi untuk restock ('x' untuk batal): "
            )
            if pilihan_kopi_input.lower() == "x":
                print("❌ - Membatalkan restock kopi.\n")
                return
            if not pilihan_kopi_input.isdigit():
                print("⚠ - Masukkan nomor kopi atau 'x' untuk batal.")
                continue
            pilihan_kopi = int(pilihan_kopi_input)
            if pilihan_kopi not in peta_nomor:
                print("⚠ - Nomor kopi tidak valid.")
                continue
            kopi = peta_nomor[pilihan_kopi]

            # Masukkan jumlah restock
            while True:
                jumlah_restock_input = input_dengan_timeout(
                    self.manajer_db,
                    f"Masukkan jumlah restock untuk {kopi.nama} ('x' untuk batal): ",
                )
                if jumlah_restock_input.lower() == "x":
                    print("❌ - Membatalkan restock kopi.\n")
                    return
                try:
                    jumlah_restock = int(jumlah_restock_input)
                    if jumlah_restock <= 0:
                        print("⚠ - Jumlah restock harus > 0.")
                        continue
                    # Gunakan metode synchronous untuk restock
                    self.manajer_db.restock_kopi_sync(kopi.nama, jumlah_restock)
                    print(
                        f"✅ - Berhasil restock {kopi.nama} sebanyak {jumlah_restock}.\n"
                    )
                    break
                except ValueError:
                    print("⚠ - Masukkan harus berupa angka.")

            lagi_input = input_dengan_timeout(
                self.manajer_db, "\nApakah ingin melakukan restock lagi? (y/n): "
            ).lower()
            if lagi_input in ["y", "ya"]:
                continue
            else:
                print("\n🔃 - Kembali ke submenu admin.\n")
                return

    def restock_bahan_tambahan(self) -> None:
        """
        Admin melakukan restock bahan tambahan.
        Menambah stok bahan tambahan sesuai input.
        """
        print("\n*********** Menu Restock Bahan Tambahan ************")
        # Autentikasi sudah dilakukan sebelum memasuki submenu admin
        daftar_tambahan = self.manajer_db.daftar_tambahan
        while True:
            print("==== Daftar Bahan Tambahan ====")
            peta_nomor = {}
            nomor = 1
            for bahan, stok in daftar_tambahan.items():
                print(f"{nomor}. {bahan} - Stok: {stok}")
                peta_nomor[nomor] = bahan
                nomor += 1
            print("===============================")

            pilihan_bahan_input = input_dengan_timeout(
                self.manajer_db,
                "Pilih bahan tambahan untuk restock ('x' untuk batal): ",
            )
            if pilihan_bahan_input.lower() == "x":
                print("❌ - Membatalkan restock bahan tambahan.\n")
                return
            if not pilihan_bahan_input.isdigit():
                print("⚠ - Masukkan nomor bahan tambahan atau 'x' untuk batal.")
                continue
            pilihan_bahan = int(pilihan_bahan_input)
            if pilihan_bahan not in peta_nomor:
                print("⚠ - Nomor bahan tambahan tidak valid.")
                continue
            bahan = peta_nomor[pilihan_bahan]

            # Masukkan jumlah restock
            while True:
                jumlah_restock_input = input_dengan_timeout(
                    self.manajer_db,
                    f"Masukkan jumlah restock untuk {bahan} ('x' untuk batal): ",
                )
                if jumlah_restock_input.lower() == "x":
                    print("❌ - Membatalkan restock bahan tambahan.\n")
                    return
                try:
                    jumlah_restock = int(jumlah_restock_input)
                    if jumlah_restock <= 0:
                        print("⚠ - Jumlah restock harus > 0.")
                        continue
                    # Gunakan metode synchronous untuk restock
                    self.manajer_db.restock_bahan_tambahan_sync(bahan, jumlah_restock)
                    print(
                        f"✅ - Berhasil restock {bahan} sebanyak {jumlah_restock} takaran.\n"
                    )
                    break
                except ValueError:
                    print("⚠ - Masukkan harus berupa angka.")

            lagi_input = input_dengan_timeout(
                self.manajer_db, "\nApakah ingin melakukan restock lagi? (y/n): "
            ).lower()
            if lagi_input in ["y", "ya"]:
                continue
            else:
                print("\n🔃 - Kembali ke submenu admin.\n")
                return

    def ganti_kode_admin(self) -> None:
        """
        Mengganti kode admin secara permanen.
        Hanya bisa dilakukan oleh admin yang sudah terautentikasi.
        """
        print("\n*********** Ganti Kode Admin ************")
        # Autentikasi sudah dilakukan sebelum memasuki submenu admin
        while True:
            kode_baru_input = input_dengan_timeout(
                self.manajer_db, "Masukkan kode admin baru ('x' untuk batal): "
            )
            if kode_baru_input.lower() == "x":
                print("❌ - Membatalkan penggantian kode admin.\n")
                return
            try:
                kode_baru = int(kode_baru_input)
                if kode_baru > 0:
                    self.manajer_db.simpan_kode_admin(kode_baru)
                    print("✅ - Kode admin berhasil diganti.\n")
                    return
                else:
                    print("⚠ - Kode admin harus > 0.")
            except ValueError:
                print("⚠ - Kode admin harus berupa angka.")

    def matikan_program(self) -> None:
        """
        Mematikan program setelah autentikasi admin.
        Jika autentikasi sukses, program keluar setelah sinkronisasi terakhir.
        """
        print("\n*********** Menonaktifkan Program ************")
        # Autentikasi sudah dilakukan sebelum memasuki submenu admin
        print("💤 - Mesin kopi dimatikan. Menyimpan perubahan terakhir...")
        self.manajer_db.simpan_perubahan_sebelum_keluar()
        print("Program akan keluar.")

        import sys
        sys.exit(0)
