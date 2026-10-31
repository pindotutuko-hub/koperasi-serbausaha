# CARA MEMBANGUN APLIKASI

Dokumen ini untuk orang yang **membuat** berkas aplikasinya, bukan untuk
pengguna akhir. Pengguna akhir cukup membaca `PANDUAN.md`.

**Aturan dasar:** berkas aplikasi harus dibangun di sistem operasi yang sama
dengan sasarannya. EXE Windows dibangun di Windows, aplikasi macOS dibangun di
Mac. Tidak ada jalan pintas lintas sistem — kecuali lewat GitHub Actions, yang
meminjam komputer Windows dan Mac milik GitHub (lihat bagian di bawah).

---

## CARA PALING MUDAH — satu klik

Klik dua kali **`SETUP_OTOMATIS.bat`**.

Skrip ini memeriksa Python, mengunduh dan memasangnya sendiri bila belum ada,
memasang seluruh pustaka, lalu membangun EXE-nya — semuanya dalam satu jalan.
Hanya perlu koneksi internet. Lama proses 5–12 menit.

Berkas jadi: **`dist\KantinKoperasi.exe`**

## CARA MANUAL (bila Python sudah terpasang)

1. Pastikan Python 3.10 atau lebih baru sudah ada. Saat memasangnya,
   **centang "Add python.exe to PATH"** — ini wajib.
2. Klik dua kali **`build_exe.bat`**, tunggu 3–6 menit.
3. Berkas jadi: **`dist\KantinKoperasi.exe`**

Berkas EXE tersebut berdiri sendiri. Bisa disalin ke komputer Windows lain
dan langsung dijalankan tanpa perlu memasang Python di sana.

### Membuat installer (opsional)

1. Pasang **Inno Setup 6** dari <https://jrsoftware.org/isdl.php> (gratis).
2. Klik dua kali **`build_installer.bat`**.
3. Berkas jadi: **`installer_output\KantinKoperasi_Setup_1.0.1.exe`**

---

## MEMBANGUN VERSI macOS

Di komputer Mac, buka Terminal lalu:

```bash
cd /path/ke/koperasi-serbausaha
bash build_mac.sh
```

Hasilnya `dist/KantinKoperasi.app` dan `dist/KantinKoperasi-mac.dmg`.

Skrip menandatangani aplikasi secara *ad-hoc* agar macOS mau menjalankannya.
Penandatanganan resmi memerlukan Apple Developer Program (berbayar, per tahun);
tanpa itu, pengguna cukup klik kanan → Open pada pembukaan pertama.

Aplikasi yang dibangun hanya berjalan di arsitektur mesin pembangunnya: Mac
Apple Silicon menghasilkan versi Apple Silicon, Mac Intel menghasilkan versi
Intel. Untuk keduanya sekaligus, pakai GitHub Actions di bawah.

---

## MEMBANGUN SEMUA VERSI TANPA KOMPUTER APA PUN

GitHub Actions meminjamkan komputer Windows dan Mac milik GitHub. Cara ini
menghasilkan **lima berkas sekaligus** — portable Windows, installer Windows,
portable Mac Apple Silicon, portable Mac Intel, dan DMG — tanpa perlu memasang
Python, Inno Setup, atau punya Mac sendiri.

1. Buka repositori ini di GitHub.
2. Masuk tab **Actions** → pilih **Bangun Aplikasi (Windows + macOS)**.
3. Klik **Run workflow**.
4. Tunggu 5–10 menit, unduh hasilnya di bagian **Artifacts**.

Untuk menerbitkan Release otomatis beserta seluruh berkasnya:

```bash
git tag v1.0.1
git push origin v1.0.1
```

Berkas alur kerjanya ada di `.github/workflows/build.yml`.

---

## MENJALANKAN DARI KODE SUMBER (tanpa build)

Berguna untuk mencoba program atau melakukan perubahan:

```bash
pip install -r requirements.txt
python main.py
```

Berjalan di Windows, Linux, maupun macOS. Di Linux, paket `python3-tk` perlu
dipasang lebih dahulu:

```bash
sudo apt install python3-tk
```

---

## STRUKTUR FOLDER

```
kantin/
├── main.py                     titik masuk program
├── requirements.txt            daftar pustaka yang dibutuhkan
├── KantinKoperasi.spec         konfigurasi PyInstaller
├── version_info.txt            informasi versi yang tertanam di EXE
├── SETUP_OTOMATIS.bat          Windows: pasang Python + buat EXE sekaligus
├── build_exe.bat               Windows: buat EXE saja, bila Python sudah ada
├── build_portable.bat          Windows: susun folder portable untuk flashdisk
├── build_installer.bat         Windows: buat installer
├── build_mac.sh                macOS: buat .app dan .dmg
├── installer.iss               skrip Inno Setup
├── PANDUAN.md                  panduan untuk pengguna
├── BUILD.md                    dokumen ini
├── README.md                   ringkasan program
├── LISENSI.txt                 ketentuan pemakaian
├── app/
│   ├── data_awal.json          COA, saldo awal, jurnal Jan–Feb 2026
│   ├── db.py                   basis data SQLite & pengaturan
│   ├── engine.py               mesin akuntansi & tutup buku
│   ├── pdfout.py               pembuat laporan PDF
│   ├── xlsio.py                impor/ekspor Excel
│   └── ui/
│       ├── widgets.py          komponen tampilan & format rupiah
│       ├── tab_jurnal.py       tab jurnal + dialog input & impor
│       ├── tab_laporan.py      buku besar, neraca lajur, laporan
│       ├── tab_data.py         daftar akun & saldo awal
│       └── utama.py            jendela utama, menu, beranda, tutup buku
├── assets/
│   ├── ikon.ico                ikon aplikasi (Windows)
│   ├── ikon.icns               ikon aplikasi (macOS)
│   └── ikon.png                ikon aplikasi (umum)
└── contoh/
    ├── Template_Impor_Jurnal.xlsx
    ├── Contoh_Impor_Terisi.xlsx
    ├── Contoh_Laporan_Lengkap_Januari_2026.pdf
    └── Contoh_Ekspor_Laporan_Januari_2026.xlsx
```

---

## CATATAN TEKNIS

**Pustaka yang dipakai:** Tkinter (bawaan Python) untuk tampilan, SQLite
(bawaan Python) untuk basis data, ReportLab untuk PDF, openpyxl untuk Excel,
pypdf untuk menggabungkan PDF. Tidak ada komponen berbayar.

**Ukuran EXE:** sekitar 25–35 MB karena seluruh pustaka ikut dibungkus.

**Letak data pengguna** bergantung pada mode:

| Mode | Windows | macOS |
|------|---------|-------|
| Terpasang | `%LOCALAPPDATA%\KantinKoperasi\` | `~/Library/Application Support/KantinKoperasi/` |
| Portable | `<folder aplikasi>\Data\` | `<folder aplikasi>/Data/` |

Mode portable aktif bila di sebelah aplikasi ada folder bernama `Data` atau
berkas penanda `portable.txt`. Berkas programnya sama persis untuk kedua mode —
hanya keberadaan penanda itu yang membedakan.

Di macOS, folder `Data` diletakkan **di sebelah** berkas `.app`, bukan di
dalamnya, supaya tidak ikut terhapus saat aplikasi diganti versi baru.

Bila media penyimpanan ternyata tidak bisa ditulisi (mis. flashdisk read-only),
program otomatis kembali ke mode terpasang. Mode portable juga bisa dimatikan
paksa lewat variabel lingkungan `KANTIN_PORTABLE=off`.

**Antivirus:** sebagian antivirus kadang menandai hasil PyInstaller sebagai
mencurigakan (false positive). Bila terjadi, tambahkan berkas EXE ke daftar
pengecualian, atau bangun ulang setelah memperbarui PyInstaller ke versi
terbaru.

**Memperbarui versi:** ubah `VERSI_APLIKASI` di `app/db.py`, `version_info.txt`,
dan `#define VersiApp` di `installer.iss` agar seragam.

**Mengganti data awal:** berkas `app/data_awal.json` berisi daftar akun, saldo
awal, dan jurnal yang otomatis dimuat saat basis data pertama kali dibuat.
Untuk memulai dari kosong, hapus isi bagian `jurnal` dan `saldo_awal` pada
berkas tersebut sebelum membangun EXE.

---

## RIWAYAT PERUBAHAN

**2.1.0**
- Dua akun baru untuk jurnal penyesuaian akhir bulan: **118 Pendapatan yang
  Masih Harus Diterima** dan **216 Beban yang Masih Harus Dibayar**, supaya
  tidak bercampur dengan piutang penjualan seragam (113) maupun utang ke
  pemasok (211) dan tetap mudah ditelusuri saat rekonsiliasi.
- Tombol transaksi cepat di tab Jurnal diganti isinya: kini berisi empat
  jurnal penyesuaian yang memang harus ditimbang manusia tiap akhir bulan
  (penyusutan peralatan, beban belum dibayar, pendapatan belum diterima,
  pemakaian perlengkapan) dan otomatis menyetel jenis jurnal ke AJP.
  Transaksi kas dan pembelian tidak lagi ada di sini karena sudah ditangani
  tab Buku Kas dan tab Persediaan.
- Basis data naik ke versi 3, migrasi otomatis seperti sebelumnya.
**2.0.0**
- Alur pencatatan dirancang ulang untuk petugas tanpa dasar akuntansi:
  tab **Buku Kas** (uang masuk/keluar dengan pilihan berbahasa awam) dan
  tab **Persediaan** (barang datang/terjual) menjadi satu-satunya tempat
  input. Jurnal, buku besar, neraca lajur, dan laporan keuangan tersusun
  sendiri dari kedua catatan itu.
- Persediaan **perpetual** dengan harga pokok **rata-rata bergerak**, dua
  jenis barang: Seragam & ATK, serta Makanan & Minuman. Barang keluar cukup
  diisi jumlah unitnya; harga pokok dihitung program dan langsung masuk ke
  Laporan Laba Rugi. Stock opname bulanan tidak lagi diperlukan.
- Penjualan yang dibayar menyusul: piutang bertambah dan stok berkurang
  dalam satu langkah; pelunasannya dicatat lewat Buku Kas.
- Istilah **Neraca** diganti **Laporan Posisi Keuangan** di seluruh
  antarmuka, judul PDF, nama berkas, dan dokumentasi. "Neraca Lajur" dan
  "Neraca Saldo" tetap, karena keduanya istilah baku tersendiri.
- Laporan baru: Buku Kas dan Kartu Persediaan, keduanya siap cetak PDF.
- Basis data naik ke versi 2 dengan migrasi otomatis. Pembukuan lama tetap
  utuh dan tetap dihitung dengan metode periodik agar angkanya tidak
  bergeser; pencatatan baru memakai perpetual. Saldo persediaan lama
  dibiarkan di akunnya sendiri dan tidak dicampur dengan persediaan baru.


**1.0.1b** — versi repositori
- Mode **portable** untuk Windows dan macOS: data disimpan di folder `Data`
  di sebelah aplikasi, sehingga seluruh pembukuan ikut berpindah bersama
  flashdisk dan komputer yang dipakai tidak ditulisi apa pun.
- Dukungan **macOS**: bundel `.app`, berkas `.dmg`, ikon `.icns`, dan skrip
  `build_mac.sh`.
- Alur kerja GitHub Actions membangun kelima berkas sekaligus dan menerbitkan
  Release otomatis saat diberi tag.

**1.0.1**
- Perbaikan: mencetak laporan tidak lagi gagal bila berkas PDF/Excel hasil
  cetak sebelumnya masih terbuka di layar. Program otomatis menyimpan dengan
  nama bercadangan — `... (2).pdf`, `... (3).pdf` — dan baru memakai kembali
  nama aslinya setelah berkas lama ditutup.
- Pesan galat teknis kini diterjemahkan menjadi penjelasan berbahasa Indonesia
  beserta cara mengatasinya.

**1.0.0**
- Rilis pertama.
