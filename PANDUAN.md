# PANDUAN PEMAKAIAN
## Program Pembukuan Kantin Koperasi — versi 1.0.0

Panduan ini ditulis untuk pengurus koperasi, bukan untuk programmer.
Tidak perlu paham komputer secara mendalam untuk memakainya.

---

## DAFTAR ISI

1. [Memasang program](#1-memasang-program)
2. [Mengenal tampilan](#2-mengenal-tampilan)
3. [Persiapan awal (sekali saja)](#3-persiapan-awal-sekali-saja)
4. [Memasukkan transaksi harian](#4-memasukkan-transaksi-harian)
5. [Mengimpor jurnal dari Excel](#5-mengimpor-jurnal-dari-excel)
6. [Melihat dan mencetak laporan](#6-melihat-dan-mencetak-laporan)
7. [Stock opname dan HPP](#7-stock-opname-dan-hpp)
8. [Tutup buku ke bulan berikutnya](#8-tutup-buku-ke-bulan-berikutnya)
9. [Mencadangkan dan memulihkan data](#9-mencadangkan-dan-memulihkan-data)
10. [Alur kerja bulanan (ringkas)](#10-alur-kerja-bulanan-ringkas)
11. [Contoh jurnal transaksi kantin](#11-contoh-jurnal-transaksi-kantin)
12. [Tanya jawab dan mengatasi masalah](#12-tanya-jawab-dan-mengatasi-masalah)

---

## 1. MEMASANG PROGRAM

Ada tiga cara. Pilih salah satu yang paling sesuai.

### Cara A — memakai installer Windows (disarankan untuk komputer tetap)

1. Klik dua kali `KantinKoperasi_Setup_1.0.0.exe`.
2. Bila Windows menampilkan peringatan biru **"Windows protected your PC"**,
   klik **More info** → **Run anyway**. Peringatan ini muncul karena program
   belum membeli sertifikat digital, bukan karena berisi virus.
3. Ikuti langkahnya sampai selesai (cukup klik **Next** terus).
4. Ikon **Pembukuan Kantin** akan muncul di Desktop.

### Cara B — versi portable (flashdisk)

Salin seluruh folder `PembukuanKantin-Portable` ke flashdisk, lalu klik dua
kali `KantinKoperasi.exe`. Tidak ada proses pemasangan sama sekali.

Keunggulannya: **seluruh data ikut di dalam folder itu**. Flashdisk bisa
dibawa ke komputer mana pun dan pembukuan tetap lanjut dari posisi terakhir.
Komputer yang dipinjam tidak ditulisi apa pun.

### Cara C — di komputer Mac

Buka berkas `.dmg`, seret ikon aplikasi ke folder Applications. Atau, untuk
versi portable, salin seluruh folder portable ke tempat yang dikehendaki.

**Pembukaan pertama di Mac:** klik **kanan** ikon aplikasi → pilih **Open** →
tekan **Open** sekali lagi pada kotak peringatan. Cukup sekali; berikutnya
bisa dibuka dengan klik dua kali biasa. Peringatan itu muncul karena aplikasi
belum didaftarkan ke Apple, bukan karena berisi virus.

### Di mana data saya disimpan?

Tergantung mode yang dipakai. Lihat lewat menu **Berkas → Lokasi Data** —
mode yang sedang aktif tertulis di baris pertama.

**Mode portable** — data ada di folder `Data` di sebelah aplikasi:

```
PembukuanKantin-Portable\Data\
```

**Mode terpasang** — data ada di folder pengguna komputer:

```
Windows : C:\Users\<nama-pengguna>\AppData\Local\KantinKoperasi\
macOS   : ~/Library/Application Support/KantinKoperasi/
```

Isinya sama: `kantin.db` (basis data), folder `backup` (cadangan otomatis),
dan folder `Laporan` (hasil cetak PDF/Excel).

Pada mode terpasang, **data tidak ikut terhapus** walaupun program dihapus
atau diperbarui.

### Berpindah antar mode

Berkas programnya sama persis; yang menentukan hanya ada-tidaknya penanda.

- **Jadikan portable:** buat folder bernama `Data` di sebelah aplikasi.
- **Kembali ke terpasang:** hapus folder `Data` dan berkas `portable.txt`.

Memindahkan pembukuan yang sudah berjalan ke mode portable: buat folder
`Data`, lalu salin berkas `kantin.db` dari folder lama ke dalamnya.

---

## 2. MENGENAL TAMPILAN

Di bagian atas jendela terdapat **pemilih periode** (misalnya "Januari 2026").
Semua yang ditampilkan di layar mengikuti periode yang sedang dipilih.

Program terdiri dari 8 tab:

| Tab | Fungsi |
|-----|--------|
| **Beranda** | Ringkasan cepat: kas, bank, persediaan, penjualan, SHU, total aktiva |
| **Jurnal Transaksi** | Memasukkan, mengubah, menghapus, dan mengimpor transaksi |
| **Buku Besar** | Mutasi per akun, atau rekap saldo seluruh akun |
| **Neraca Lajur** | Kertas kerja 12 kolom + tempat mengisi stock opname |
| **Laporan Keuangan** | Laba Rugi, Perubahan Modal, Neraca, Arus Kas, Rekap Penjualan |
| **Daftar Akun** | Daftar kode akun (COA) — bisa ditambah/diubah |
| **Saldo Awal** | Saldo pembuka periode pertama |
| **Tutup Buku** | Mengunci bulan berjalan dan membuka bulan berikutnya |

Tombol yang sering dipakai selalu berada di bagian atas tiap tab.

---

## 3. PERSIAPAN AWAL (SEKALI SAJA)

Program dibuka dengan **26 akun** siap pakai untuk usaha kantin/toko, tanpa
angka apa pun. Tiga hal berikut diisi sekali di awal:

1. **Menu Berkas → Pengaturan** — isi nama koperasi, unit usaha, alamat, kota,
   nama ketua, dan nama bendahara. Data ini yang tercetak di kop dan kolom
   tanda tangan setiap laporan PDF.
2. **Tab Daftar Akun** — periksa apakah ada akun yang perlu ditambah, misalnya
   akun beban baru. Tekan **Tambah Akun**.
3. **Tab Saldo Awal** — isi saldo pembuka koperasi per tanggal mulai
   pembukuan: kas, bank, piutang, persediaan, peralatan, utang, simpanan
   anggota, modal, dan laba ditahan. Indikator di bawah tabel harus
   bertuliskan **SEIMBANG** sebelum bisa disimpan.

   Belum tahu angkanya? Ambil dari neraca pembukuan sebelumnya, atau hitung
   fisik: uang kas, saldo rekening, nilai barang di kantin, dan peralatan.

> Saldo awal otomatis terkunci bila periode sebelumnya sudah ditutup buku,
> karena angkanya diambil dari hasil tutup buku, bukan diketik manual.

---

## 4. MEMASUKKAN TRANSAKSI HARIAN

1. Buka tab **Jurnal Transaksi** → klik **Transaksi Baru**.
2. Isi **Tanggal** (klik ikon kalender bila perlu).
3. **No Bukti** terisi otomatis, tapi boleh diganti sesuai nomor bukti fisik.
4. **Jenis**: pilih `JU` untuk transaksi biasa, `AJP` untuk jurnal penyesuaian
   (penyusutan, pemakaian perlengkapan, dan sejenisnya).
5. Isi **Keterangan** singkat namun jelas.
6. Pada tabel rincian, pilih akun lalu isi kolom **Debit** ATAU **Kredit**
   (jangan keduanya pada baris yang sama). Klik **+ Baris** bila butuh baris
   tambahan.
7. Perhatikan indikator di bawah tabel. Tombol simpan baru aktif bila sudah
   tertulis **BALANCE** (total debit = total kredit).
8. Klik **Simpan**, atau **Simpan & Input Lagi** untuk langsung mengisi
   transaksi berikutnya.

### Tombol Transaksi Cepat

Di dalam dialog terdapat 5 tombol pintasan yang langsung mengisikan pasangan
akun yang benar, tinggal ketik nominalnya:

- **Penjualan Tunai** — Kas (D) / Penjualan Kantin (K)
- **Pembelian Tunai** — Pembelian (D) / Kas (K)
- **Bayar Beban** — Beban (D) / Kas (K)
- **Setor ke Bank** — Bank (D) / Kas (K)
- **Terima Piutang** — Kas (D) / Piutang (K)

### Mengubah atau menghapus

Klik dua kali baris transaksi untuk mengubah, atau pilih baris lalu tekan
tombol **Hapus**. Transaksi pada periode yang sudah ditutup buku tidak bisa
diubah — buka kembali periodenya terlebih dahulu (lihat bagian 8).

---

## 5. MENGIMPOR JURNAL DARI EXCEL

Cocok bila transaksi sudah dicatat harian di Excel atau di buku kas yang
kemudian diketik massal.

**Langkah:**

1. Tab **Jurnal Transaksi** → klik **Unduh Template**. Simpan berkasnya.
2. Buka berkas template tersebut di Excel. Isi mulai **baris 6**:

   | Kolom | Isi |
   |-------|-----|
   | No Bukti | Nomor bukti. **Baris dengan nomor bukti sama = satu transaksi.** |
   | Tanggal | `DD/MM/YYYY` (contoh `05/03/2026`) atau format tanggal Excel |
   | Kode Akun | Kode akun, misal `111`. Tersedia daftar pilihan (dropdown) |
   | Keterangan | Uraian transaksi |
   | Debit | Isi angka, atau kosongkan/0 |
   | Kredit | Isi angka, atau kosongkan/0 |
   | Jenis | `JU` atau `AJP` |

   Sheet **DaftarAkun** di berkas yang sama memuat seluruh kode akun beserta
   namanya sebagai rujukan.

3. Simpan berkas Excel tersebut.
4. Kembali ke program → klik **Impor Excel** → pilih berkasnya.
5. Program menampilkan **pratinjau**: daftar transaksi yang terbaca dan daftar
   masalah bila ada (akun tidak dikenal, tanggal di luar periode, transaksi
   tidak balance).
6. Bila tidak ada masalah, klik **Impor Sekarang**.

> Impor hanya berjalan bila seluruh transaksi balance dan seluruh kode akun
> dikenali. Berkas `.xlsx`, `.xlsm`, dan `.csv` semuanya bisa dibaca.

Berkas `contoh/Contoh_Impor_Terisi.xlsx` berisi transaksi contoh yang lengkap
(penjualan tunai, penjualan kredit, pembelian, retur, beban, setoran bank,
simpanan wajib, sampai jurnal penyesuaian) — silakan dijadikan acuan. Angkanya
fiktif; sesuaikan juga bulan pada kolom Tanggal dengan periode tujuan.

---

## 6. MELIHAT DAN MENCETAK LAPORAN

Setiap laporan punya tombol **Cetak PDF** di bagian atasnya. Hasil cetak
otomatis memakai kop koperasi, nomor halaman, waktu cetak, dan kolom tanda
tangan ketua serta bendahara.

Laporan yang tersedia:

| Laporan | Letak |
|---------|-------|
| Jurnal Umum | Tab Jurnal Transaksi |
| Buku Besar (per akun) | Tab Buku Besar → mode "Per Akun" |
| Rekap Buku Besar | Tab Buku Besar → mode "Rekap Semua Akun" |
| Neraca Lajur 12 kolom | Tab Neraca Lajur |
| Laporan Laba Rugi (SHU) | Tab Laporan Keuangan |
| Laporan Perubahan Modal | Tab Laporan Keuangan |
| Neraca | Tab Laporan Keuangan |
| Laporan Arus Kas | Tab Laporan Keuangan |
| Rekap Penjualan Harian | Tab Laporan Keuangan |
| Daftar Akun | Tab Daftar Akun |
| Saldo Awal | Tab Saldo Awal |

**Tombol praktis:**

- **Cetak Semua (1 PDF)** — menggabungkan 8 laporan utama menjadi satu berkas
  PDF siap dijilid untuk laporan bulanan atau rapat anggota.
- **Ekspor Excel** — mengekspor seluruh laporan ke satu berkas Excel
  multi-sheet, bila angkanya masih ingin diolah lagi.

Hasil cetak tersimpan di folder `Laporan` (menu **Berkas → Lokasi Data**),
dan berkas PDF-nya langsung terbuka setelah selesai dibuat.

Contoh hasil cetak dapat dilihat pada `contoh/Contoh_Laporan_Lengkap.pdf`.

---

## 7. STOCK OPNAME DAN HPP

Program memakai **metode persediaan fisik (periodik)** — metode yang lazim dan
paling praktis untuk kantin koperasi.

Artinya: setiap pembelian barang dagangan dicatat ke akun **511 Pembelian**
(bukan langsung menambah akun Persediaan). Nilai persediaan yang sebenarnya
ditentukan lewat **penghitungan fisik barang (stock opname)** di akhir bulan.

**Cara mengisi:**

1. Hitung fisik seluruh barang dagangan di kantin pada hari terakhir bulan.
2. Buka tab **Neraca Lajur**.
3. Isi kotak **Persediaan Akhir (Stock Opname)** dengan nilai rupiahnya.
4. Klik **Simpan**.

Program menghitung sendiri:

```
HPP = Persediaan Awal + Pembelian + Angkut Pembelian
      − Retur Pembelian − Potongan Pembelian − Persediaan Akhir
```

**Penting:** bila stock opname tidak diisi, HPP akan dihitung nol dan SHU
menjadi terlalu besar. Isi angka ini setiap akhir bulan sebelum tutup buku.

---

## 8. TUTUP BUKU KE BULAN BERIKUTNYA

Tutup buku mengunci bulan berjalan dan memindahkan saldo akhir menjadi saldo
awal bulan berikutnya, sekaligus memindahkan SHU ke akun Laba Ditahan.

**Langkah:**

1. Pastikan seluruh transaksi bulan tersebut sudah masuk.
2. Pastikan stock opname sudah diisi (bagian 7).
3. Buka tab **Tutup Buku**. Program menampilkan hasil **pemeriksaan kesiapan**.
   Bila ada peringatan berwarna merah, selesaikan dahulu.
4. Periksa ringkasan angka yang ditampilkan (total penjualan, HPP, SHU,
   total aktiva).
5. Klik **Tutup Buku Periode Ini** dan konfirmasi.
6. Periode baru terbentuk otomatis dan langsung menjadi periode aktif.

**Setelah tutup buku:** seluruh transaksi bulan tersebut terkunci dan tidak
bisa diubah. Bila ternyata ada kesalahan, klik **Buka Kembali Periode** pada
tab yang sama — periode berikutnya (bila masih kosong) akan dihapus, transaksi
kembali bisa diedit, lalu tutup buku lagi setelah diperbaiki.

> Disarankan menekan tombol **Cadangkan Data** sebelum tutup buku.

---

## 9. MENCADANGKAN DAN MEMULIHKAN DATA

- **Berkas → Cadangkan Data** — membuat salinan basis data bertanggal di
  folder `backup`. Lakukan minimal sebulan sekali dan sebelum tutup buku.
- Program juga **mencadangkan otomatis setiap kali ditutup**.
- **Berkas → Pulihkan Data** — mengembalikan data dari berkas cadangan.
  Data yang ada sekarang akan tergantikan, jadi gunakan dengan hati-hati.

**Sangat disarankan:** salin isi folder `backup` ke flashdisk atau Google Drive
secara berkala. Kerusakan hard disk atau laptop hilang adalah penyebab
kehilangan data pembukuan yang paling sering terjadi.

**Khusus pemakai versi portable:** flashdisk jauh lebih mudah hilang, rusak,
atau terformat daripada hard disk komputer. Salin seluruh folder `Data` ke
komputer atau penyimpanan awan setidaknya setiap selesai tutup buku bulanan.

---

## 10. ALUR KERJA BULANAN (RINGKAS)

```
SETIAP HARI / MINGGU
  └─ Input transaksi  (Jurnal Transaksi → Transaksi Baru)
     atau impor dari Excel  (Jurnal Transaksi → Impor Excel)

AKHIR BULAN
  1. Periksa kelengkapan transaksi           → tab Jurnal Transaksi
  2. Input jurnal penyesuaian (jenis AJP)    → penyusutan, perlengkapan
  3. Hitung fisik barang, isi stock opname   → tab Neraca Lajur
  4. Periksa neraca lajur sudah BALANCE      → tab Neraca Lajur
  5. Lihat Laba Rugi, Perubahan Modal,
     Neraca, Arus Kas                        → tab Laporan Keuangan
  6. Klik "Cetak Semua (1 PDF)"              → berkas laporan bulanan
  7. Cadangkan data                          → Berkas → Cadangkan Data
  8. Tutup buku                              → tab Tutup Buku

 → Bulan berikutnya terbuka otomatis, saldo awal sudah terisi sendiri.
```

---

## 11. CONTOH JURNAL TRANSAKSI KANTIN

| Kejadian | Debit | Kredit |
|----------|-------|--------|
| Rekap penjualan tunai harian | 111 Kas | 411 Penjualan Kantin |
| Penjualan seragam belum dibayar | 113 Piutang | 412 Penjualan Seragam & ATK |
| Pelanggan melunasi piutang | 111 Kas | 113 Piutang |
| Barang dikembalikan pembeli | 413 Retur & Potongan Penjualan | 111 Kas |
| Beli barang dagangan tunai | 511 Pembelian | 111 Kas |
| Beli barang dagangan kredit | 511 Pembelian | 211 Utang Usaha |
| Ongkos angkut barang beli | 512 Angkut Pembelian | 111 Kas |
| Kembalikan barang rusak ke supplier | 211 Utang Usaha | 513 Retur Pembelian |
| Bayar utang ke supplier | 211 Utang Usaha | 111 Kas |
| Bayar gaji penjaga kantin | 611 Beban Gaji / Honor | 111 Kas |
| Bayar listrik & air | 612 Beban Listrik & Air | 111 Kas |
| Setor kas ke bank | 112 Bank | 111 Kas |
| Tarik tunai dari bank | 111 Kas | 112 Bank |
| Terima simpanan wajib anggota | 111 Kas | 312 Simpanan Wajib |
| Terima simpanan pokok anggota baru | 111 Kas | 311 Simpanan Pokok |
| Beli peralatan kantin | 121 Peralatan | 111 Kas |
| Penyusutan peralatan *(AJP)* | 614 Beban Penyusutan | 122 Akum. Penyusutan |
| Pemakaian perlengkapan *(AJP)* | 613 Beban ATK & Perlengkapan | 115 Perlengkapan |

---

## 12. TANYA JAWAB DAN MENGATASI MASALAH

**Program tidak mau dibuka / muncul peringatan Windows SmartScreen.**
Klik **More info** → **Run anyway**. Ini terjadi karena berkas EXE belum
bersertifikat digital, bukan karena berisi virus.

**Tombol Simpan pada dialog jurnal tidak bisa ditekan.**
Berarti total debit belum sama dengan total kredit. Periksa indikator
BALANCE di bawah tabel rincian.

**Neraca tidak balance.**
Penyebab paling sering: stock opname belum diisi, atau saldo awal belum
seimbang. Buka tab Neraca Lajur dan periksa status di bagian bawah.

**SHU terasa terlalu besar.**
Stock opname belum diisi sehingga HPP masih nol. Lihat bagian 7.

**Saya salah input transaksi bulan lalu yang sudah ditutup.**
Tab Tutup Buku → **Buka Kembali Periode** → perbaiki → tutup buku lagi.

**Impor Excel ditolak.**
Baca daftar masalah di jendela pratinjau. Penyebab umum: kode akun salah
ketik, tanggal di luar bulan periode tujuan, atau ada transaksi yang debit
dan kreditnya tidak sama.

**Bagaimana memindahkan data ke komputer lain?**
Menu **Berkas → Cadangkan Data**, salin berkas cadangannya ke komputer baru,
pasang program di sana, lalu **Berkas → Pulihkan Data**. Bila memakai versi
portable, cukup bawa flashdisknya — datanya sudah ikut.

**Apakah versi portable dan versi terpasang bisa dipakai bersamaan?**
Bisa, tetapi datanya terpisah dan tidak saling menyusul. Pilih satu sebagai
pembukuan resmi agar tidak ada angka yang tercecer di dua tempat.

**Flashdisk saya terproteksi (read-only), apa yang terjadi?**
Program otomatis beralih ke mode terpasang supaya pekerjaan tidak terhenti.
Periksa menu **Berkas → Lokasi Data** untuk melihat data sedang ditulis
ke mana.

**Bisakah dipakai beberapa orang sekaligus?**
Program ini dirancang untuk satu komputer (basis data lokal). Untuk pemakaian
bersama, tunjuk satu komputer sebagai pencatat resmi, lalu bagikan hasil
laporannya dalam bentuk PDF.

**Bagaimana menambah akun baru?**
Tab **Daftar Akun** → **Tambah Akun**. Isi kode, nama, kelompok (Aktiva/
Kewajiban/Modal/Pendapatan/Beban), dan subkategori. Kode akun sebaiknya
mengikuti pola yang sudah ada: 1xx aktiva, 2xx kewajiban, 3xx modal,
4xx pendapatan, 5xx pembelian, 6xx beban.

---

*Program Pembukuan Kantin Koperasi v1.0.0 — dokumen ini juga dapat dibuka
dari dalam program melalui menu **Bantuan → Panduan**.*
