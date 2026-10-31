# PANDUAN PEMAKAIAN
## Program Pembukuan Kantin Koperasi — versi 2.0

Panduan ini ditulis untuk petugas kantin, bukan untuk orang akuntansi.
Tidak perlu tahu apa itu debit, kredit, atau jurnal. Program yang
mengurus semua itu sendiri.

**Yang perlu Anda lakukan hanya dua hal:**

> 1. Catat **uang** yang masuk dan keluar → tab **Buku Kas**
> 2. Catat **barang** yang datang dan terjual → tab **Persediaan**

Dari dua catatan itu, program menyusun sendiri jurnal, buku besar, neraca
lajur, sampai laporan keuangan lengkap yang tinggal dicetak.

---

## DAFTAR ISI

1. [Memasang program](#1-memasang-program)
2. [Mengenal tampilan](#2-mengenal-tampilan)
3. [Persiapan awal (sekali saja)](#3-persiapan-awal-sekali-saja)
4. [Mencatat uang masuk dan keluar](#4-mencatat-uang-masuk-dan-keluar)
5. [Mencatat barang masuk dan terjual](#5-mencatat-barang-masuk-dan-terjual)
6. [Penjualan yang dibayar menyusul](#6-penjualan-yang-dibayar-menyusul)
7. [Melihat dan mencetak laporan](#7-melihat-dan-mencetak-laporan)
8. [Tutup buku ke bulan berikutnya](#8-tutup-buku-ke-bulan-berikutnya)
9. [Mencadangkan data](#9-mencadangkan-data)
10. [Alur kerja bulanan](#10-alur-kerja-bulanan)
11. [Tanya jawab](#11-tanya-jawab)

---

## 1. MEMASANG PROGRAM

### Windows

**Cara A — installer.** Klik dua kali `KantinKoperasi_Setup_2.0.0.exe`, ikuti
sampai selesai. Bila muncul peringatan biru "Windows protected your PC", klik
**More info** → **Run anyway**.

**Cara B — portable (flashdisk).** Salin folder `PembukuanKantin-Portable`
ke flashdisk, klik dua kali `KantinKoperasi.exe`. Seluruh data ikut di dalam
folder itu, jadi bisa dibawa ke komputer mana pun.

### Mac

Buka berkas `.dmg`, seret ikonnya ke folder Applications. **Pembukaan
pertama:** klik **kanan** ikon aplikasi → **Open** → tekan **Open** lagi.
Cukup sekali.

Peringatan pada Windows maupun Mac muncul karena aplikasi belum
bersertifikat digital berbayar, bukan karena berisi virus.

### Di mana data saya tersimpan?

Lihat menu **Berkas → Lokasi Data**. Baris pertama memberi tahu modenya:

- **PORTABLE** — data ada di folder `Data` di sebelah aplikasi, ikut
  berpindah bila foldernya disalin.
- **TERPASANG** — data ada di folder pengguna komputer, tetap aman walaupun
  program dihapus atau diperbarui.

---

## 2. MENGENAL TAMPILAN

Di bagian atas ada **pemilih periode** (misalnya "Maret 2026"). Semua yang
tampil mengikuti bulan yang sedang dipilih.

| Tab | Isinya | Siapa yang pakai |
|-----|--------|------------------|
| **Beranda** | Ringkasan: sisa kas, persediaan, SHU | semua |
| **Buku Kas** | Uang masuk dan keluar | **petugas** |
| **Persediaan** | Barang datang dan terjual | **petugas** |
| Jurnal | Hasil olahan otomatis, bisa diperiksa | pengurus |
| Buku Besar | Mutasi tiap akun | pengurus |
| Neraca Lajur | Kertas kerja 12 kolom | pengurus |
| Laporan Keuangan | Laba Rugi, Perubahan Modal, Posisi Keuangan, Arus Kas | pengurus |
| Daftar Akun | Daftar kode akun | pengurus |
| Saldo Awal | Saldo pembuka | pengurus |
| Tutup Buku | Mengunci bulan, pindah ke bulan berikutnya | pengurus |

**Petugas sehari-hari cukup memakai dua tab saja:** Buku Kas dan Persediaan.

---

## 3. PERSIAPAN AWAL (SEKALI SAJA)

1. **Berkas → Pengaturan** — isi nama koperasi, unit usaha, kota, nama ketua
   dan bendahara. Data ini tercetak di kop dan kolom tanda tangan setiap
   laporan.
2. **Tab Saldo Awal** — isi saldo pembuka: uang kas, saldo bank, piutang,
   peralatan, utang, simpanan anggota, dan modal. Indikator di bawah tabel
   harus bertuliskan **SEIMBANG** sebelum bisa disimpan.
3. **Tab Persediaan** — catat stok barang yang ada sekarang lewat tombol
   **Barang Masuk**: berapa unit dan berapa harga belinya.

Setelah itu program siap dipakai sehari-hari.

---

## 4. MENCATAT UANG MASUK DAN KELUAR

Buka tab **Buku Kas**. Ada dua tombol besar.

### Uang masuk (tombol hijau)

Dipakai setiap ada uang diterima. Isi empat hal:

| Isian | Contoh |
|-------|--------|
| Tanggal | 05/03/2026 |
| Untuk apa? | pilih **Penjualan Kantin — Uang hasil penjualan** |
| Keterangan | Rekap penjualan 5 Maret |
| Jumlah uang | 485.000 |

Klik **Simpan**. Selesai.

### Uang keluar (tombol merah)

Dipakai setiap ada uang dikeluarkan:

| Isian | Contoh |
|-------|--------|
| Tanggal | 15/03/2026 |
| Untuk apa? | pilih **Beban Gaji / Honor — Pengeluaran rutin kantin** |
| Keterangan | Gaji penjaga kantin bulan Maret |
| Jumlah uang | 1.200.000 |

### Daftar "Untuk apa?"

Setiap pilihan sudah diberi penjelasan singkat, jadi tinggal dibaca:

| Pilih ini | Kalau kejadiannya |
|-----------|-------------------|
| Penjualan Kantin | Uang hasil jualan makanan dan minuman |
| Penjualan Seragam & ATK | Uang hasil jualan seragam atau alat tulis |
| Piutang | Pelanggan melunasi utangnya |
| Bank | Setor uang ke bank, atau tarik tunai |
| Beban Gaji / Honor | Bayar gaji penjaga |
| Beban Listrik & Air | Bayar listrik atau air |
| Utang Usaha | Membayar utang ke pemasok |
| Simpanan Wajib / Pokok | Terima setoran anggota |
| Peralatan | Beli barang tahan lama, misalnya kulkas atau etalase |

> **Pembelian barang dagangan tidak dicatat di sini.** Catat di tab
> Persediaan, nanti buku kas terisi sendiri.

### Mengubah atau menghapus

Klik dua kali barisnya untuk mengubah, atau pilih baris lalu tekan **Hapus**.

---

## 5. MENCATAT BARANG MASUK DAN TERJUAL

Buka tab **Persediaan**. Ada dua jenis barang:

1. **Seragam & ATK** — satuannya potong
2. **Makanan & Minuman** — satuannya item

Di bagian atas terlihat sisa stok dan nilainya masing-masing.

### Barang masuk (tombol hijau)

Dipakai setiap barang datang dari pemasok:

| Isian | Contoh |
|-------|--------|
| Tanggal | 02/03/2026 |
| Jenis barang | Makanan & Minuman |
| Keterangan | Beli snack dari pemasok |
| Berapa unit masuk? | 200 |
| Harga beli per unit | 3.000 |
| Dibayar | Tunai sekarang / Belum dibayar (utang) |

Program otomatis menambah stok, dan **buku kas ikut terisi sendiri** bila
dibayar tunai. Tidak perlu mencatat dua kali.

### Barang keluar (tombol oranye)

Dipakai setiap barang terjual atau terpakai. **Cukup isi berapa unitnya:**

| Isian | Contoh |
|-------|--------|
| Tanggal | 10/03/2026 |
| Jenis barang | Makanan & Minuman |
| Keterangan | Terjual 1–10 Maret |
| Berapa unit keluar? | 150 |

**Harga pokoknya dihitung sendiri oleh program.** Anda tidak perlu tahu
berapa harga beli barang itu dulu — program menghitungnya dari rata-rata
harga beli yang tercatat, dan langsung memasukkannya ke Laporan Laba Rugi.

Uang hasil penjualannya tetap dicatat terpisah di **Buku Kas** sebagai uang
masuk, karena jumlah uang yang diterima belum tentu sama dengan harga pokok
barangnya — selisihnya itulah keuntungan kantin.

### Penyesuaian stok

Dipakai kalau hitungan fisik berbeda dengan catatan, misalnya barang rusak,
hilang, atau kedaluwarsa. Isi selisih unitnya, beri tanda **minus** bila
stok berkurang (contoh: `-5`).

---

## 6. PENJUALAN YANG DIBAYAR MENYUSUL

Untuk seragam yang diambil siswa tapi dibayar belakangan, pakai tombol
**Penjualan dibayar menyusul** di tab Persediaan:

| Isian | Contoh |
|-------|--------|
| Tanggal | 23/03/2026 |
| Jenis barang | Seragam & ATK |
| Pembeli / keterangan | Seragam 12 siswa kelas 7A |
| Berapa unit terjual? | 12 |
| Harga jual seluruhnya | 1.560.000 |

Program mencatat piutang bertambah dan stok berkurang sekaligus.

**Saat dilunasi nanti:** catat di **Buku Kas** sebagai uang masuk, pilih
**Piutang — Pelanggan melunasi utangnya**.

---

## 7. MELIHAT DAN MENCETAK LAPORAN

Semua laporan tersusun sendiri. Setiap laporan punya tombol **Cetak PDF**,
lengkap dengan kop koperasi, nomor halaman, waktu cetak, dan kolom tanda
tangan ketua serta bendahara.

| Laporan | Letaknya |
|---------|----------|
| Buku Kas | tab Buku Kas |
| Kartu Persediaan | tab Persediaan |
| Jurnal Umum | tab Jurnal |
| Buku Besar per akun | tab Buku Besar |
| Rekap Buku Besar | tab Buku Besar |
| Neraca Lajur 12 kolom | tab Neraca Lajur |
| Laporan Laba Rugi (SHU) | tab Laporan Keuangan |
| Laporan Perubahan Modal | tab Laporan Keuangan |
| **Laporan Posisi Keuangan** | tab Laporan Keuangan |
| Laporan Arus Kas | tab Laporan Keuangan |
| Rekap Penjualan Harian | tab Laporan Keuangan |

**Cetak Semua (1 PDF)** menggabungkan laporan utama jadi satu berkas siap
jilid untuk rapat anggota. **Ekspor Excel** mengeluarkan semuanya ke satu
berkas Excel multi-sheet.

### Bagaimana keuntungan dihitung?

```
Uang hasil penjualan            (dari Buku Kas)
  −  Harga pokok barang terjual (dari tab Persediaan, otomatis)
  =  LABA KOTOR
  −  Beban: gaji, listrik, dll  (dari Buku Kas)
  =  SISA HASIL USAHA (SHU)
```

Harga pokok dihitung dengan metode **rata-rata bergerak**: setiap kali
barang masuk dengan harga berbeda, program menghitung ulang harga rata-rata,
lalu memakainya saat barang keluar. Rinciannya bisa dilihat di Kartu
Persediaan.

---

## 8. TUTUP BUKU KE BULAN BERIKUTNYA

Tutup buku mengunci bulan berjalan dan memindahkan seluruh saldo ke bulan
berikutnya.

1. Pastikan semua catatan bulan itu sudah masuk.
2. Cocokkan sisa stok di tab Persediaan dengan hitungan fisik. Bila berbeda,
   catat lewat **Penyesuaian stok**.
3. Buka tab **Tutup Buku**, periksa hasil pemeriksaan kesiapan.
4. Klik **Cadangkan Data** lebih dulu.
5. Klik **Tutup Buku Periode Ini**.

Periode baru terbentuk otomatis. Saldo kas, piutang, utang, modal, dan sisa
stok ikut terbawa sendiri.

**Keliru menutup?** Klik **Buka Kembali Periode** di tab yang sama.

---

## 9. MENCADANGKAN DATA

- **Berkas → Cadangkan Data** — membuat salinan bertanggal.
- Program juga mencadangkan otomatis setiap kali ditutup.
- **Berkas → Pulihkan Data** — mengembalikan dari cadangan.

**Salin folder cadangan ke flashdisk atau Google Drive secara berkala**,
terutama setiap selesai tutup buku. Hard disk rusak dan laptop hilang adalah
penyebab kehilangan pembukuan yang paling sering terjadi.

---

## 10. ALUR KERJA BULANAN

```
SETIAP HARI ATAU SETIAP MINGGU
  └─ Uang masuk / keluar      →  tab Buku Kas
  └─ Barang datang / terjual  →  tab Persediaan

AKHIR BULAN
  1. Periksa buku kas sudah lengkap
  2. Cocokkan sisa stok dengan hitungan fisik;
     bila beda, catat lewat "Penyesuaian stok"
  3. Catat penyusutan peralatan bila ada     → tab Jurnal, jenis AJP
  4. Lihat laporan keuangan                  → tab Laporan Keuangan
  5. Klik "Cetak Semua (1 PDF)"
  6. Cadangkan data                          → Berkas → Cadangkan Data
  7. Tutup buku                              → tab Tutup Buku

 → Bulan berikutnya terbuka otomatis, saldo ikut terbawa sendiri.
```

---

## 11. TANYA JAWAB

**Saya tidak mengerti akuntansi, apa bisa memakai program ini?**
Bisa. Isi tab Buku Kas dan tab Persediaan saja. Semua istilah akuntansi
diurus program, tidak akan muncul di dua tab itu.

**Barang dibeli, dicatat di Buku Kas atau di Persediaan?**
Di **Persediaan**, lewat tombol Barang Masuk. Buku kas akan terisi sendiri.
Kalau dicatat di keduanya, uangnya terhitung keluar dua kali.

**Saya tidak tahu harga pokok barang yang terjual.**
Tidak perlu tahu. Isi jumlah unitnya saja, program yang menghitung.

**Kenapa uang masuk dari penjualan tidak sama dengan nilai barang keluar?**
Memang seharusnya berbeda. Uang masuk adalah harga jual, nilai barang keluar
adalah harga beli. Selisihnya keuntungan kantin.

**Stok di layar tidak cocok dengan barang yang ada.**
Pakai **Penyesuaian stok** di tab Persediaan. Isi selisihnya, beri tanda
minus bila barang yang ada lebih sedikit dari catatan.

**Barang keluar ditolak karena melebihi stok.**
Berarti ada pembelian yang belum dicatat. Catat dulu Barang Masuk-nya.

**Saya salah mencatat bulan lalu yang sudah ditutup.**
Tab Tutup Buku → **Buka Kembali Periode** → perbaiki → tutup buku lagi.

**Bisa ditambah jenis barang selain dua itu?**
Bisa, tapi perlu dibuatkan akun dan jenisnya lebih dulu. Hubungi yang
menyiapkan program ini. Memisahkan seragam dan ATK jadi dua jenis tersendiri
membuat harga pokoknya lebih tepat, karena harganya jauh berbeda.

**Bagaimana memindahkan pembukuan ke komputer lain?**
**Berkas → Cadangkan Data**, salin berkas cadangannya, lalu di komputer baru
**Berkas → Pulihkan Data**. Kalau memakai versi portable, cukup bawa
flashdisknya.

**Kenapa laporannya disebut "Laporan Posisi Keuangan", bukan "Neraca"?**
Istilah itu yang dipakai standar akuntansi yang berlaku sekarang. Isinya
sama: daftar harta, utang, dan modal koperasi pada tanggal tertentu.

---

*Program Pembukuan Kantin Koperasi v2.0 — panduan ini juga bisa dibuka dari
dalam program lewat menu **Bantuan → Panduan**.*
