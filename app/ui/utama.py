"""Jendela utama Program Pembukuan Kantin Koperasi."""
from __future__ import annotations

import os
import sys
import tkinter as tk
from datetime import date
from tkinter import filedialog, ttk

from .. import db, engine, pdfout, xlsio
from . import widgets as w
from .tab_data import TabAkun, TabSaldoAwal
from .tab_jurnal import TabJurnal
from .tab_kas import TabKas
from .tab_persediaan import TabPersediaan
from .tab_laporan import TabBukuBesar, TabLaporan, TabNeracaLajur

PANDUAN = """PANDUAN SINGKAT PEMAKAIAN

YANG PERLU DIISI PETUGAS HANYA DUA TAB
   1. Tab "Buku Kas"    — setiap uang masuk dan uang keluar
   2. Tab "Persediaan"  — setiap barang datang dan barang terjual

   Dari dua catatan itu program menyusun sendiri jurnal, buku besar, neraca
   lajur, sampai laporan keuangan. Tidak perlu tahu debit maupun kredit.


1. MENCATAT UANG  (tab Buku Kas)
   Tombol hijau "UANG MASUK" untuk uang yang diterima, tombol merah
   "UANG KELUAR" untuk uang yang dikeluarkan. Isi tanggal, pilih "Untuk apa?"
   dari daftar yang sudah diberi penjelasan, tulis keterangan, isi jumlahnya.

   Pembelian barang dagangan TIDAK dicatat di sini — catat di tab Persediaan,
   buku kas akan terisi sendiri.

2. MENCATAT BARANG  (tab Persediaan)
   "BARANG MASUK"  : barang datang. Isi jumlah unit dan harga beli per unit.
                     Pilih dibayar tunai atau belum dibayar (utang pemasok).
   "BARANG KELUAR" : barang terjual. CUKUP ISI JUMLAH UNITNYA. Harga pokok
                     dihitung sendiri oleh program dari rata-rata harga beli.
   "Penjualan dibayar menyusul" : seragam diambil siswa, dibayar belakangan.
                     Piutang bertambah dan stok berkurang sekaligus.
   "Penyesuaian stok" : barang rusak, hilang, atau hasil hitung fisik berbeda.
                     Beri tanda minus bila stok berkurang.

   Dua jenis barang disediakan: Seragam & ATK, serta Makanan & Minuman.

3. PERSEDIAAN DAN HARGA POKOK
   Persediaan dicatat secara PERPETUAL dengan harga pokok rata-rata bergerak.
   Setiap barang masuk dengan harga berbeda, rata-ratanya dihitung ulang;
   setiap barang keluar, harga pokoknya diambil dari rata-rata saat itu dan
   langsung masuk ke Laporan Laba Rugi. Tidak perlu stock opname bulanan,
   cukup Penyesuaian stok bila hitungan fisik berbeda dari catatan.

       Uang hasil penjualan  −  Harga pokok barang terjual  =  Laba kotor
       Laba kotor  −  Beban (gaji, listrik, dsb)            =  SHU

4. LAPORAN DAN CETAK PDF
   Tab "Laporan Keuangan" berisi Laba Rugi, Perubahan Modal, Laporan Posisi
   Keuangan, Arus Kas, dan Rekap Penjualan Harian. Tombol "Cetak Laporan Ini"
   mencetak laporan yang sedang dibuka; "Cetak Semua Laporan (1 PDF)"
   menggabungkan seluruh laporan bulanan jadi satu berkas siap dilampirkan ke
   RAT. Buku Kas dan Kartu Persediaan juga punya tombol cetaknya sendiri.

5. JURNAL PENYESUAIAN AKHIR BULAN  (tab Jurnal)
   Untuk hal yang tidak lewat kas maupun persediaan, dan memang harus
   ditimbang di akhir bulan. Tersedia empat tombol yang mengisi akunnya
   sendiri dan langsung menyetel jenis jurnal ke AJP:

       Penyusutan peralatan       Beban Penyusutan / Akum. Penyusutan
       Beban belum dibayar        Beban ybs / Beban yang Masih Harus Dibayar
       Pendapatan belum diterima  Pendapatan ybs Masih Harus Diterima / Penjualan
       Pemakaian perlengkapan     Beban ATK & Perlengkapan / Perlengkapan

   Seluruh catatan dari Buku Kas dan Persediaan juga tampil di tab ini,
   lengkap dengan keterangan asalnya, sehingga bisa diperiksa pengurus.

6. TUTUP BUKU
   Tab "Tutup Buku" memeriksa kesiapan, lalu mengunci periode dan membuat
   saldo awal bulan berikutnya secara otomatis — termasuk memindahkan SHU ke
   akun Laba Ditahan dan membawa sisa stok. Tidak perlu jurnal penutup manual.
   Bila ada koreksi, gunakan "Buka Kembali Periode".

7. DATA DAN CADANGAN
   Seluruh data tersimpan di satu berkas basis data (menu Berkas → Lokasi
   Data, yang juga menunjukkan apakah program berjalan mode portable).
   Lakukan "Cadangkan Data" secara berkala, misalnya tiap selesai tutup buku,
   dan simpan salinannya di flashdisk atau penyimpanan awan.
"""


class TabBeranda(ttk.Frame):
    def __init__(self, induk, aplikasi):
        super().__init__(induk, padding=12)
        self.app = aplikasi

        ttk.Label(self, text="Beranda", style="Judul.TLabel").pack(anchor="w")
        self.lbl_periode = ttk.Label(self, text="", style="Sub.TLabel")
        self.lbl_periode.pack(anchor="w", pady=(2, 10))

        kartu = ttk.Frame(self)
        kartu.pack(fill="x")
        self.kartu = {}
        for kunci, judul in (("kas", "Saldo Kas"), ("bank", "Saldo Bank"),
                             ("persediaan", "Persediaan Barang"), ("pendapatan", "Penjualan Bulan Ini"),
                             ("shu", "SHU Bulan Ini"), ("aktiva", "Total Aktiva")):
            k = w.Kartu(kartu, judul)
            k.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.kartu[kunci] = k

        self.lbl_status = ttk.Label(self, text="", style="Tebal.TLabel")
        self.lbl_status.pack(anchor="w", pady=(12, 6))

        aksi = ttk.Labelframe(self, text="Aksi cepat", padding=10)
        aksi.pack(fill="x", pady=(4, 10))
        tombol = [
            ("💵  Catat Uang Masuk / Keluar", lambda: self.app.buka_tab("Buku Kas"),
             "Utama.TButton"),
            ("📦  Catat Barang Masuk / Keluar", lambda: self.app.buka_tab("Persediaan"),
             "TButton"),
            ("📊  Lihat Laporan Keuangan", lambda: self.app.buka_tab("Laporan Keuangan"), "TButton"),
            ("🖨  Cetak Semua Laporan (PDF)", self.app.cetak_paket, "TButton"),
            ("🔒  Tutup Buku Bulan Ini", lambda: self.app.buka_tab("Tutup Buku"), "TButton"),
        ]
        for teks, perintah, gaya in tombol:
            ttk.Button(aksi, text=teks, command=perintah, style=gaya).pack(side="left", padx=(0, 8))

        bawah = ttk.Frame(self)
        bawah.pack(fill="both", expand=True)
        kiri = ttk.Labelframe(bawah, text="Transaksi terakhir", padding=8)
        kiri.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.tabel = w.buat_tabel(kiri, [("tgl", "Tanggal", 90, "center"),
                                         ("ket", "Keterangan", 330, "w"),
                                         ("nilai", "Nilai", 120, "e")], tinggi=9)
        kanan = ttk.Labelframe(bawah, text="Langkah kerja bulanan", padding=10)
        kanan.pack(side="left", fill="both")
        langkah = ["1.  Catat semua transaksi di tab Jurnal",
                   "2.  Periksa mutasi di tab Buku Besar",
                   "3.  Isi stock opname di tab Neraca Lajur",
                   "4.  Baca & cetak Laporan Keuangan",
                   "5.  Jalankan Tutup Buku",
                   "6.  Cadangkan data (menu Berkas)"]
        for teks in langkah:
            ttk.Label(kanan, text=teks).pack(anchor="w", pady=2)

    def muat(self):
        r = engine.ringkasan(self.app.periode_id)
        p = r["periode"]
        self.lbl_periode.configure(
            text=f"Periode {engine.nama_periode(p['tahun'], p['bulan'])} · "
                 f"status {'DITUTUP' if p['status'] == 'TUTUP' else 'AKTIF'} · "
                 f"{r['jumlah_transaksi']} transaksi tercatat")
        self.kartu["kas"].set(w.rp_lengkap(r["kas"]))
        self.kartu["bank"].set(w.rp_lengkap(r["bank"]))
        self.kartu["persediaan"].set(w.rp_lengkap(r["persediaan"]))
        self.kartu["pendapatan"].set(w.rp_lengkap(r["pendapatan"]), w.HIJAU)
        self.kartu["shu"].set(w.rp_lengkap(r["shu"]), w.HIJAU if r["shu"] >= 0 else w.MERAH)
        self.kartu["aktiva"].set(w.rp_lengkap(r["total_aktiva"]))
        if r["seimbang"]:
            teks, warna = "Pembukuan BALANCE ✓  (debit = kredit, aktiva = kewajiban + modal)", w.HIJAU
        else:
            teks, warna = ("Pembukuan TIDAK BALANCE — periksa jurnal dan saldo awal.", w.MERAH)
        if not r["opname_diisi"]:
            teks += "   •   Stock opname bulan ini belum diisi (HPP belum memperhitungkan barang terjual)."
        self.lbl_status.configure(text=teks, foreground=warna)

        daftar = engine.daftar_jurnal(self.app.periode_id)[-9:][::-1]
        baris = []
        for j in daftar:
            nilai = sum(d["debit"] for d in engine.detail_jurnal(j["id"]))
            baris.append([w.tgl_id(j["tanggal"]), j["keterangan"] or "", w.rp(nilai)])
        w.isi_tabel(self.tabel, baris)


class TabTutupBuku(ttk.Frame):
    def __init__(self, induk, aplikasi):
        super().__init__(induk, padding=12)
        self.app = aplikasi

        ttk.Label(self, text="Tutup Buku", style="Judul.TLabel").pack(anchor="w")
        ttk.Label(self, text="Mengunci periode berjalan dan menyiapkan saldo awal bulan "
                             "berikutnya secara otomatis.", style="Sub.TLabel").pack(anchor="w")

        kotak = ttk.Labelframe(self, text="Pemeriksaan kesiapan", padding=10)
        kotak.pack(fill="x", pady=(12, 8))
        self.lbl_cek = ttk.Label(kotak, text="", justify="left", wraplength=980)
        self.lbl_cek.pack(anchor="w")

        ringkas = ttk.Labelframe(self, text="Ringkasan periode berjalan", padding=10)
        ringkas.pack(fill="x", pady=(0, 8))
        self.lbl_ringkas = ttk.Label(ringkas, text="", justify="left")
        self.lbl_ringkas.pack(anchor="w")

        aksi = ttk.Frame(self)
        aksi.pack(fill="x", pady=(4, 12))
        self.btn_tutup = ttk.Button(aksi, text="🔒  Tutup Buku Periode Ini", style="Hijau.TButton",
                                    command=self.tutup)
        self.btn_tutup.pack(side="left")
        self.btn_buka = ttk.Button(aksi, text="🔓  Buka Kembali Periode", style="Bahaya.TButton",
                                   command=self.buka)
        self.btn_buka.pack(side="left", padx=(8, 0))
        ttk.Button(aksi, text="💾  Cadangkan Data Dulu",
                   command=self.app.cadangkan).pack(side="left", padx=(8, 0))

        riwayat = ttk.Labelframe(self, text="Riwayat periode", padding=8)
        riwayat.pack(fill="both", expand=True)
        self.tabel = w.buat_tabel(riwayat, [("periode", "Periode", 160, "center"),
                                            ("status", "Status", 110, "center"),
                                            ("tutup", "Waktu Tutup Buku", 180, "center"),
                                            ("trx", "Jumlah Transaksi", 140, "center"),
                                            ("shu", "SHU", 150, "e"),
                                            ("aktiva", "Total Aktiva", 160, "e")], tinggi=10)

    def muat(self):
        p = engine.periode(self.app.periode_id)
        nama = engine.nama_periode(p["tahun"], p["bulan"])
        masalah = engine.cek_siap_tutup(self.app.periode_id)
        nl = engine.neraca_lajur(self.app.periode_id)
        lr = engine.laba_rugi(self.app.periode_id, nl)
        n = engine.neraca(self.app.periode_id, nl)

        if p["status"] == "TUTUP":
            self.lbl_cek.configure(
                text=f"Periode {nama} sudah ditutup pada {p['tanggal_tutup'] or '-'}.\n"
                     "Jurnal periode ini terkunci. Gunakan tombol 'Buka Kembali Periode' "
                     "bila ada koreksi.", foreground=w.ORANYE)
        elif masalah:
            self.lbl_cek.configure(text="Belum siap ditutup:\n" +
                                   "\n".join("   ✗  " + m for m in masalah), foreground=w.MERAH)
        else:
            catatan = ("" if nl["opname_diisi"] else
                       "\n   ⚠  Stock opname belum diisi — HPP dihitung tanpa perubahan "
                       "persediaan. Sebaiknya isi dulu di tab Neraca Lajur.")
            self.lbl_cek.configure(
                text=f"Siap ditutup:\n   ✓  Jurnal balance\n   ✓  Posisi keuangan balance\n"
                     f"   ✓  Periode sebelumnya sudah beres{catatan}", foreground=w.HIJAU)

        berikut = "Januari %d" % (p["tahun"] + 1) if p["bulan"] == 12 else \
            f"{db.NAMA_BULAN[p['bulan'] + 1]} {p['tahun']}"
        self.lbl_ringkas.configure(
            text=(f"Periode              : {nama}\n"
                  f"Pendapatan bersih    : {w.rp_lengkap(lr['total_pendapatan'])}\n"
                  f"Harga pokok penjualan: {w.rp_lengkap(lr['hpp'])}\n"
                  f"Beban operasional    : {w.rp_lengkap(lr['total_beban'])}\n"
                  f"SHU / laba bersih    : {w.rp_lengkap(lr['shu'])}  → otomatis masuk "
                  f"akun Laba Ditahan\n"
                  f"Total aktiva         : {w.rp_lengkap(n['total_aktiva'])}\n"
                  f"Persediaan akhir     : {w.rp_lengkap(nl['persediaan_akhir'])}"
                  f"{'  (hasil opname)' if nl['opname_diisi'] else '  (belum opname)'}\n"
                  f"Setelah tutup buku   : saldo akhir seluruh akun neraca menjadi saldo awal "
                  f"{berikut}."))
        self.btn_tutup.state(["disabled"] if (masalah or p["status"] == "TUTUP") else ["!disabled"])
        self.btn_buka.state(["!disabled"] if p["status"] == "TUTUP" else ["disabled"])

        baris, tag = [], {}
        for i, per in enumerate(engine.daftar_periode()):
            jml = db.koneksi().execute("SELECT count(*) c FROM jurnal WHERE periode_id=?",
                                       (per["id"],)).fetchone()["c"]
            r = engine.ringkasan(per["id"])
            baris.append([engine.nama_periode(per["tahun"], per["bulan"]),
                          "Ditutup" if per["status"] == "TUTUP" else "Aktif",
                          (per["tanggal_tutup"] or "-").replace("T", " "), jml,
                          w.rp(r["shu"]), w.rp(r["total_aktiva"])])
            if per["id"] == self.app.periode_id:
                tag[i] = "judul"
        w.isi_tabel(self.tabel, baris, tag)

    def tutup(self):
        p = engine.periode(self.app.periode_id)
        nama = engine.nama_periode(p["tahun"], p["bulan"])
        if not w.tanya("Konfirmasi tutup buku",
                       f"Periode {nama} akan DITUTUP:\n\n"
                       "• jurnal periode ini dikunci (tidak bisa diubah),\n"
                       "• SHU dipindahkan ke akun Laba Ditahan,\n"
                       "• saldo akhir menjadi saldo awal bulan berikutnya.\n\n"
                       "Disarankan mencadangkan data lebih dulu. Lanjutkan?", self):
            return
        try:
            hasil = engine.tutup_buku(self.app.periode_id)
        except ValueError as e:
            w.galat("Tutup buku dibatalkan", str(e), self)
            return
        b = hasil["berikut"]
        w.info("Tutup buku selesai",
               f"Periode {nama} berhasil ditutup.\n\n"
               f"SHU: {w.rp_lengkap(hasil['shu'])}\n"
               f"Total aktiva: {w.rp_lengkap(hasil['total_aktiva'])}\n\n"
               f"Periode {engine.nama_periode(b['tahun'], b['bulan'])} sudah dibuat dan "
               "siap diisi transaksi.", self)
        self.app.pilih_periode(b["id"])

    def buka(self):
        p = engine.periode(self.app.periode_id)
        nama = engine.nama_periode(p["tahun"], p["bulan"])
        if not w.tanya("Buka kembali periode",
                       f"Periode {nama} akan dibuka kembali.\n\n"
                       "Saldo awal periode berikutnya akan dihapus dan dibuat ulang "
                       "saat Anda menutup buku lagi. Lanjutkan?", self):
            return
        try:
            engine.batal_tutup_buku(self.app.periode_id)
        except ValueError as e:
            w.galat("Tidak bisa dibuka", str(e), self)
            return
        self.app.segarkan(muat_ulang_periode=True)


class DialogPengaturan(tk.Toplevel):
    KOLOM = [("nama_koperasi", "Nama Koperasi"), ("unit_usaha", "Unit Usaha"),
             ("alamat", "Alamat"), ("kota", "Kota (untuk tanda tangan)"),
             ("ketua", "Nama Ketua"), ("bendahara", "Nama Bendahara / Petugas")]

    def __init__(self, induk):
        super().__init__(induk)
        self.title("Identitas Koperasi")
        self.configure(bg=w.ABU)
        self.transient(induk)
        isi = ttk.Frame(self, padding=16)
        isi.pack(fill="both", expand=True)
        self.var = {}
        for i, (kunci, label) in enumerate(self.KOLOM):
            ttk.Label(isi, text=label).grid(row=i, column=0, sticky="w", pady=5, padx=(0, 12))
            self.var[kunci] = tk.StringVar(value=db.ambil_pengaturan(kunci))
            ttk.Entry(isi, textvariable=self.var[kunci], width=46).grid(row=i, column=1,
                                                                       sticky="w", pady=5)
        ttk.Label(isi, text="Data ini dipakai sebagai kop dan blok tanda tangan pada semua PDF.",
                  style="Sub.TLabel").grid(row=len(self.KOLOM), column=0, columnspan=2,
                                           sticky="w", pady=(10, 0))
        bawah = ttk.Frame(self, padding=(16, 0, 16, 14))
        bawah.pack(fill="x")
        ttk.Button(bawah, text="Batal", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(bawah, text="Simpan", style="Utama.TButton",
                   command=self._simpan).pack(side="right")
        self.grab_set()

    def _simpan(self):
        for kunci, _ in self.KOLOM:
            db.simpan_pengaturan(kunci, self.var[kunci].get().strip())
        self.destroy()


class Aplikasi(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"Program Pembukuan Kantin Koperasi  v{db.VERSI_APLIKASI}")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        w.pasang_gaya(self)
        self.configure(bg=w.ABU)
        ikon_ico = os.path.join(db.folder_program(), "assets", "ikon.ico")
        if sys.platform.startswith("win") and os.path.exists(ikon_ico):
            try:
                self.iconbitmap(ikon_ico)
            except tk.TclError:
                pass
        ikon = os.path.join(db.folder_program(), "assets", "ikon.png")
        if os.path.exists(ikon):
            try:
                self._gambar_ikon = tk.PhotoImage(file=ikon)
                self.iconphoto(True, self._gambar_ikon)
            except tk.TclError:
                pass

        self.periode_id = engine.periode_berjalan()["id"]
        self.var_periode = tk.StringVar()
        self._menu()
        self._kop()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(6, 10))
        # Urutan tab mengikuti alur kerja sehari-hari: dua tab pencatatan
        # lebih dulu, baru hasil olahannya, lalu pengaturan dan tutup buku.
        self.tab = {
            "Beranda": TabBeranda(self.notebook, self),
            "Buku Kas": TabKas(self.notebook, self),
            "Persediaan": TabPersediaan(self.notebook, self),
            "Jurnal": TabJurnal(self.notebook, self),
            "Buku Besar": TabBukuBesar(self.notebook, self),
            "Neraca Lajur": TabNeracaLajur(self.notebook, self),
            "Laporan Keuangan": TabLaporan(self.notebook, self),
            "Daftar Akun": TabAkun(self.notebook, self),
            "Saldo Awal": TabSaldoAwal(self.notebook, self),
            "Tutup Buku": TabTutupBuku(self.notebook, self),
        }
        for nama, bingkai in self.tab.items():
            self.notebook.add(bingkai, text=f"  {nama}  ")
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self._tab_aktif_muat())

        self.protocol("WM_DELETE_WINDOW", self.keluar)
        self.segarkan(muat_ulang_periode=True)

    # ------------------------------------------------------------------ menu #
    def _menu(self):
        bar = tk.Menu(self)
        berkas = tk.Menu(bar, tearoff=0)
        berkas.add_command(label="Cadangkan Data…", command=self.cadangkan)
        berkas.add_command(label="Pulihkan dari Cadangan…", command=self.pulihkan)
        berkas.add_separator()
        berkas.add_command(label="Buka Folder Laporan",
                           command=lambda: w.buka_berkas(db.folder_keluaran()))
        berkas.add_command(label="Lokasi Data…", command=self.lokasi_data)
        berkas.add_separator()
        berkas.add_command(label="Keluar", command=self.keluar)
        bar.add_cascade(label="Berkas", menu=berkas)

        data = tk.Menu(bar, tearoff=0)
        data.add_command(label="Input Transaksi Jurnal",
                         command=lambda: self.buka_tab("Jurnal", "input"))
        data.add_command(label="Impor Jurnal dari Excel",
                         command=lambda: self.buka_tab("Jurnal", "impor"))
        data.add_command(label="Unduh Template Impor",
                         command=lambda: self.buka_tab("Jurnal", "template"))
        data.add_separator()
        data.add_command(label="Daftar Akun (COA)", command=lambda: self.buka_tab("Daftar Akun"))
        data.add_command(label="Saldo Awal", command=lambda: self.buka_tab("Saldo Awal"))
        data.add_command(label="Tambah Periode Baru…", command=self.tambah_periode)
        bar.add_cascade(label="Data", menu=data)

        laporan = tk.Menu(bar, tearoff=0)
        for label, fungsi in (("Jurnal Umum", pdfout.cetak_jurnal_umum),
                              ("Rekap Buku Besar", pdfout.cetak_rekap_buku_besar),
                              ("Neraca Lajur", pdfout.cetak_neraca_lajur),
                              ("Laba Rugi", pdfout.cetak_laba_rugi),
                              ("Perubahan Modal", pdfout.cetak_perubahan_modal),
                              ("Laporan Posisi Keuangan", pdfout.cetak_neraca),
                              ("Arus Kas", pdfout.cetak_arus_kas),
                              ("Rekap Penjualan Harian", pdfout.cetak_rekap_penjualan)):
            laporan.add_command(label=f"Cetak PDF — {label}",
                                command=lambda f=fungsi: self._cetak(f))
        laporan.add_separator()
        laporan.add_command(label="Cetak Semua Laporan (1 PDF)", command=self.cetak_paket)
        laporan.add_command(label="Ekspor Semua ke Excel", command=self.ekspor_excel)
        bar.add_cascade(label="Laporan", menu=laporan)

        proses = tk.Menu(bar, tearoff=0)
        proses.add_command(label="Tutup Buku Periode Ini",
                           command=lambda: self.buka_tab("Tutup Buku"))
        proses.add_command(label="Pengaturan Identitas Koperasi…", command=self.pengaturan)
        bar.add_cascade(label="Proses", menu=proses)

        bantuan = tk.Menu(bar, tearoff=0)
        bantuan.add_command(label="Panduan Pemakaian", command=self.panduan)
        bantuan.add_command(label="Tentang Program", command=self.tentang)
        bar.add_cascade(label="Bantuan", menu=bantuan)
        self.config(menu=bar)

    def _kop(self):
        kop = ttk.Frame(self, style="Kop.TFrame", padding=(14, 10))
        kop.pack(fill="x")
        kiri = ttk.Frame(kop, style="Kop.TFrame")
        kiri.pack(side="left")
        self.lbl_nama = ttk.Label(kiri, text=db.ambil_pengaturan("nama_koperasi"),
                                  style="Kop.TLabel")
        self.lbl_nama.pack(anchor="w")
        self.lbl_unit = ttk.Label(kiri, text=db.ambil_pengaturan("unit_usaha"),
                                  style="KopKecil.TLabel")
        self.lbl_unit.pack(anchor="w")

        kanan = ttk.Frame(kop, style="Kop.TFrame")
        kanan.pack(side="right")
        ttk.Label(kanan, text="Periode aktif", style="KopKecil.TLabel").pack(anchor="e")
        pilih = ttk.Frame(kanan, style="Kop.TFrame")
        pilih.pack(anchor="e", pady=(2, 0))
        self.combo_periode = ttk.Combobox(pilih, textvariable=self.var_periode, width=22,
                                          state="readonly")
        self.combo_periode.pack(side="left")
        self.combo_periode.bind("<<ComboboxSelected>>", self._ganti_periode)
        self.lbl_kunci = ttk.Label(pilih, text="", style="KopKecil.TLabel")
        self.lbl_kunci.pack(side="left", padx=(10, 0))

    # -------------------------------------------------------------- periode  #
    def _muat_periode(self):
        self.periode_daftar = engine.daftar_periode()
        nilai = [f"{engine.nama_periode(p['tahun'], p['bulan'])}"
                 f"{'  (ditutup)' if p['status'] == 'TUTUP' else ''}"
                 for p in self.periode_daftar]
        self.combo_periode.configure(values=nilai)
        for i, p in enumerate(self.periode_daftar):
            if p["id"] == self.periode_id:
                self.var_periode.set(nilai[i])
                break
        else:
            if self.periode_daftar:
                self.periode_id = self.periode_daftar[0]["id"]
                self.var_periode.set(nilai[0])

    def _ganti_periode(self, _=None):
        i = self.combo_periode.current()
        if 0 <= i < len(self.periode_daftar):
            self.periode_id = self.periode_daftar[i]["id"]
            self.segarkan()

    def pilih_periode(self, periode_id: int):
        self.periode_id = periode_id
        self.segarkan(muat_ulang_periode=True)

    def tambah_periode(self):
        akhir = engine.daftar_periode()[-1] if engine.daftar_periode() else None
        th, bl = (date.today().year, date.today().month) if akhir is None else (
            (akhir["tahun"] + 1, 1) if akhir["bulan"] == 12 else (akhir["tahun"], akhir["bulan"] + 1))
        if not w.tanya("Tambah periode",
                       f"Tambahkan periode {engine.nama_periode(th, bl)}?\n\n"
                       "Catatan: saldo awal periode baru biasanya terisi otomatis lewat "
                       "proses Tutup Buku bulan sebelumnya.", self):
            return
        p = engine.tambah_periode(th, bl)
        self.pilih_periode(p["id"])

    # -------------------------------------------------------------- tindakan #
    def buka_tab(self, nama: str, aksi: str | None = None):
        self.notebook.select(list(self.tab.keys()).index(nama))
        tab = self.tab[nama]
        if aksi == "input":
            self.after(60, tab.input_baru)
        elif aksi == "impor":
            self.after(60, tab.impor)
        elif aksi == "template":
            self.after(60, tab.unduh_template)

    def _tab_aktif_muat(self):
        try:
            nama = list(self.tab.keys())[self.notebook.index(self.notebook.select())]
        except tk.TclError:
            return
        self.tab[nama].muat()

    def segarkan(self, muat_ulang_periode: bool = False):
        if muat_ulang_periode:
            self._muat_periode()
        p = engine.periode(self.periode_id)
        if p is None:
            self.periode_id = engine.periode_berjalan()["id"]
            self._muat_periode()
            p = engine.periode(self.periode_id)
        self.lbl_kunci.configure(text="🔒 ditutup" if p["status"] == "TUTUP" else "✎ dapat diisi")
        self.lbl_nama.configure(text=db.ambil_pengaturan("nama_koperasi"))
        self.lbl_unit.configure(text=db.ambil_pengaturan("unit_usaha"))
        self._tab_aktif_muat()

    def _cetak(self, fungsi):
        try:
            path = fungsi(self.periode_id)
        except Exception as e:
            w.galat("Gagal mencetak", str(e), self)
            return
        w.selesai_cetak(path, self)

    def cetak_paket(self):
        try:
            path = pdfout.cetak_paket_lengkap(self.periode_id)
        except Exception as e:
            w.galat("Gagal mencetak", str(e), self)
            return
        w.selesai_cetak(path, self)

    def ekspor_excel(self):
        p = engine.periode(self.periode_id)
        path = xlsio.nama_berkas_excel("Laporan_Bulanan", p)
        xlsio.ekspor_laporan_excel(self.periode_id, path)
        w.selesai_cetak(path, self)

    def cadangkan(self):
        bawaan = os.path.join(db.folder_data(), "backup",
                              f"kantin_{date.today().isoformat()}.db")
        path = filedialog.asksaveasfilename(
            parent=self, title="Simpan cadangan data", defaultextension=".db",
            initialfile=os.path.basename(bawaan), initialdir=os.path.dirname(bawaan),
            filetypes=[("Basis data", "*.db")])
        if not path:
            return
        db.buat_cadangan(path)
        w.info("Cadangan dibuat", f"Data berhasil dicadangkan ke:\n\n{path}\n\n"
                                  "Simpan juga salinannya di flashdisk atau penyimpanan awan.",
               self)

    def pulihkan(self):
        path = filedialog.askopenfilename(parent=self, title="Pilih berkas cadangan",
                                          filetypes=[("Basis data", "*.db")])
        if not path:
            return
        if not w.tanya("Pulihkan data",
                       "Seluruh data saat ini akan DIGANTI dengan isi berkas cadangan.\n"
                       "(Data lama otomatis dicadangkan lebih dulu.)\n\nLanjutkan?", self):
            return
        try:
            db.pulihkan_cadangan(path)
        except Exception as e:
            w.galat("Gagal memulihkan", str(e), self)
            return
        self.periode_id = engine.periode_berjalan()["id"]
        self.segarkan(muat_ulang_periode=True)
        w.info("Selesai", "Data berhasil dipulihkan dari cadangan.", self)

    def lokasi_data(self):
        if db.mode_portable():
            mode = ("Mode: PORTABLE\n"
                    "Seluruh data tersimpan di folder 'Data' di sebelah aplikasi, "
                    "sehingga ikut berpindah bila aplikasi disalin ke flashdisk "
                    "atau komputer lain.\n\n")
        else:
            mode = ("Mode: TERPASANG\n"
                    "Data tersimpan di folder pengguna komputer ini, terpisah dari "
                    "berkas program, sehingga tetap aman walau program diperbarui "
                    "atau dihapus.\n\n")
        w.info("Lokasi data",
               mode +
               f"Basis data:\n{db.path_db()}\n\nFolder laporan:\n{db.folder_keluaran()}\n\n"
               "Salin berkas basis data bila ingin memindahkan pembukuan ke komputer lain.",
               self)

    def pengaturan(self):
        d = DialogPengaturan(self)
        self.wait_window(d)
        self.segarkan()

    def panduan(self):
        jendela = tk.Toplevel(self)
        jendela.title("Panduan Pemakaian")
        jendela.geometry("860x620")
        jendela.configure(bg=w.ABU)
        bingkai = ttk.Frame(jendela, padding=12)
        bingkai.pack(fill="both", expand=True)
        teks = tk.Text(bingkai, wrap="word", font=(w.keluarga_font(), 10), relief="flat",
                       bg=w.PUTIH, padx=14, pady=12)
        gulir = ttk.Scrollbar(bingkai, orient="vertical", command=teks.yview)
        teks.configure(yscrollcommand=gulir.set)
        teks.pack(side="left", fill="both", expand=True)
        gulir.pack(side="right", fill="y")
        teks.insert("1.0", PANDUAN)
        teks.configure(state="disabled")

    def tentang(self):
        w.info("Tentang Program",
               f"Program Pembukuan Kantin Koperasi\nVersi {db.VERSI_APLIKASI}\n\n"
               "Sistem akuntansi usaha dagang: jurnal, buku besar, neraca lajur, "
               "laba rugi, perubahan modal, neraca, arus kas, dan tutup buku bulanan.\n\n"
               f"Mode: {'PORTABLE' if db.mode_portable() else 'Terpasang'}\n"
               f"Data tersimpan di: {db.folder_data()}", self)

    def keluar(self):
        try:
            db.buat_cadangan()      # cadangan otomatis saat menutup program
        except Exception:
            pass
        db.tutup_koneksi()
        self.destroy()


def jalankan():
    db.koneksi()
    Aplikasi().mainloop()
