import cv2

from apps.database.manajer_database import ManajerDatabase
from apps.managers.manajer_pesanan import ManajerPesanan
from apps.data_classes import DataKomposisi, CatatanPenjualan


class ManajerPesananOnline:
    """Kelas untuk mengelola proses pemindaian QR Code Antrian Pesanan Online."""

    def __init__(self, manajer_db: ManajerDatabase, manajer_pesanan: ManajerPesanan):
        self.manajer_db = manajer_db
        self.manajer_pesanan = manajer_pesanan
        self.daftar_kopi = manajer_pesanan.daftar_kopi
        self.menu_manager = manajer_pesanan.manajer_menu

    def format_komposisi(self, komposisi: DataKomposisi) -> str:
        """
        Mengubah objek DataKomposisi menjadi string yang dapat disimpan di sheets.

        Args:
            komposisi (DataKomposisi): Objek komposisi yang akan diformat

        Returns:
            str: String representasi komposisi
        """
        parts = []
        if komposisi.gula > 0:
            parts.append(f"Gula: {komposisi.gula}")
        if komposisi.krimer > 0:
            parts.append(f"Krimer: {komposisi.krimer}")
        if komposisi.susu > 0:
            parts.append(f"Susu: {komposisi.susu}")
        if komposisi.cokelat > 0:
            parts.append(f"Cokelat: {komposisi.cokelat}")
        return ", ".join(parts) if parts else "Tanpa tambahan"

    def scan_qr(self) -> None:
        """Fungsi untuk memindai QR dan mengonfirmasi pesanan dengan status `Pending`."""
        detektor = cv2.QRCodeDetector()
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
                data, _, _ = detektor.detectAndDecode(frame)
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

        data_qr = self.manajer_db.worksheet_pesanan_online.get_all_records()
        indeks_kolom_pesanan_online = self.manajer_db.dapatkan_indeks_kolom(
            self.manajer_db.worksheet_pesanan_online
        )
        indeks_kolom_persediaan = self.manajer_db.dapatkan_indeks_kolom(
            self.manajer_db.worksheet_persediaan
        )
        self.daftar_kopi = self.manajer_db.daftar_kopi
        self.menu_manager.tetapkan_nomor_kopi()

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

                komposisi = DataKomposisi(
                    gula=int(baris.get("Gula", 0)),
                    krimer=int(baris.get("Krimer", 0)),
                    susu=int(baris.get("Susu", 0)),
                    cokelat=int(baris.get("Cokelat", 0)),
                )
                suhu = baris["Suhu"].lower()

                # Menambah pesanan ke daftar
                self.manajer_pesanan.tambah_pesanan(
                    pesanan, kopi, suhu, komposisi, jumlah_dapat_diproses
                )

                # Memperbarui status pesanan di Google Sheets
                if jumlah_dapat_diproses == jumlah_dipesan:
                    self.manajer_db.worksheet_pesanan_online.update_cell(
                        index, indeks_kolom_pesanan_online["Status"], "Selesai"
                    )
                    self.manajer_db.worksheet_pesanan_online.update_cell(
                        index, indeks_kolom_pesanan_online["Jumlah"], 0
                    )
                else:
                    sisa_pesanan = jumlah_dipesan - jumlah_dapat_diproses
                    self.manajer_db.worksheet_pesanan_online.update_cell(
                        index, indeks_kolom_pesanan_online["Jumlah"], sisa_pesanan
                    )

                stok_baru = kopi.sisa - jumlah_dapat_diproses
                self.manajer_db.worksheet_persediaan.update_cell(
                    kopi.nomor_baris,
                    indeks_kolom_persediaan["Sisa Persediaan"],
                    stok_baru,
                )
                kopi.sisa = stok_baru

            elif str(baris["QR"]) == qr_code and baris["Status"] == "Selesai":
                valid = True

        if pesanan:
            print(" ")
            self.manajer_pesanan.ringkasan_pesanan(pesanan)
            print("\n☕ - Terima kasih! Silakan ambil kopi Anda.\n\n")
            for item in pesanan:
                # Format komposisi sebelum mencatat penjualan
                komposisi_str = self.format_komposisi(item.komposisi)
                self.manajer_db.catat_penjualan(
                    CatatanPenjualan(
                        jenis_kopi=item.kopi.nama,
                        suhu=item.suhu,
                        komposisi=komposisi_str,  # Menggunakan string yang sudah diformat
                        jumlah=f"x{item.jumlah}",
                        total_harga=item.kopi.harga,
                        metode_pembayaran="Pembelian Daring Melalui Website",
                    )
                )
        else:
            if not habis:
                if valid:
                    print("ℹ - Semua pesanan dengan QR ini sudah selesai.\n\n")
                else:
                    print("⚠ - QR yang diberikan tidak valid.\n\n")
