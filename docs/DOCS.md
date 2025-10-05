# **Dokumentasi Tugas Besar Berpikir Komputasional (Coffee Machine _Extended Version_)**

## 1. Data Classes

### 1.1 DataKopi
Kelas yang merepresentasikan informasi lengkap tentang satu jenis kopi dalam sistem.

| Atribut | Tipe Data | Deskripsi |
|---------|-----------|-----------|
| `nama` | str | Nama jenis kopi yang unik dalam sistem |
| `harga` | int | Harga kopi dalam Rupiah |
| `sisa` | int | Jumlah stok yang tersedia saat ini |
| `nomor_baris` | int | Posisi data dalam spreadsheet untuk update |
| `nomor` | int | Nomor urut yang ditampilkan di menu (default: 0) |

**Contoh Penggunaan:**
```python
kopi_arabika = DataKopi(
    nama="Kopi Arabika Premium",
    harga=25000,
    sisa=100,
    nomor_baris=2,
    nomor=1
)
```

### 1.2 DataKomposisi
Kelas yang mengatur detail komposisi bahan tambahan dalam setiap pesanan kopi.

| Atribut | Tipe Data | Deskripsi |
|---------|-----------|-----------|
| `gula` | int | Jumlah takaran gula (0-5 takaran) |
| `krimer` | int | Jumlah takaran krimer (0-5 takaran) |
| `susu` | int | Jumlah takaran susu (0-5 takaran) |
| `cokelat` | int | Jumlah takaran cokelat (0-5 takaran) |

**Panduan Takaran:**
- 0 = Tanpa tambahan
- 1 = Sangat sedikit
- 2 = Sedikit
- 3 = Sedang
- 4 = Banyak
- 5 = Sangat banyak

**Contoh Penggunaan:**
```python
komposisi_latte = DataKomposisi(
    gula=2,    # Sedikit gula
    krimer=3,  # Krimer sedang
    susu=4,    # Susu banyak
    cokelat=1  # Sedikit cokelat
)
```

### 1.3 ItemPesanan
Kelas yang merepresentasikan satu item dalam pesanan pelanggan.

| Atribut | Tipe Data | Deskripsi |
|---------|-----------|-----------|
| `kopi` | DataKopi | Referensi ke objek kopi yang dipesan |
| `jumlah` | int | Jumlah cup yang dipesan |
| `suhu` | str | Pilihan suhu ("hangat" atau "dingin") |
| `komposisi` | DataKomposisi | Referensi ke komposisi yang dipilih |

**Contoh Penggunaan:**
```python
pesanan = ItemPesanan(
    kopi=kopi_arabika,
    jumlah=2,
    suhu="hangat",
    komposisi=komposisi_latte
)
```

### 1.4 DataRefID
Kelas yang menyimpan informasi referensi untuk pembayaran QR.

| Atribut | Tipe Data | Deskripsi |
|---------|-----------|-----------|
| `ref_id` | str | ID referensi unik untuk transaksi |
| `total_harga` | int | Total harga yang harus dibayar |
| `metode_pembayaran` | str | Metode pembayaran yang digunakan |
| `timestamp` | str | Waktu pembuatan referensi |
| `status` | str | Status pembayaran ("Pending"/"Selesai"/"Expired") |
| `nomor_baris` | int | Posisi dalam spreadsheet (default: 0) |

**Contoh Penggunaan:**
```python
ref_qr = DataRefID(
    ref_id="QR123456789",
    total_harga=50000,
    metode_pembayaran="QRIS",
    timestamp="2024-12-23 14:30:00",
    status="Pending",
    nomor_baris=5
)
```

### 1.5 CatatanPenjualan
Kelas yang mencatat detail transaksi penjualan untuk pelaporan.

| Atribut | Tipe Data | Deskripsi |
|---------|-----------|-----------|
| `jenis_kopi` | str | Nama kopi yang terjual |
| `suhu` | str | Suhu penyajian |
| `komposisi` | str | Detail komposisi dalam format string |
| `jumlah` | str | Jumlah pesanan dalam format "x{jumlah}" |
| `total_harga` | int | Total harga pesanan |
| `metode_pembayaran` | str | Metode pembayaran yang digunakan |

**Contoh Penggunaan:**
```python
catatan = CatatanPenjualan(
    jenis_kopi="Kopi Arabika Premium",
    suhu="hangat",
    komposisi="Gula (2), Krimer (3), Susu (4), Cokelat (1)",
    jumlah="x2",
    total_harga=50000,
    metode_pembayaran="QRIS"
)
```

## 2. Manajer Database

### 2.1 Inisialisasi ManajerDatabase

#### Method: `__init__(self)`

**Deskripsi:**  
Metode inisialisasi yang mengatur koneksi ke Google Sheets dan mempersiapkan sistem caching.

**Proses Detail:**
1. Mengatur kredensial Google Sheets
2. Mengotorisasi koneksi
3. Membuka spreadsheet target
4. Menginisialisasi worksheet untuk setiap jenis data
5. Membuat threading lock
6. Membuat antrian update
7. Memuat data awal ke cache
8. Memulai thread sinkronisasi

**Atribut yang Diinisialisasi:**

| Atribut | Tipe Data | Deskripsi |
|---------|-----------|-----------|
| `worksheet_persediaan` | gspread.Worksheet | Worksheet untuk data kopi |
| `worksheet_tambahan` | gspread.Worksheet | Worksheet untuk bahan tambahan |
| `worksheet_qr` | gspread.Worksheet | Worksheet untuk data QR |
| `worksheet_penjualan` | gspread.Worksheet | Worksheet untuk penjualan |
| `worksheet_pesanan_online` | gspread.Worksheet | Worksheet untuk pesanan online |
| `kunci` | threading.Lock | Lock untuk sinkronisasi thread |
| `antrian_update` | queue.Queue | Antrian operasi update |
| `daftar_kopi` | Dict[str, DataKopi] | Cache kopi |
| `daftar_tambahan` | Dict[str, int] | Cache bahan tambahan |
| `daftar_qr` | List[DataRefID] | Cache data QR |
| `kode_admin` | int | Kode akses admin |

**Contoh Penggunaan:**
```python
manajer_db = ManajerDatabase()
```

### 2.2 Manajemen Kode Admin

#### Method: `muat_kode_admin(self) -> int`

**Deskripsi:**  
Membaca kode admin dari file atau menggunakan nilai default jika file tidak ada.

**Proses Detail:**
1. Mencari file admin_code.txt di direktori credentials
2. Membaca kode dari file jika ada
3. Menggunakan kode default jika file tidak ada
4. Membuat file baru dengan kode default jika diperlukan

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| int | Kode admin yang akan digunakan |

### 2.3 Manajemen Data Kopi dan Tambahan

#### Method: `simpan_kode_admin(self, kode_baru: int) -> None`

**Deskripsi:**  
Menyimpan kode admin baru ke dalam file secara permanen.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `kode_baru` | int | Kode admin baru yang akan disimpan |

**Proses Detail:**
1. Membuka file admin_code.txt dalam mode write
2. Menulis kode baru ke file
3. Memperbarui variabel instance kode_admin
4. Menangani error jika terjadi masalah penulisan

**Contoh Penggunaan:**
```python
manajer_db.simpan_kode_admin(123456)
```

#### Method: `muat_data_kopi(self) -> Dict[str, DataKopi]`

**Deskripsi:**  
Memuat data kopi dari worksheet ke dalam cache lokal.

**Proses Detail:**
1. Mengambil semua record dari worksheet persediaan
2. Mengkonversi setiap baris menjadi objek DataKopi
3. Menyimpan dalam dictionary dengan nama kopi sebagai key

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| Dict[str, DataKopi] | Dictionary berisi data kopi dengan nama sebagai key |

**Contoh Penggunaan:**
```python
daftar_kopi = manajer_db.muat_data_kopi()
for nama, kopi in daftar_kopi.items():
    print(f"{nama}: {kopi.sisa} cup tersedia")
```

#### Method: `muat_data_tambahan(self) -> Dict[str, int]`

**Deskripsi:**  
Memuat data bahan tambahan dari worksheet ke cache lokal.

**Proses Detail:**
1. Mengambil semua record dari worksheet bahan tambahan
2. Mengkonversi data ke dictionary
3. Menyimpan data dalam format nama bahan -> jumlah stok

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| Dict[str, int] | Dictionary berisi stok bahan tambahan |

**Contoh Penggunaan:**
```python
daftar_tambahan = manajer_db.muat_data_tambahan()
for bahan, stok in daftar_tambahan.items():
    print(f"{bahan}: {stok} takaran tersisa")
```

#### Method: `muat_daftar_qr(self) -> List[DataRefID]`

**Deskripsi:**  
Memuat data referensi QR dari worksheet ke cache lokal.

**Proses Detail:**
1. Mengambil semua record dari worksheet QR
2. Mengkonversi setiap baris menjadi objek DataRefID
3. Menyimpan dalam list untuk tracking status pembayaran

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| List[DataRefID] | List berisi semua data referensi QR |

**Contoh Penggunaan:**
```python
daftar_qr = manajer_db.muat_daftar_qr()
for qr in daftar_qr:
    if qr.status == "Pending":
        print(f"QR {qr.ref_id} menunggu pembayaran")
```

#### Method: `dapatkan_kopi_terlaris(self) -> str`

**Deskripsi:**  
Menganalisis data penjualan untuk menentukan kopi terlaris.

**Proses Detail:**
1. Mengambil semua record dari worksheet penjualan
2. Menghitung total penjualan untuk setiap jenis kopi
3. Menentukan kopi dengan penjualan tertinggi

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| str | Nama kopi terlaris, atau string kosong jika tidak ada data |

**Contoh Penggunaan:**
```python
kopi_terlaris = manajer_db.dapatkan_kopi_terlaris()
print(f"Kopi terlaris: {kopi_terlaris}")
```

### 2.4 Sinkronisasi Data

#### Method: `sinkronisasi_periodik(self) -> None`

**Deskripsi:**  
Melakukan sinkronisasi berkala antara cache lokal dan Google Sheets.

**Proses Detail:**
1. Memproses semua operasi dalam antrian update
2. Mengupdate spreadsheet kopi
3. Mengupdate spreadsheet bahan tambahan
4. Mengupdate spreadsheet QR
5. Menunggu interval waktu tertentu
6. Menangani error yang mungkin terjadi

**Variabel yang Digunakan:**

| Variabel | Tipe Data | Deskripsi |
|----------|-----------|-----------|
| `operasi` | Tuple | Tuple berisi tipe operasi dan data terkait |
| `tipe_operasi` | str | Jenis operasi update yang dilakukan |
| `data_tambahan` | List[Dict] | Data bahan tambahan dari spreadsheet |
| `peta_baris_bahan` | Dict[str, int] | Mapping nama bahan ke nomor baris |

**Contoh Operasi Update:**
```python
# Update stok kopi
self.worksheet_persediaan.update_cell(kopi.nomor_baris, 3, kopi.sisa)

# Update stok bahan tambahan
self.worksheet_tambahan.update_cell(nomor_baris, 2, self.daftar_tambahan[bahan])

# Update status QR
self.worksheet_qr.update_cell(qr.nomor_baris, 5, qr.status)
```

### 2.5 Manajemen Antrian Update

#### Method: `enqueue_update_stok(self, nama_kopi: str, jumlah_terjual: int) -> None`

**Deskripsi:**  
Menambahkan operasi update stok kopi ke dalam antrian.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `nama_kopi` | str | Nama kopi yang akan diupdate |
| `jumlah_terjual` | int | Jumlah yang terjual |

**Contoh Penggunaan:**
```python
manajer_db.enqueue_update_stok("Kopi Arabika", 2)
```

### 2.6 Operasi Update Database

#### Method: `enqueue_restock_kopi(self, nama_kopi: str, jumlah_restock: int) -> None`

**Deskripsi:**  
Menambahkan operasi restock kopi ke dalam antrian proses.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `nama_kopi` | str | Nama kopi yang akan direstock |
| `jumlah_restock` | int | Jumlah yang akan ditambahkan ke stok |

**Proses Detail:**
1. Membuat tuple operasi restock
2. Menambahkan ke antrian untuk diproses
3. Memastikan thread-safety dengan lock

**Contoh Penggunaan:**
```python
manajer_db.enqueue_restock_kopi("Espresso", 50)
```

#### Method: `enqueue_update_status_qr(self, ref_id: str, status_baru: str) -> None`

**Deskripsi:**  
Menambahkan operasi update status QR ke dalam antrian.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `ref_id` | str | ID referensi QR |
| `status_baru` | str | Status baru ("Pending"/"Selesai"/"Expired") |

**Contoh Penggunaan:**
```python
manajer_db.enqueue_update_status_qr("QR123456", "Selesai")
```

#### Method: `enqueue_catat_penjualan(self, catatan_penjualan: CatatanPenjualan) -> None`

**Deskripsi:**  
Menambahkan operasi pencatatan penjualan ke dalam antrian.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `catatan_penjualan` | CatatanPenjualan | Objek berisi detail penjualan |

**Contoh Penggunaan:**
```python
catatan = CatatanPenjualan(
    jenis_kopi="Americano",
    suhu="dingin",
    komposisi="Gula (2), Susu (1)",
    jumlah="x1",
    total_harga=25000,
    metode_pembayaran="Tunai"
)
manajer_db.enqueue_catat_penjualan(catatan)
```

#### Method: `enqueue_update_tambahan(self, bahan: str, jumlah: int) -> None`

**Deskripsi:**  
Menambahkan operasi update stok bahan tambahan ke dalam antrian.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `bahan` | str | Nama bahan tambahan |
| `jumlah` | int | Jumlah perubahan (positif/negatif) |

**Contoh Penggunaan:**
```python
# Mengurangi stok gula
manajer_db.enqueue_update_tambahan("Gula", -2)

# Menambah stok susu
manajer_db.enqueue_update_tambahan("Susu", 50)
```

### 2.7 Operasi Sinkronisasi dan Update

#### Method: `update_stok(self, nama_kopi: str, jumlah_terjual: int) -> None`

**Deskripsi:**  
Mengupdate stok kopi di cache lokal.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `nama_kopi` | str | Nama kopi yang diupdate |
| `jumlah_terjual` | int | Jumlah yang terjual |

**Proses Detail:**
1. Memverifikasi keberadaan kopi di cache
2. Mengurangi stok sesuai jumlah terjual
3. Memastikan stok tidak negatif

**Contoh Penggunaan:**
```python
manajer_db.update_stok("Cappuccino", 3)
```

#### Method: `restock_kopi(self, nama_kopi: str, jumlah_restock: int) -> None`

**Deskripsi:**  
Menambah stok kopi di cache lokal.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `nama_kopi` | str | Nama kopi untuk restock |
| `jumlah_restock` | int | Jumlah yang ditambahkan |

**Contoh Penggunaan:**
```python
manajer_db.restock_kopi("Latte", 100)
```

#### Method: `update_status_qr(self, ref_id: str, status_baru: str) -> None`

**Deskripsi:**  
Mengupdate status QR di cache lokal.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `ref_id` | str | ID referensi QR |
| `status_baru` | str | Status yang akan diset |

**Contoh Penggunaan:**
```python
manajer_db.update_status_qr("QR789012", "Expired")
```

### 2.8 Operasi Pembersihan dan Finalisasi

#### Method: `simpan_perubahan_sebelum_keluar(self) -> None`

**Deskripsi:**  
Memastikan semua perubahan tersimpan sebelum program dimatikan.

**Proses Detail:**
1. Mengosongkan antrian update
2. Memproses semua operasi pending
3. Memperbarui semua worksheet terkait
4. Menangani error yang mungkin terjadi

**Contoh Penggunaan:**
```python
try:
    # Operasi normal program
    pass
finally:
    manajer_db.simpan_perubahan_sebelum_keluar()
```

## 3. Manajer Menu (ManajerMenu)

### 3.1 Inisialisasi Manajer Menu

#### Method: `__init__(self, daftar_kopi: Dict[str, DataKopi], nama_kopi_terlaris: str = "")`

**Deskripsi:**  
Menginisialisasi manajer menu dengan daftar kopi dan kopi terlaris.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `daftar_kopi` | Dict[str, DataKopi] | Dictionary berisi semua kopi tersedia |
| `nama_kopi_terlaris` | str | Nama kopi dengan penjualan tertinggi |

**Atribut yang Diinisialisasi:**

| Atribut | Tipe Data | Deskripsi |
|---------|-----------|-----------|
| `daftar_kopi` | Dict[str, DataKopi] | Cache daftar kopi |
| `nama_kopi_terlaris` | str | Referensi kopi terlaris |

**Contoh Penggunaan:**
```python
manajer_menu = ManajerMenu(
    daftar_kopi={
        "Espresso": DataKopi("Espresso", 20000, 50, 2, 1),
        "Latte": DataKopi("Latte", 25000, 40, 3, 2)
    },
    nama_kopi_terlaris="Latte"
)
```

### 3.2 Manajemen Nomor Menu

#### Method: `tetapkan_nomor_kopi(self) -> None`

**Deskripsi:**  
Memberikan nomor urut pada setiap kopi yang memiliki stok tersedia.

**Proses Detail:**
1. Menginisialisasi counter nomor
2. Memeriksa stok setiap kopi
3. Memberikan nomor urut pada kopi dengan stok > 0
4. Mengabaikan kopi dengan stok habis

**Contoh Penggunaan:**
```python
manajer_menu.tetapkan_nomor_kopi()
```

### 3.3 Tampilan Menu

#### Method: `tampilkan_menu_kopi(self) -> None`

**Deskripsi:**  
Menampilkan daftar kopi yang tersedia dengan format terstruktur.

**Proses Detail:**
1. Mencetak header menu
2. Menampilkan setiap kopi dengan stok > 0
3. Menambahkan tanda bintang untuk kopi terlaris
4. Menampilkan harga dan stok tersisa

**Format Tampilan:**
```
================ Menu Kopi =================
1. Espresso - Rp20000 - Persediaan: 50
2. Latte ★ - Rp25000 - Persediaan: 40
=============================================
```

## 4. Manajer Pesanan (ManajerPesanan)

### 4.1 Inisialisasi Manajer Pesanan

#### Method: `__init__(self, manajer_db: ManajerDatabase, daftar_kopi: Dict[str, DataKopi], manajer_menu: ManajerMenu, daftar_tambahan: Dict[str, int])`

**Deskripsi:**  
Menginisialisasi manajer pesanan dengan semua dependensi yang diperlukan.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `manajer_db` | ManajerDatabase | Instance database manager |
| `daftar_kopi` | Dict[str, DataKopi] | Dictionary kopi tersedia |
| `manajer_menu` | ManajerMenu | Instance menu manager |
| `daftar_tambahan` | Dict[str, int] | Dictionary bahan tambahan |

**Contoh Penggunaan:**
```python
manajer_pesanan = ManajerPesanan(
    manajer_db=db_manager,
    daftar_kopi=kopi_dict,
    manajer_menu=menu_manager,
    daftar_tambahan=tambahan_dict
)
```

### 4.2 Pemilihan Suhu Kopi

#### Method: `pilih_suhu(self, nama_kopi: str) -> Optional[str]`

**Deskripsi:**  
Menangani proses pemilihan suhu kopi oleh pelanggan.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `nama_kopi` | str | Nama kopi yang dipilih |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| Optional[str] | "hangat"/"dingin" atau None jika dibatalkan |

**Proses Detail:**
1. Menampilkan opsi suhu
2. Memvalidasi input pelanggan
3. Mengembalikan pilihan atau None jika dibatalkan

**Contoh Penggunaan:**
```python
suhu = manajer_pesanan.pilih_suhu("Espresso")
if suhu:
    print(f"Suhu dipilih: {suhu}")
else:
    print("Pemilihan suhu dibatalkan")
```

### 4.3 Pengaturan Komposisi

#### Method: `atur_jumlah(self, tipe_bahan: str) -> Optional[int]`

**Deskripsi:**  
Menangani pengaturan jumlah takaran untuk setiap bahan tambahan.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `tipe_bahan` | str | Jenis bahan tambahan yang diatur |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| Optional[int] | Jumlah takaran (0-5) atau None jika dibatalkan |

**Proses Detail:**
1. Menampilkan stok tersedia
2. Meminta input jumlah takaran
3. Memvalidasi input terhadap batasan dan stok
4. Mengembalikan jumlah yang valid

**Contoh Penggunaan:**
```python
jumlah_gula = manajer_pesanan.atur_jumlah("Gula")
if jumlah_gula is not None:
    print(f"Jumlah gula: {jumlah_gula} takaran")
```

#### Method: `pilih_komposisi(self) -> Optional[DataKomposisi]`

**Deskripsi:**  
Menangani pemilihan komposisi lengkap untuk pesanan kopi.

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| Optional[DataKomposisi] | Objek komposisi atau None jika dibatalkan |

**Proses Detail:**
1. Meminta input untuk setiap bahan tambahan
2. Membuat objek DataKomposisi
3. Memvalidasi ketersediaan semua bahan
4. Mengembalikan komposisi lengkap

**Contoh Penggunaan:**
```python
komposisi = manajer_pesanan.pilih_komposisi()
if komposisi:
    print(f"Gula: {komposisi.gula}, Susu: {komposisi.susu}")
```

### 4.4 Manajemen Pesanan

#### Method: `pesan_jumlah(self) -> Optional[int]`

**Deskripsi:**  
Menangani input jumlah kopi yang akan dipesan.

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| Optional[int] | Jumlah pesanan atau None jika dibatalkan |

**Proses Detail:**
1. Meminta input jumlah pesanan
2. Memvalidasi input harus positif
3. Menangani pembatalan pesanan

**Contoh Penggunaan:**
```python
jumlah = manajer_pesanan.pesan_jumlah()
if jumlah:
    print(f"Memesan {jumlah} cup kopi")
```

#### Method: `komposisi_sama(self, komp1: DataKomposisi, komp2: DataKomposisi) -> bool`

**Deskripsi:**  
Membandingkan dua komposisi untuk menentukan kesamaan.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `komp1` | DataKomposisi | Komposisi pertama |
| `komp2` | DataKomposisi | Komposisi kedua |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| bool | True jika komposisi sama, False jika berbeda |

**Contoh Penggunaan:**
```python
komp1 = DataKomposisi(gula=2, krimer=1, susu=1, cokelat=0)
komp2 = DataKomposisi(gula=2, krimer=1, susu=1, cokelat=0)
if manajer_pesanan.komposisi_sama(komp1, komp2):
    print("Komposisi identik")
```

### 4.5 Pemrosesan Pesanan

#### Method: `tambah_pesanan(self, data_pesanan: List[ItemPesanan], kopi: DataKopi, suhu: str, komposisi: DataKomposisi, jumlah: int) -> List[ItemPesanan]`

**Deskripsi:**  
Menambahkan pesanan baru atau mengupdate pesanan yang ada.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `data_pesanan` | List[ItemPesanan] | Daftar pesanan saat ini |
| `kopi` | DataKopi | Kopi yang dipesan |
| `suhu` | str | Pilihan suhu |
| `komposisi` | DataKomposisi | Komposisi bahan tambahan |
| `jumlah` | int | Jumlah yang dipesan |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| List[ItemPesanan] | Daftar pesanan yang diupdate |

**Proses Detail:**
1. Mencari pesanan serupa yang sudah ada
2. Menggabungkan pesanan jika ditemukan yang sama
3. Menambahkan pesanan baru jika berbeda
4. Mengembalikan daftar pesanan terupdate

**Contoh Penggunaan:**
```python
pesanan_baru = manajer_pesanan.tambah_pesanan(
    data_pesanan=pesanan_existing,
    kopi=kopi_espresso,
    suhu="hangat",
    komposisi=komposisi_standar,
    jumlah=2
)
```

### 4.6 Ringkasan dan Validasi Pesanan

#### Method: `ringkasan_pesanan(self, pesanan: List[ItemPesanan]) -> int`

**Deskripsi:**  
Menampilkan ringkasan pesanan dan menghitung total harga.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `pesanan` | List[ItemPesanan] | Daftar item yang dipesan |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| int | Total harga pesanan |

**Proses Detail:**
1. Menampilkan header ringkasan
2. Menghitung harga per item
3. Menampilkan detail komposisi
4. Menjumlahkan total harga
5. Menampilkan total akhir

**Format Output:**
```
========== Ringkasan Pesanan ==========
1. Espresso (hangat) x2 - Rp40000
   Gula: 2 takaran, Susu: 1 takaran, ...
2. Latte (dingin) x1 - Rp25000
   Gula: 1 takaran, Susu: 3 takaran, ...
>>> Total Harga: Rp65000
=======================================
```

## 5. Manajer Pembayaran (ManajerPembayaran)

### 5.1 Inisialisasi

#### Method: `__init__(self, manajer_db: ManajerDatabase)`

**Deskripsi:**  
Menginisialisasi manajer pembayaran dengan koneksi database.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `manajer_db` | ManajerDatabase | Instance manager database |

### 5.2 Tampilan Metode Pembayaran

#### Method: `tampilkan_metode_pembayaran(self) -> None`

**Deskripsi:**  
Menampilkan daftar metode pembayaran yang tersedia.

**Format Output:**
```
=== Metode Pembayaran Tersedia ===
1. Tunai
2. QRIS
==================================
```

### 5.3 Proses Pembayaran Tunai

#### Method: `proses_pembayaran_tunai(self, total_harga: int) -> Tuple[bool, str]`

**Deskripsi:**  
Menangani proses pembayaran tunai dan perhitungan kembalian.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `total_harga` | int | Total yang harus dibayar |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| Tuple[bool, str] | (Status sukses, Metode pembayaran) |

**Proses Detail:**
1. Menerima input uang dari pelanggan
2. Memvalidasi jumlah pembayaran
3. Menghitung kembalian
4. Menangani pembatalan

**Contoh Penggunaan:**
```python
sukses, metode = manajer_pembayaran.proses_pembayaran_tunai(50000)
if sukses:
    print(f"Pembayaran {metode} berhasil")
```

### 5.4 Proses Pembayaran QRIS

#### Method: `generate_random_string(self, length: int = 10) -> str`

**Deskripsi:**  
Menghasilkan string acak untuk referensi QR.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `length` | int | Panjang string yang diinginkan |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| str | String acak dengan panjang tertentu |

#### Method: `generate_qr(self, data: str) -> None`

**Deskripsi:**  
Membuat dan menampilkan QR code dalam format ASCII.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `data` | str | Data yang akan dikodekan dalam QR |

**Proses Detail:**
1. Membuat objek QR Code
2. Mengatur parameter QR
3. Menambahkan data
4. Menampilkan dalam format ASCII

#### Method: `proses_pembayaran_qris(self, total_harga: int) -> Tuple[bool, str]`

**Deskripsi:**  
Menangani proses pembayaran menggunakan QRIS.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `total_harga` | int | Total yang harus dibayar |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| Tuple[bool, str] | (Status sukses, "QRIS") |

**Proses Detail:**
1. Menghasilkan referensi ID unik
2. Membuat URL data QR
3. Menampilkan QR code
4. Mencatat transaksi di database
5. Menunggu konfirmasi pembayaran
6. Menangani timeout

## 6. Manajer Admin (ManajerAdmin)

### 6.1 Inisialisasi

#### Method: `__init__(self, manajer_db: ManajerDatabase)`

**Deskripsi:**  
Menginisialisasi manajer admin dengan koneksi database.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `manajer_db` | ManajerDatabase | Instance manager database |

### 6.2 Autentikasi Admin

#### Method: `autentikasi_admin(self) -> bool`

**Deskripsi:**  
Memvalidasi kredensial administrator.

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| bool | Status autentikasi berhasil/gagal |

**Proses Detail:**
1. Memberikan 5 kesempatan login
2. Memvalidasi input kode admin
3. Menangani pembatalan
4. Mencatat percobaan gagal

**Contoh Penggunaan:**
```python
if manajer_admin.autentikasi_admin():
    print("Login admin berhasil")
else:
    print("Login gagal atau dibatalkan")
```

### 6.3 Manajemen Stok

#### Method: `restock_kopi(self) -> None`

**Deskripsi:**  
Menangani proses penambahan stok kopi.

**Proses Detail:**
1. Menampilkan daftar kopi
2. Meminta pilihan kopi untuk restock
3. Memvalidasi jumlah restock
4. Mengupdate stok di database
5. Memberikan konfirmasi

**Format Tampilan:**
```
==== Daftar Kopi ====
1. Espresso - Stok: 20
2. Latte - Stok: 15
=====================
```

### 6.4 Manajemen Bahan Tambahan

#### Method: `restock_bahan_tambahan(self) -> None`

**Deskripsi:**  
Menangani proses penambahan stok bahan tambahan.

**Proses Detail:**
1. Menampilkan daftar bahan
2. Meminta pilihan bahan untuk restock
3. Memvalidasi jumlah restock
4. Mengupdate stok di database
5. Memberikan konfirmasi

**Format Tampilan:**
```
==== Daftar Bahan Tambahan ====
1. Gula - Stok: 100
2. Susu - Stok: 80
3. Krimer - Stok: 90
4. Cokelat - Stok: 70
================================
```

### 6.5 Manajemen Keamanan

#### Method: `ganti_kode_admin(self) -> None`

**Deskripsi:**  
Menangani proses perubahan kode admin.

**Proses Detail:**
1. Memvalidasi kode baru
2. Menyimpan kode ke file
3. Mengupdate cache
4. Memberikan konfirmasi

**Validasi Kode:**
- Harus berupa angka
- Harus positif
- Tidak boleh sama dengan kode lama

### 6.6 Manajemen Sistem

#### Method: `matikan_program(self) -> None`

**Deskripsi:**  
Menangani proses mematikan sistem dengan aman.

**Proses Detail:**
1. Menyimpan perubahan terakhir
2. Sinkronisasi database
3. Membersihkan resources
4. Menutup koneksi
5. Mengakhiri program

## 7. Manajer Pesanan Online (ManajerPesananOnline)

### 7.1 Inisialisasi

#### Method: `__init__(self, manajer_db: ManajerDatabase, manajer_pesanan: ManajerPesanan)`

**Deskripsi:**  
Menginisialisasi manajer pesanan online.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `manajer_db` | ManajerDatabase | Instance manager database |
| `manajer_pesanan` | ManajerPesanan | Instance manager pesanan |

### 7.2 Pemindaian QR

#### Method: `scan_qr(self) -> None`

**Deskripsi:**  
Menangani proses pemindaian dan validasi QR code.

**Proses Detail:**
1. Inisialisasi pemindai QR
2. Membuka kamera
3. Memproses pemindaian
4. Memvalidasi kode QR
5. Memproses pesanan
6. Mengupdate status

**Komponen Pemindaian:**
```python
detektor = cv2.QRCodeDetector()
cap = cv2.VideoCapture(0)
```

**Status Pesanan:**
- Pending: Menunggu pemrosesan
- Selesai: Pesanan telah diproses
- Expired: Waktu pemesanan habis

## 8. Aplikasi Web (AplikasiWeb)

### 8.1 Inisialisasi

#### Method: `__init__(self, manajer_db: ManajerDatabase)`

**Deskripsi:**  
Menginisialisasi aplikasi web Flask dengan konfigurasi dan route yang diperlukan.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `manajer_db` | ManajerDatabase | Instance manager database |

**Atribut yang Diinisialisasi:**

| Atribut | Tipe Data | Deskripsi |
|---------|-----------|-----------|
| `app` | Flask | Instance aplikasi Flask |
| `manajer_db` | ManajerDatabase | Referensi ke database manager |

### 8.2 Routing dan Handler

#### Method: `setup_routes(self)`

**Deskripsi:**  
Mengatur semua route dan handler untuk aplikasi web.

**Route yang Diatur:**

| Route | Method | Fungsi | Deskripsi |
|-------|---------|---------|-----------|
| `/search` | GET | `cari()` | Menampilkan halaman loading |
| `/proses_cari` | GET | `proses_cari()` | Memproses pencarian referensi |
| `/berhasil` | GET | `berhasil()` | Menampilkan halaman sukses |
| `/gagal` | GET | `gagal()` | Menampilkan halaman gagal |
| `/404` | - | `halaman_tidak_ditemukan()` | Handler error 404 |

### 8.3 Manajemen Data

#### Method: `ambil_data(self, manajer_db: ManajerDatabase, ref_id: str) -> Optional[DataRefID]`

**Deskripsi:**  
Mengambil data pembayaran berdasarkan referensi ID.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `manajer_db` | ManajerDatabase | Instance database manager |
| `ref_id` | str | ID referensi pembayaran |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| Optional[DataRefID] | Data referensi atau None jika tidak ditemukan |

#### Method: `update_status(self, manajer_db: ManajerDatabase, ref_id: str, status_baru: str) -> bool`

**Deskripsi:**  
Mengupdate status pembayaran di cache dan database.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `manajer_db` | ManajerDatabase | Instance database manager |
| `ref_id` | str | ID referensi pembayaran |
| `status_baru` | str | Status yang akan diset |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| bool | Status update berhasil/gagal |

### 8.4 Template Filters

#### Filter: `rupiah`

**Deskripsi:**  
Filter Jinja2 untuk memformat angka ke format rupiah.

**Contoh Penggunaan:**
```html
<p>Total: Rp{{ total_harga|rupiah }}</p>
```

**Output Format:**
- Input: 50000
- Output: "50.000"

## 9. Fungsi Utilitas

### 9.1 Input Dengan Timeout

#### Function: `input_dengan_timeout(manajer_db: ManajerDatabase, teks: str, batas_waktu: int = Konfigurasi.DURASI_TIMEOUT) -> str`

**Deskripsi:**  
Fungsi untuk mengambil input dengan batas waktu.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `manajer_db` | ManajerDatabase | Instance database manager |
| `teks` | str | Prompt untuk input |
| `batas_waktu` | int | Durasi timeout dalam detik |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| str | Input pengguna atau 'timeout' jika waktu habis |

**Penanganan Timeout:**
1. Menampilkan pesan timeout
2. Kembali ke menu utama
3. Menyimpan perubahan jika ada

**Contoh Penggunaan:**
```python
try:
    pilihan = input_dengan_timeout(
        manajer_db,
        "Pilih opsi (1-5): ",
        60  # timeout 60 detik
    )
except TimeoutOccurred:
    print("Waktu input habis")
```

## 10. Main Program

### 10.1 Fungsi Utilitas Main

#### Function: `cek_webservice(host: str, port: int) -> bool`

**Deskripsi:**  
Memeriksa ketersediaan webservice.

**Parameter:**

| Parameter | Tipe Data | Deskripsi |
|-----------|-----------|-----------|
| `host` | str | Hostname webservice |
| `port` | int | Port webservice |

**Return Value:**

| Tipe Data | Deskripsi |
|-----------|-----------|
| bool | Status webservice aktif/nonaktif |

### 10.2 Fungsi Main

#### Function: `main()`

**Deskripsi:**  
Fungsi utama yang menjalankan sistem mesin kopi.

**Proses Detail:**
1. Inisialisasi database manager
2. Menjalankan webservice
3. Memverifikasi koneksi
4. Memulai simulasi mesin kopi
5. Menangani interrupt

**Penanganan Error:**
1. Koneksi database gagal
2. Webservice gagal start
3. Keyboard interrupt
4. Runtime errors

## 11. Error Handling dan Logging

### 11.1 Struktur Error Handling

**Tipe Error yang Ditangani:**
1. Database Connection Errors
2. Input/Output Errors
3. Timeout Errors
4. Authentication Errors
5. Network Errors

**Format Log Error:**
```python
try:
    # Operasi database/network
except Exception as e:
    print(f"⚠ - Terjadi kesalahan: {str(e)}")
    # Logging atau recovery steps
```

### 11.2 Recovery Mechanisms

**Automatic Recovery Steps:**
1. Reconnection attempts
2. Cache fallback
3. Graceful degradation
4. User notification
5. State preservation

## 12. Konfigurasi Sistem

### 12.1 Kelas Konfigurasi

**Lokasi File:** `credentials/config.py`

#### Konstanta Sistem

| Konstanta | Tipe Data | Nilai Default | Deskripsi |
|-----------|-----------|---------------|-----------|
| `FILE_AKUN_LAYANAN` | str | "credentials/coffee-machine-ct24-ab01b40294eb.json" | Path ke file kredensial Google Service Account |
| `ID_SHEET` | str | "1aIdU_E6X5ZI0xcS6caC1SfajpIycn97aed0or6YxxXM" | ID Google Spreadsheet untuk database |
| `KODE_ADMIN_DEFAULT` | int | 1234567890 | Kode administrator default |
| `PORT` | int | 5000 | Port untuk webservice Flask |
| `DURASI_TIMEOUT` | int | 60 | Timeout untuk input pengguna (detik) |
| `INTERVAL_SINKRONISASI` | int | 300 | Interval sinkronisasi database (detik) |
| `QRIS_TIMEOUT` | int | 300 | Timeout pembayaran QRIS (detik) |

### 12.2 Arsitektur Sistem

#### Komponen Utama:
1. **Frontend Layer**
   - Antarmuka CLI untuk interaksi pengguna
   - Web interface untuk pembayaran QRIS
   - QR Code scanner interface

2. **Business Logic Layer**
   - Manajer Pesanan: Pemrosesan pesanan
   - Manajer Pembayaran: Handling transaksi
   - Manajer Admin: Fungsi administratif
   - Manajer Menu: Pengelolaan menu

3. **Data Layer**
   - Google Sheets sebagai database
   - Local caching system
   - File system untuk konfigurasi

4. **Integration Layer**
   - Google Sheets API
   - QR Code processing
   - Payment gateway interface

#### Alur Data:
```
User Input → Business Logic → Cache → Database Sync → Google Sheets
                ↓
            Payment Processing
                ↓
            Order Fulfillment
```

### 12.3 Persyaratan Sistem

#### Dependencies:
```
gspread==5.10.0
google-auth==2.22.0
Flask==2.0.1
opencv-python==4.8.0
qrcode==7.3
inputimeout==1.0.4
```

#### Sistem Operasi yang Didukung:
- Windows 10/11
- Linux (Ubuntu 20.04+)
- macOS (10.15+)

#### Hardware Requirements:
- Minimum 2GB RAM
- Webcam (untuk QR scanning)
- Koneksi internet stabil

### 12.4 Panduan Deployment

1. **Persiapan Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Konfigurasi Credentials:**
   - Letakkan file service account di `credentials/`
   - Update `config.py` sesuai kebutuhan

3. **Menjalankan Sistem:**
   ```bash
   python main.py
   ```

4. **Monitoring:**
   - Cek log files di `logs/`
   - Monitor memory usage
   - Pantau koneksi database

### 12.5 Maintenance

#### Backup Procedure:
1. Daily backup configurasi
2. Weekly backup database
3. Monthly system check

#### Update Procedure:
1. Backup current state
2. Apply updates
3. Test functionality
4. Roll back if needed