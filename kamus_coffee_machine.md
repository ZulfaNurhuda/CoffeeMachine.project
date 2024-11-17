# **KAMUS PEMROGRAMAN ALGORITMA COFFEE MACHINE**

## **Daftar Isi**
1. [Global Variables](#global-variables)
2. [Data Classes](#data-classes)
3. [Classes dan Atributnya](#classes-dan-atributnya)
    - [DatabaseManager](#databasemanager)
    - [MenuManager](#menumanager)
    - [PesananManager](#pesananmanager)
    - [PembayaranManager](#pembayaranmanager)
    - [ScanQR](#scanqr)
    - [RestockKopi](#restockkopi)
    - [MesinKopi](#mesinkopi)
4. [Fungsi dan Variabel Lokal](#fungsi-dan-variabel-lokal)
    - [`input_dengan_timeout`](#input_dengan_timeout)
    - [`DatabaseManager.get_column_indices`](#databasemanagerget_column_indices)
    - [`DatabaseManager.ambil_data_kopi`](#databasemanagerambil_data_kopi)
    - [`DatabaseManager.update_stok`](#databasemanagerupdate_stok)
    - [`DatabaseManager.catat_penjualan`](#databasemanagercatat_penjualan)
    - [`DatabaseManager.restock_kopi`](#databasemanagerrestock_kopi)
    - [`MenuManager.assign_kopi_numbers`](#menumanagerassign_kopi_numbers)
    - [`MenuManager.tampilkan_menu_kopi`](#menumanagertampilkan_menu_kopi)
    - [`PesananManager.pilih_suhu`](#pesananmanagerpilih_suhu)
    - [`PesananManager.atur_jumlah`](#pesananmanageratur_jumlah)
    - [`PesananManager.pilih_komposisi`](#pesananmanagerpilih_komposisi)
    - [`PesananManager.pesan_jumlah`](#pesananmanagerpesan_jumlah)
    - [`PesananManager.tambah_pesanan`](#pesananmanagertambah_pesanan)
    - [`PesananManager.ringkasan_pesanan`](#pesananmanagerringkasan_pesanan)
    - [`PesananManager.pilih_kopi`](#pesananmanagerpilih_kopi)
    - [`PembayaranManager.proses_pembayaran_tunai`](#pembayaranmanagerproses_pembayaran_tunai)
    - [`PembayaranManager.generate_random_string`](#pembayaranmanagergenerate_random_string)
    - [`PembayaranManager.generate_qr_terminal`](#pembayaranmanagergenerate_qr_terminal)
    - [`PembayaranManager.proses_pembayaran_qris`](#pembayaranmanagerproses_pembayaran_qris)
    - [`PembayaranManager.proses_pembayaran`](#pembayaranmanagerproses_pembayaran)
    - [`ScanQR.scan_qr`](#scanqrscan_qr)
    - [`RestockKopi.restock_kopi`](#restockkopirestock_kopi)
    - [`MesinKopi.shutdown_program`](#mesinkopishutdown_program)
    - [`MesinKopi.coffee_machine_simulasi`](#mesinkopicoffee_machine_simulasi)
5. [Variabel Lainnya](#variabel-lainnya)

---

## **Global Variables**

| Variabel                      | Tipe Data  |
|-------------------------------|------------|
| `Config.SHEET_ID`             | `string`   |
| `Config.SERVICE_ACCOUNT_FILE` | `string`   |
| `Config.KODE_ADMIN`           | `integer`  |
| `Config.TIMEOUT_DURATION`     | `integer`  |

---

## **Data Classes**

| Variabel                | Tipe Data    |
|-------------------------|--------------|
| `KopiData.nama`         | `string`     |
| `KopiData.harga`        | `integer`    |
| `KopiData.sisa`         | `integer`    |
| `KopiData.row_number`   | `integer`    |
| `KopiData.nomor`        | `integer`    |
| `Komposisi.gula`        | `integer`    |
| `Komposisi.krimer`      | `integer`    |
| `Komposisi.susu`        | `integer`    |
| `Komposisi.cokelat`     | `integer`    |
| `PesananItem.kopi`      | `KopiData`   |
| `PesananItem.jumlah`    | `integer`    |
| `PesananItem.suhu`      | `string`     |
| `PesananItem.komposisi` | `Komposisi`  |

---

## **Classes dan Atributnya**

> ### **DatabaseManager**

| Variabel                     | Tipe Data                                 |
|------------------------------|-------------------------------------------|
| `DatabaseManager.persediaan` | `gspread.Worksheet`                       |
| `DatabaseManager.penjualan`  | `gspread.Worksheet`                       |
| `DatabaseManager.antrian_qr` | `gspread.Worksheet`                       |
| `DatabaseManager.kredensial` | `Credentials`                             |
| `DatabaseManager.client`     | `gspread.Client`                          |
| `DatabaseManager.lembar_kerja` | `gspread.Worksheet`                     |

> ### **MenuManager**

| Variabel                  | Tipe Data                |
|---------------------------|--------------------------|
| `MenuManager.daftar_kopi` | `Dict[string, KopiData]` |

> ### **PesananManager**

| Variabel                      | Tipe Data                |
|-------------------------------|--------------------------|
| `PesananManager.daftar_kopi`  | `Dict[string, KopiData]` |
| `PesananManager.menu_manager` | `MenuManager`            |

> ### **PembayaranManager**

| Variabel              | Tipe Data |
|-----------------------|-----------|
| *Tidak ada atribut instance* |           |

> ### **ScanQR**

| Variabel                 | Tipe Data                 |
|--------------------------|---------------------------|
| `ScanQR.db_manager`      | `DatabaseManager`         |
| `ScanQR.pesanan_manager` | `PesananManager`          |
| `ScanQR.daftar_kopi`     | `Dict[string, KopiData]`  |
| `ScanQR.menu_manager`    | `MenuManager`             |

> ### **RestockKopi**

| Variabel                   | Tipe Data                |
|----------------------------|--------------------------|
| `RestockKopi.db_manager`   | `DatabaseManager`        |
| `RestockKopi.menu_manager` | `MenuManager`            |
| `RestockKopi.daftar_kopi`  | `Dict[string, KopiData]` |

> ### **MesinKopi**

| Variabel                        | Tipe Data                |
|---------------------------------|--------------------------|
| `MesinKopi.db_manager`          | `DatabaseManager`        |
| `MesinKopi.daftar_kopi`         | `Dict[string, KopiData]` |
| `MesinKopi.menu_manager`        | `MenuManager`            |
| `MesinKopi.pesanan_manager`     | `PesananManager`         |
| `MesinKopi.pembayaran_manager`  | `PembayaranManager`     |
| `MesinKopi.scan_qr_manager`     | `ScanQR`                 |
| `MesinKopi.restock_manager`     | `RestockKopi`            |

---

## **Fungsi dan Variabel Lokal**

> ### `input_dengan_timeout`

| Variabel        | Tipe Data |
|-----------------|-----------|
| `teks`          | `string`  |
| `batas_waktu`   | `integer` |
| `mesin_kopi`    | `MesinKopi`|

> ### `DatabaseManager.get_column_indices`

| Variabel | Tipe Data      |
|----------|----------------|
| `header` | `List[string]` |
| `name`   | `string`       |
| `idx`    | `integer`      |

> ### `DatabaseManager.ambil_data_kopi`

| Variabel   | Tipe Data    |
|------------|--------------|
| `data_kopi`| `List[Dict]`  |
| `baris`    | `Dict`        |
| `i`        | `integer`     |

> ### `DatabaseManager.update_stok`

| Variabel          | Tipe Data |
|-------------------|-----------|
| `kopi`            | `KopiData`|
| `jumlah_terjual`  | `integer` |
| `stok_baru`       | `integer` |

> ### `DatabaseManager.catat_penjualan`

| Variabel            | Tipe Data      |
|---------------------|----------------|
| `item_pesanan`      | `PesananItem`  |
| `metode_pembayaran` | `string`       |
| `komposisi_all`     | `string`       |
| `row`               | `List`          |

> ### `DatabaseManager.restock_kopi`

| Variabel         | Tipe Data |
|------------------|-----------|
| `kopi`           | `KopiData`|
| `jumlah_restock` | `integer` |

> ### `MenuManager.assign_kopi_numbers`

| Variabel | Tipe Data |
|----------|-----------|
| `nomor`  | `integer` |
| `kopi`   | `KopiData`|

> ### `MenuManager.tampilkan_menu_kopi`

| Variabel | Tipe Data |
|----------|-----------|
| `kopi`   | `KopiData`|

> ### `PesananManager.pilih_suhu`

| Variabel    | Tipe Data |
|-------------|-----------|
| `nama_kopi` | `string`  |
| `suhu_input`| `string`  |
| `suhu`      | `string`  |

> ### `PesananManager.atur_jumlah`

| Variabel       | Tipe Data |
|----------------|-----------|
| `tipe_bahan`   | `string`  |
| `jumlah_input` | `string`  |
| `jumlah`       | `integer` |

> ### `PesananManager.pilih_komposisi`

| Variabel  | Tipe Data |
|-----------|-----------|
| `gula`    | `integer` |
| `krimer`  | `integer` |
| `susu`    | `integer` |
| `cokelat` | `integer` |

> ### `PesananManager.pesan_jumlah`

| Variabel       | Tipe Data |
|----------------|-----------|
| `jumlah_input` | `string`  |
| `jumlah`       | `integer` |

> ### `PesananManager.tambah_pesanan`

| Variabel       | Tipe Data           |
|----------------|---------------------|
| `data_pesanan` | `List[PesananItem]` |
| `kopi`         | `KopiData`          |
| `suhu`         | `string`            |
| `komposisi`    | `Komposisi`         |
| `jumlah`       | `integer`           |
| `existing`     | `PesananItem`       |

> ### `PesananManager.ringkasan_pesanan`

| Variabel               | Tipe Data           |
|------------------------|---------------------|
| `pesanan`              | `List[PesananItem]` |
| `new_line`             | `integer`           |
| `ringkasan_pesanan_teks` | `string`         |
| `total_harga`          | `integer`           |
| `idx`                  | `integer`           |

> ### `PesananManager.pilih_kopi`

| Variabel             | Tipe Data                |
|----------------------|--------------------------|
| `kopi_nama_by_nomor` | `Dict[integer, KopiData]`|
| `data_pesanan`       | `List[PesananItem]`      |
| `pesanan_ke`         | `integer`                |
| `pilihan`            | `string`                 |
| `pilihan_int`        | `integer`                |
| `kopi`               | `KopiData`               |
| `suhu`               | `string`                 |
| `komposisi`          | `Komposisi`              |
| `jumlah`             | `integer`                |
| `lagi`               | `string`                 |

> ### `PembayaranManager.proses_pembayaran_tunai`

| Variabel        | Tipe Data |
|-----------------|-----------|
| `total_harga`   | `integer` |
| `total_dibayar` | `integer` |
| `uang_input`    | `string`  |
| `uang`          | `integer` |
| `kembalian`     | `integer` |
| `kurang`        | `integer` |

> ### `PembayaranManager.generate_random_string`

| Variabel | Tipe Data |
|----------|-----------|
| `length` | `integer` |

> ### `PembayaranManager.generate_qr_terminal`

| Variabel | Tipe Data |
|----------|-----------|
| `data`   | `string`  |

> ### `PembayaranManager.proses_pembayaran_qris`

| Variabel            | Tipe Data |
|---------------------|-----------|
| `total_harga`       | `integer` |
| `code_to_qr`        | `string`  |
| `code_from_user`    | `string`  |

> ### `PembayaranManager.proses_pembayaran`

| Variabel                  | Tipe Data       |
|---------------------------|-----------------|
| `total_harga`             | `integer`       |
| `metode_pembayaran_input` | `string`        |
| `metode_pembayaran`       | `integer`       |
| `proses_pembayaran_sukses`| `boolean`       |
| `proses_pembayaran_metode`| `string`        |

> ### `ScanQR.scan_qr`

| Variabel                | Tipe Data               |
|-------------------------|-------------------------|
| `detector`              | `cv2.QRCodeDetector`    |
| `cap`                   | `cv2.VideoCapture`      |
| `qr_code`               | `string`                |
| `data_qr`               | `List[Dict]`            |
| `antrian_qr_columns`    | `Dict[string, integer]` |
| `persediaan_columns`    | `Dict[string, integer]` |
| `pesanan`               | `List[PesananItem]`     |
| `habis`                 | `boolean`               |
| `valid`                 | `boolean`               |
| `index`                 | `integer`               |
| `kopi_nama`             | `string`                |
| `jumlah_dipesan`        | `integer`               |
| `stok_saat_ini`         | `integer`               |
| `jumlah_dapat_diproses` | `integer`               |
| `komposisi`             | `Komposisi`             |

> ### `RestockKopi.restock_kopi`

| Variabel               | Tipe Data |
|------------------------|-----------|
| `max_attempts`         | `integer` |
| `attempts`             | `integer` |
| `kode_admin_input`     | `string`  |
| `kode_admin`           | `integer` |
| `pilihan_kopi_input`   | `string`  |
| `pilihan_kopi`         | `integer` |
| `jumlah_restock_input` | `string`  |
| `jumlah_restock`       | `integer` |
| `lagi_input`           | `string`  |

> ### `MesinKopi.shutdown_program`

| Variabel           | Tipe Data |
|--------------------|-----------|
| `max_attempts`     | `integer` |
| `attempts`         | `integer` |
| `kode_admin_input` | `string`  |
| `kode_admin`       | `integer` |

> ### `MesinKopi.coffee_machine_simulasi`

| Variabel             | Tipe Data           |
|----------------------|---------------------|
| `pilihan`            | `string`            |
| `pesanan`            | `List[PesananItem]` |
| `stok_cukup`         | `boolean`           |
| `total_harga`        | `integer`           |
| `pembayaran_sukses`  | `boolean`           |
| `metode`             | `string`            |
| `pilihan_input`      | `string`            |
| `mesin_kopi`         | `MesinKopi`         |
| `barik`              | `Dict`               |
| `pilihan_int`        | `integer`           |

---

## Variabel Lainnya

| Variabel                 | Tipe Data                                           |
|--------------------------|-----------------------------------------------------|
| `sys`                    | `module`                                            |
| `os`                     | `module`                                            |
| `random`                 | `module`                                            |
| `string`                 | `module`                                            |
| `dataclass`              | `decorator`                                         |
| `Dict`                   | `typing.Dict`                                       |
| `List`                   | `typing.List`                                       |
| `Tuple`                  | `typing.Tuple`                                      |
| `Optional`               | `typing.Optional`                                   |
| `lru_cache`              | `functools.lru_cache`                               |
| `gspread`                | `module`                                            |
| `Credentials`            | `google.oauth2.service_account.Credentials`        |
| `inputimeout`            | `inputimeout.inputimeout`                           |
| `TimeoutOccurred`        | `inputimeout.TimeoutOccurred`                       |
| `cv2`                    | `module`                                            |
| `qrcode_terminal`        | `module`                                            |
| `i`                      | `integer`                                           |
| `baris`                  | `Dict`                                               |
| `ret`                    | `boolean`                                           |
| `frame`                  | `numpy.ndarray`                                     |
| `data`                   | `string`                                            |
| `header`                 | `List[string]`                                      |
| `name`                   | `string`                                            |
| `idx`                    | `integer`                                           |
| `total_dibayar`          | `integer`                                           |
| `uang_input`             | `string`                                            |
| `uang`                   | `integer`                                           |
| `kembalian`              | `integer`                                           |
| `kurang`                 | `integer`                                           |
| `code_to_qr`             | `string`                                            |
| `code_from_user`         | `string`                                            |
| `length`                 | `integer`                                           |
| `data_qr`                | `List[Dict]`                                        |
| `antrian_qr_columns`     | `Dict[string, integer]`                             |
| `persediaan_columns`     | `Dict[string, integer]`                             |
| `pesanan`                | `List[PesananItem]`                                 |
| `habis`                  | `boolean`                                           |
| `valid`                  | `boolean`                                           |
| `index`                  | `integer`                                           |
| `kopi_nama`              | `string`                                            |
| `jumlah_dipesan`         | `integer`                                           |
| `stok_saat_ini`          | `integer`                                           |
| `jumlah_dapat_diproses`  | `integer`                                           |
| `sisa_pesanan`           | `integer`                                           |
| `pilihan`                | `string`                                            |
| `pilihan_int`            | `integer`                                           |
| `lagi`                   | `string`                                            |
| `pilihan_kopi_input`     | `string`                                            |
| `pilihan_kopi`           | `integer`                                           |
| `jumlah_restock_input`   | `string`                                            |
| `jumlah_restock`         | `integer`                                           |
| `lagi_input`             | `string`                                            |
| `kode_admin_input`       | `string`                                            |
| `kode_admin`             | `integer`                                           |
| `mesin_kopi`             | `MesinKopi`                                         |

---

## **Keterangan:**

- **Global Variables**: Variabel yang didefinisikan di luar kelas dan fungsi, biasanya sebagai konfigurasi atau konstanta.
  
- **Data Classes**: Kelas yang digunakan untuk menyimpan data dengan atribut yang telah ditentukan.
  
- **Classes dan Atributnya**: Variabel yang merupakan atribut dari kelas tertentu, baik atribut kelas maupun atribut instance.
  
- **Fungsi dan Variabel Lokal**: Variabel yang digunakan di dalam fungsi atau metode, termasuk parameter dan variabel lokal. Ini mencakup variabel loop seperti `i`, `baris`, `ret`, `frame`, dan lainnya.
  
- **Variabel Lainnya**: Variabel yang merujuk pada modul atau objek eksternal yang diimpor.

---

## **Catatan:**

- Beberapa variabel memiliki tipe data yang lebih kompleks atau spesifik berdasarkan konteks penggunaannya dalam kode.
  
- Tipe data seperti `Dict[string, KopiData]` atau `List[PesananItem]` menunjukkan struktur data yang mengandung objek dari kelas tertentu.
  
- Modul eksternal seperti `gspread`, `cv2`, atau `qrcode_terminal` disebutkan sebagai tipe data `module` atau sesuai dengan objek yang diimpor dari modul tersebut.
  
- Variabel seperti `i`, `baris`, `ret`, `frame`, dan lainnya adalah variabel lokal yang digunakan dalam loop atau operasi tertentu dalam fungsi atau metode.