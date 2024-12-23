from dataclasses import dataclass

@dataclass
class DataKopi:
    """Merepresentasikan data kopi: nama, harga, stok, nomor baris di sheets, dan nomor menu."""
    nama: str
    harga: int
    sisa: int
    nomor_baris: int
    nomor: int = 0

@dataclass
class DataKomposisi:
    """Merepresentasikan komposisi bahan tambahan pada kopi."""
    gula: int
    krimer: int
    susu: int
    cokelat: int

@dataclass
class ItemPesanan:
    """Merepresentasikan satu item pesanan."""
    kopi: DataKopi
    jumlah: int
    suhu: str
    komposisi: DataKomposisi

@dataclass
class DataRefID:
    """Merepresentasikan data Reference ID untuk pembayaran QR."""
    ref_id: str
    total_harga: int
    metode_pembayaran: str
    timestamp: str
    status: str
    nomor_baris: int = 0

@dataclass
class CatatanPenjualan:
    """Merepresentasikan data penjualan (satu transaksi kopi)."""
    jenis_kopi: str
    suhu: str
    komposisi: str
    jumlah: str
    total_harga: int
    metode_pembayaran: str

    def to_dict(self):
        """
        Mengkonversi objek CatatanPenjualan menjadi dictionary untuk
        disimpan di database.
        
        Returns:
            dict: Dictionary yang berisi informasi penjualan.
        """
        return {
            "jenis_kopi": self.jenis_kopi,
            "suhu": self.suhu,
            "komposisi": self.komposisi,
            "jumlah": self.jumlah,
            "total_harga": self.total_harga * self.jumlah,
            "metode_pembayaran": "Pembelian Daring Melalui Website"
        }
