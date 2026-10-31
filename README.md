<div align="center">

<img src="assets/ikon.png" width="110" alt="Pembukuan Kantin Koperasi">

# Program Pembukuan Kantin Koperasi

**Aplikasi pembukuan desktop untuk unit usaha kantin koperasi**

Menggantikan pembukuan Excel dengan program yang lebih aman dari salah rumus,
lengkap dengan cetak PDF sekali klik dan proses tutup buku bulanan.
Bebas dipakai dan disesuaikan oleh koperasi mana pun.

Versi 2.0 · Windows & macOS · tersedia versi portable · tanpa internet

</div>

---

## Unduh

Ambil berkas jadi di halaman **[Releases](../../releases)**:

| Berkas | Untuk siapa |
|--------|-------------|
| `PembukuanKantin-Portable-Windows.zip` | Windows — jalan dari flashdisk, tanpa dipasang |
| `KantinKoperasi_Setup_1.0.1.exe` | Windows — dipasang seperti aplikasi biasa |
| `PembukuanKantin-Portable-macOS-AppleSilicon.zip` | Mac M1/M2/M3/M4 — portable |
| `KantinKoperasi-macOS-AppleSilicon.dmg` | Mac M1/M2/M3/M4 — dipasang ke Applications |

Berkas Mac di atas untuk **Apple Silicon** (M1/M2/M3/M4). GitHub sudah tidak
menyediakan mesin pembangun Mac Intel, jadi pemakai Mac Intel perlu membangun
sendiri di mesinnya dengan `bash build_mac.sh` (lihat [BUILD.md](BUILD.md)).

Belum ada berkas di Releases? Buka tab **Actions → Bangun Aplikasi → Run
workflow**, tunggu 5–10 menit, lalu unduh di bagian **Artifacts**. Semua versi
dibangun di server GitHub, jadi tidak perlu memasang apa pun di komputer
sendiri — dan Mac tetap bisa dibuatkan walau Bapak hanya punya Windows.

### Membuka pertama kali

**Windows** — muncul "Windows protected your PC": klik *More info* → *Run anyway*.
**macOS** — klik **kanan** ikon aplikasi → *Open* → *Open*. Cukup sekali saja.

Keduanya muncul karena aplikasi belum bersertifikat digital berbayar, bukan
karena berisi virus.

---

## Portable atau terpasang?

Berkas programnya sama persis; yang membedakan hanya letak datanya.

| | Portable | Terpasang |
|---|---|---|
| Data disimpan di | folder `Data` di sebelah aplikasi | folder pengguna komputer |
| Dibawa pakai flashdisk | ya, data ikut pindah | tidak |
| Menulis ke komputer yang dipakai | tidak sama sekali | ya |
| Cocok untuk | bendahara yang berpindah komputer | satu komputer tetap di koperasi |

**Mengaktifkan mode portable:** buat folder bernama `Data` di sebelah
`KantinKoperasi.exe` (atau `KantinKoperasi.app`). Paket portable dari Releases
sudah berisi folder itu, jadi langsung siap pakai.

**Mematikannya kembali:** hapus folder `Data` dan berkas `portable.txt`.

Mode yang sedang aktif bisa dilihat lewat menu **Berkas → Lokasi Data**. Bila
media penyimpanannya ternyata tidak bisa ditulisi, program otomatis kembali ke
mode terpasang supaya pekerjaan tidak terhenti.

---

## Kemampuan

**Pencatatan**
- Input jurnal manual dengan pemeriksaan balance otomatis — tombol simpan
  terkunci selama debit ≠ kredit
- 5 tombol transaksi cepat untuk pola jurnal yang sering dipakai
- Impor massal dari Excel/CSV dengan template bawaan, pratinjau, dan
  pemeriksaan kesalahan sebelum data masuk
- Jurnal penyesuaian (AJP) terpisah dari jurnal umum

**Laporan — 11 jenis, semuanya bisa dicetak PDF**

Jurnal Umum · Buku Besar per akun · Rekap Buku Besar · Neraca Lajur 12 kolom ·
Laba Rugi (SHU) · Perubahan Modal · Neraca · Arus Kas · Rekap Penjualan Harian ·
Daftar Akun · Saldo Awal

Tersedia pula **Cetak Semua (1 PDF)** yang menggabungkan 8 laporan utama
menjadi satu berkas siap jilid, serta **Ekspor Excel** multi-sheet. Setiap PDF
memuat kop koperasi, nomor halaman, waktu cetak, dan kolom tanda tangan ketua
serta bendahara.

**Proses akuntansi**
- Metode persediaan fisik/periodik dengan input stock opname
- HPP dihitung otomatis: persediaan awal + pembelian + angkut − retur −
  potongan − persediaan akhir
- Tutup buku bulanan: mengunci periode, memindahkan SHU ke Laba Ditahan, dan
  membentuk saldo awal bulan berikutnya secara otomatis
- Fasilitas buka kembali periode bila ada koreksi
- Pencadangan manual dan otomatis setiap program ditutup

---

## Dirancang untuk petugas tanpa dasar akuntansi

Petugas hanya mengisi **dua tab**. Istilah debit dan kredit tidak pernah muncul.

```
  Tab BUKU KAS          Tab PERSEDIAAN
  uang masuk/keluar     barang datang/terjual
         │                     │
         └──────────┬──────────┘
                    ▼
     program menyusun sendiri: jurnal → buku besar →
     neraca lajur → laba rugi, perubahan modal,
     laporan posisi keuangan, arus kas
```

Pada **Buku Kas**, petugas memilih "Untuk apa?" dari daftar berbahasa
sehari-hari ("Uang hasil penjualan", "Bayar gaji penjaga"), bukan memilih
akun. Pada **Persediaan**, barang keluar cukup diisi jumlah unitnya —
harga pokoknya dihitung sendiri oleh program.

---

## Persediaan perpetual, dua jenis barang

Persediaan dicatat **perpetual** dengan **harga pokok rata-rata bergerak**:
setiap barang masuk dengan harga berbeda, rata-ratanya dihitung ulang;
setiap barang keluar, harga pokoknya terbentuk sendiri dan langsung masuk
ke Laporan Laba Rugi. Tidak perlu stock opname bulanan.

Dua jenis bawaan: **Seragam & ATK** dan **Makanan & Minuman**, masing-masing
punya akun persediaan, akun harga pokok, dan akun penjualan sendiri.

```
Uang hasil penjualan  −  Harga pokok barang terjual  =  Laba kotor
Laba kotor            −  Beban (gaji, listrik, dsb)  =  SHU
```

---

## Memulai pemakaian

Program dibuka dengan **bagan akun (COA) 26 akun** yang sudah siap untuk usaha
kantin/toko, tanpa angka apa pun. Repositori ini sengaja tidak memuat data
pembukuan koperasi mana pun.

Tiga langkah pertama:

1. **Berkas → Pengaturan** — isi nama koperasi, unit usaha, kota, nama ketua
   dan bendahara. Data ini yang tercetak di kop dan kolom tanda tangan setiap
   laporan.
2. **Tab Daftar Akun** — periksa 26 akun bawaan, tambah atau ubah bila perlu.
3. **Tab Saldo Awal** — isi saldo pembuka. Indikator di bawah tabel harus
   bertuliskan SEIMBANG sebelum bisa disimpan.

Setelah itu mulai mencatat di tab **Jurnal Transaksi**, atau impor sekaligus
dari Excel memakai template yang bisa diunduh dari dalam program.

Folder [`contoh/`](contoh) berisi template impor, contoh yang sudah terisi, dan
contoh hasil cetak PDF serta ekspor Excel — semuanya memakai data fiktif
"Koperasi Sejahtera Mandiri" sebagai ilustrasi.

---

## Membangun sendiri

Bila ingin membangun dari kode sumber, bukan mengunduh dari Releases.

**Windows** — klik dua kali `SETUP_OTOMATIS.bat`. Skrip memasang Python sendiri
bila belum ada, lalu membangun EXE-nya. Lanjutkan dengan `build_portable.bat`
untuk versi flashdisk, atau `build_installer.bat` untuk installer (perlu
[Inno Setup](https://jrsoftware.org/isdl.php)).

**macOS** — buka Terminal, masuk ke folder ini, lalu jalankan `bash build_mac.sh`.

**Mencoba tanpa membangun** — di sistem operasi mana pun:

```bash
pip install -r requirements.txt
python main.py
```

Di Linux, `python3-tk` perlu dipasang lebih dulu. Rincian lengkap dan catatan
teknis ada di **[BUILD.md](BUILD.md)**.

---

## Struktur

```
app/
├── db.py            basis data SQLite, pengaturan, deteksi mode portable
├── engine.py        mesin akuntansi & tutup buku
├── pdfout.py        pembuat 11 laporan PDF
├── xlsio.py         impor/ekspor Excel
├── data_awal.json   COA, saldo awal, jurnal Jan–Feb 2026
└── ui/              antarmuka Tkinter (8 tab)
assets/              ikon (.ico Windows, .icns macOS, .png)
contoh/              template impor, contoh terisi, contoh hasil cetak
```

**Pustaka:** Tkinter dan SQLite (bawaan Python), ReportLab (PDF),
openpyxl (Excel), pypdf (gabung PDF). Tidak ada komponen berbayar.

---

## Dokumentasi

| Berkas | Isi |
|--------|-----|
| **[PANDUAN.md](PANDUAN.md)** | Manual pemakaian untuk pengurus koperasi — 12 bagian, termasuk tabel contoh jurnal 18 transaksi khas kantin |
| **[BUILD.md](BUILD.md)** | Cara membangun aplikasi, catatan teknis, riwayat perubahan |
| **[LISENSI.txt](LISENSI.txt)** | Ketentuan pemakaian |

---

<div align="center">
<sub>Bebas digunakan dan disesuaikan oleh koperasi mana pun</sub>
</div>
