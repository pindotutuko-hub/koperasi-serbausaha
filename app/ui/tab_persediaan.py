"""Tab Persediaan — mutasi barang masuk dan keluar secara perpetual.

Petugas cukup mencatat barang datang (berapa unit, berapa harganya) dan
barang terjual (cukup berapa unit). Harga pokok dihitung sendiri oleh
program dengan rata-rata bergerak, lalu mengalir ke laporan laba rugi.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import engine, kasbuku
from . import widgets as w


class DialogMutasi(tk.Toplevel):
    """Form barang masuk, barang keluar, atau penyesuaian stok."""

    JUDUL = {
        "MASUK": ("BARANG MASUK", "Barang datang dari pemasok", "#1E7B34"),
        "KELUAR": ("BARANG KELUAR", "Barang terjual atau terpakai", "#B26B00"),
        "PENYESUAIAN": ("PENYESUAIAN STOK", "Hasil hitung fisik, rusak, atau hilang", "#1F4E79"),
    }

    def __init__(self, induk, aplikasi, arah: str, jenis_id: int | None = None,
                 mutasi_id: int | None = None):
        super().__init__(induk)
        self.aplikasi = aplikasi
        self.arah = arah
        self.mutasi_id = mutasi_id

        judul, sub, warna = self.JUDUL[arah]
        self.title(judul.title())
        self.resizable(False, False)
        self.transient(induk)
        self.configure(bg=w.ABU)

        kop = tk.Frame(self, bg=warna)
        kop.pack(fill="x")
        tk.Label(kop, text=judul, bg=warna, fg="white",
                 font=(w.keluarga_font(), 13, "bold"),
                 padx=16, pady=10).pack(side="left")
        tk.Label(kop, text=sub, bg=warna, fg="#E8EEF5", padx=4, pady=12).pack(side="left")

        isi = ttk.Frame(self, padding=16)
        isi.pack(fill="both", expand=True)
        isi.columnconfigure(1, weight=1)

        b = 0
        ttk.Label(isi, text="Tanggal").grid(row=b, column=0, sticky="w", pady=6)
        self.tgl = w.EntriTanggal(isi)
        self.tgl.grid(row=b, column=1, sticky="w", pady=6)

        b += 1
        ttk.Label(isi, text="Jenis barang").grid(row=b, column=0, sticky="w", pady=6)
        self.jenis = kasbuku.daftar_jenis()
        self.var_jenis = tk.StringVar()
        self.peta_jenis = {j["nama"]: j for j in self.jenis}
        self.cb_jenis = ttk.Combobox(isi, textvariable=self.var_jenis,
                                     values=[j["nama"] for j in self.jenis],
                                     state="readonly", width=34)
        self.cb_jenis.grid(row=b, column=1, sticky="w", pady=6)
        self.cb_jenis.bind("<<ComboboxSelected>>", lambda e: self._info_stok())
        if jenis_id:
            for j in self.jenis:
                if j["id"] == jenis_id:
                    self.var_jenis.set(j["nama"])
        elif self.jenis:
            self.var_jenis.set(self.jenis[0]["nama"])

        b += 1
        self.lbl_stok = ttk.Label(isi, text="", style="Sub.TLabel")
        self.lbl_stok.grid(row=b, column=1, sticky="w")

        b += 1
        ttk.Label(isi, text="Keterangan").grid(row=b, column=0, sticky="w", pady=6)
        self.var_ket = tk.StringVar()
        ttk.Entry(isi, textvariable=self.var_ket, width=46).grid(
            row=b, column=1, sticky="ew", pady=6)

        b += 1
        teks_jumlah = {"MASUK": "Berapa unit masuk?",
                       "KELUAR": "Berapa unit keluar?",
                       "PENYESUAIAN": "Selisih unit"}[arah]
        ttk.Label(isi, text=teks_jumlah).grid(row=b, column=0, sticky="w", pady=6)
        baris_j = ttk.Frame(isi)
        baris_j.grid(row=b, column=1, sticky="w", pady=6)
        self.jml = w.EntriAngka(baris_j, lebar=12, font=(w.keluarga_font(), 12),
                                saat_ubah=self._hitung)
        self.jml.pack(side="left")
        self.lbl_satuan = ttk.Label(baris_j, text="unit", style="Sub.TLabel")
        self.lbl_satuan.pack(side="left", padx=(8, 0))
        if arah == "PENYESUAIAN":
            ttk.Label(baris_j, style="Sub.TLabel",
                      text="  (beri tanda minus bila stok berkurang)").pack(side="left")

        if arah == "MASUK":
            b += 1
            ttk.Label(isi, text="Harga beli per unit").grid(row=b, column=0, sticky="w", pady=6)
            baris_h = ttk.Frame(isi)
            baris_h.grid(row=b, column=1, sticky="w", pady=6)
            ttk.Label(baris_h, text="Rp").pack(side="left", padx=(0, 6))
            self.harga = w.EntriAngka(baris_h, lebar=14, font=(w.keluarga_font(), 12),
                                      saat_ubah=self._hitung)
            self.harga.pack(side="left")

            b += 1
            ttk.Label(isi, text="Dibayar").grid(row=b, column=0, sticky="w", pady=6)
            self.var_bayar = tk.StringVar(value="TUNAI")
            rb = ttk.Frame(isi)
            rb.grid(row=b, column=1, sticky="w", pady=6)
            ttk.Radiobutton(rb, text="Tunai sekarang", value="TUNAI",
                            variable=self.var_bayar).pack(side="left")
            ttk.Radiobutton(rb, text="Belum dibayar (utang ke pemasok)", value="UTANG",
                            variable=self.var_bayar).pack(side="left", padx=(16, 0))

        b += 1
        self.lbl_hasil = ttk.Label(isi, text="", style="Tebal.TLabel", foreground=w.BIRU)
        self.lbl_hasil.grid(row=b, column=0, columnspan=2, sticky="w", pady=(12, 0))

        kaki = ttk.Frame(self, padding=(16, 0, 16, 16))
        kaki.pack(fill="x")
        ttk.Button(kaki, text="Batal", command=self.destroy).pack(side="right")
        ttk.Button(kaki, text="Simpan", style="Utama.TButton",
                   command=self._simpan).pack(side="right", padx=(0, 8))
        if mutasi_id is None:
            ttk.Button(kaki, text="Simpan & Catat Lagi",
                       command=lambda: self._simpan(lagi=True)).pack(side="right", padx=(0, 8))

        if mutasi_id is not None:
            self._muat()
        self._info_stok()

        self.grab_set()
        self.wait_window()

    def _jenis_terpilih(self) -> dict | None:
        return self.peta_jenis.get(self.var_jenis.get())

    def _info_stok(self):
        j = self._jenis_terpilih()
        if not j:
            return
        unit, nilai = kasbuku.saldo_persediaan(j["id"])
        rata = kasbuku.harga_rata_rata(j["id"])
        self.lbl_satuan.configure(text=j["satuan"])
        self.lbl_stok.configure(
            text=f"Stok sekarang: {unit:,.0f} {j['satuan']}  ·  nilai {w.rp(nilai)}"
                 + (f"  ·  harga pokok rata-rata {w.rp(rata)}/{j['satuan']}" if unit else ""))
        self._hitung()

    def _hitung(self):
        j = self._jenis_terpilih()
        if not j:
            return
        jml = self.jml.nilai()
        if self.arah == "MASUK":
            nilai = jml * getattr(self, "harga", None).nilai() if hasattr(self, "harga") else 0
            self.lbl_hasil.configure(
                text=f"Nilai barang masuk: {w.rp(nilai)}" if nilai else "")
        else:
            rata = kasbuku.harga_rata_rata(j["id"])
            nilai = jml * rata
            if nilai:
                nama_hpp = ("Harga pokok penjualan" if self.arah == "KELUAR"
                            else "Nilai penyesuaian")
                self.lbl_hasil.configure(
                    text=f"{nama_hpp}: {w.rp(nilai)}   "
                         f"({jml:,.0f} × {w.rp(rata)} — dihitung otomatis)")
            else:
                self.lbl_hasil.configure(text="")

    def _muat(self):
        from .. import db
        m = db.koneksi().execute(
            "SELECT * FROM mutasi_persediaan WHERE id=?", (self.mutasi_id,)).fetchone()
        if not m:
            return
        self.tgl.set_iso(m["tanggal"])
        self.var_ket.set(m["keterangan"] or "")
        self.jml.set_nilai(m["jumlah"])
        for j in self.jenis:
            if j["id"] == m["jenis_id"]:
                self.var_jenis.set(j["nama"])
        if self.arah == "MASUK" and hasattr(self, "harga"):
            self.harga.set_nilai(m["harga"])
        self.cb_jenis.configure(state="disabled")

    def _simpan(self, lagi: bool = False):
        j = self._jenis_terpilih()
        if not j:
            w.galat("Belum dipilih", "Pilih dulu jenis barangnya.", self)
            return
        tanggal = self.tgl.iso()
        if not tanggal:
            w.galat("Tanggal belum benar", "Isi tanggal dengan format HH/BB/TTTT.", self)
            return
        jml = self.jml.nilai()
        if self.arah == "PENYESUAIAN":
            teks = self.jml.var.get().strip()
            if teks.startswith("-"):
                jml = -abs(jml)
        ket = self.var_ket.get().strip() or {
            "MASUK": "Barang masuk", "KELUAR": "Barang terjual",
            "PENYESUAIAN": "Penyesuaian stok"}[self.arah]

        harga = self.harga.nilai() if (self.arah == "MASUK" and hasattr(self, "harga")) else 0
        lawan = ""
        if self.arah == "MASUK" and getattr(self, "var_bayar", None):
            lawan = "211" if self.var_bayar.get() == "UTANG" else ""

        try:
            kasbuku.simpan_mutasi(self.aplikasi.periode_id, j["id"], tanggal, self.arah,
                                  jml, ket, harga=harga, kode_lawan=lawan,
                                  mutasi_id=self.mutasi_id)
        except Exception as e:
            w.galat("Belum bisa disimpan", str(e), self)
            return

        self.aplikasi.segarkan()
        if lagi and self.mutasi_id is None:
            self.jml.set_nilai(0)
            self.var_ket.set("")
            self._info_stok()
        else:
            self.destroy()


class DialogJualKredit(tk.Toplevel):
    """Penjualan yang uangnya dibayar menyusul (misalnya seragam siswa)."""

    def __init__(self, induk, aplikasi):
        super().__init__(induk)
        self.aplikasi = aplikasi
        self.title("Penjualan Dibayar Menyusul")
        self.resizable(False, False)
        self.transient(induk)
        self.configure(bg=w.ABU)

        kop = tk.Frame(self, bg=w.BIRU)
        kop.pack(fill="x")
        tk.Label(kop, text="PENJUALAN DIBAYAR MENYUSUL", bg=w.BIRU, fg="white",
                 font=(w.keluarga_font(), 13, "bold"), padx=16, pady=10).pack(side="left")

        isi = ttk.Frame(self, padding=16)
        isi.pack(fill="both", expand=True)
        isi.columnconfigure(1, weight=1)

        ttk.Label(isi, text="Tanggal").grid(row=0, column=0, sticky="w", pady=6)
        self.tgl = w.EntriTanggal(isi)
        self.tgl.grid(row=0, column=1, sticky="w", pady=6)

        ttk.Label(isi, text="Jenis barang").grid(row=1, column=0, sticky="w", pady=6)
        self.jenis = kasbuku.daftar_jenis()
        self.peta = {j["nama"]: j for j in self.jenis}
        self.var_jenis = tk.StringVar(value=self.jenis[0]["nama"] if self.jenis else "")
        cb = ttk.Combobox(isi, textvariable=self.var_jenis,
                          values=[j["nama"] for j in self.jenis],
                          state="readonly", width=34)
        cb.grid(row=1, column=1, sticky="w", pady=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self._stok())

        self.lbl_stok = ttk.Label(isi, text="", style="Sub.TLabel")
        self.lbl_stok.grid(row=2, column=1, sticky="w")

        ttk.Label(isi, text="Pembeli / keterangan").grid(row=3, column=0, sticky="w", pady=6)
        self.var_ket = tk.StringVar()
        ttk.Entry(isi, textvariable=self.var_ket, width=46).grid(
            row=3, column=1, sticky="ew", pady=6)

        ttk.Label(isi, text="Berapa unit terjual?").grid(row=4, column=0, sticky="w", pady=6)
        br = ttk.Frame(isi)
        br.grid(row=4, column=1, sticky="w", pady=6)
        self.jml = w.EntriAngka(br, lebar=12, font=(w.keluarga_font(), 12))
        self.jml.pack(side="left")
        self.lbl_satuan = ttk.Label(br, text="unit", style="Sub.TLabel")
        self.lbl_satuan.pack(side="left", padx=(8, 0))

        ttk.Label(isi, text="Harga jual seluruhnya").grid(row=5, column=0, sticky="w", pady=6)
        bh = ttk.Frame(isi)
        bh.grid(row=5, column=1, sticky="w", pady=6)
        ttk.Label(bh, text="Rp").pack(side="left", padx=(0, 6))
        self.nilai = w.EntriAngka(bh, lebar=16, font=(w.keluarga_font(), 12))
        self.nilai.pack(side="left")

        ttk.Label(isi, style="Sub.TLabel", wraplength=440,
                  text="Piutang bertambah sebesar harga jual, dan stok barang "
                       "otomatis berkurang. Saat dilunasi nanti, catat di Buku Kas "
                       "sebagai uang masuk dengan pilihan 'Piutang'.").grid(
                           row=6, column=0, columnspan=2, sticky="w", pady=(12, 0))

        kaki = ttk.Frame(self, padding=(16, 0, 16, 16))
        kaki.pack(fill="x")
        ttk.Button(kaki, text="Batal", command=self.destroy).pack(side="right")
        ttk.Button(kaki, text="Simpan", style="Utama.TButton",
                   command=self._simpan).pack(side="right", padx=(0, 8))

        self._stok()
        self.grab_set()
        self.wait_window()

    def _stok(self):
        j = self.peta.get(self.var_jenis.get())
        if not j:
            return
        unit, nilai = kasbuku.saldo_persediaan(j["id"])
        self.lbl_satuan.configure(text=j["satuan"])
        self.lbl_stok.configure(
            text=f"Stok sekarang: {unit:,.0f} {j['satuan']}  ·  nilai {w.rp(nilai)}")

    def _simpan(self):
        j = self.peta.get(self.var_jenis.get())
        tanggal = self.tgl.iso()
        if not j or not tanggal:
            w.galat("Belum lengkap", "Lengkapi tanggal dan jenis barangnya.", self)
            return
        try:
            kasbuku.simpan_penjualan_kredit(
                self.aplikasi.periode_id, j["id"], tanggal, self.jml.nilai(),
                self.nilai.nilai(), self.var_ket.get().strip() or "Penjualan kredit")
        except Exception as e:
            w.galat("Belum bisa disimpan", str(e), self)
            return
        self.aplikasi.segarkan()
        self.destroy()


class TabPersediaan(ttk.Frame):
    """Kartu persediaan per jenis barang beserta mutasinya."""

    def __init__(self, induk, aplikasi):
        super().__init__(induk, padding=12)
        self.aplikasi = aplikasi

        atas = ttk.Frame(self)
        atas.pack(fill="x", pady=(0, 10))
        ttk.Label(atas, text="Persediaan Barang", style="Judul.TLabel").pack(side="left")
        ttk.Label(atas, style="Sub.TLabel",
                  text="   Catat barang datang dan barang terjual.").pack(
                      side="left", padx=(4, 0))
        ttk.Button(atas, text="Cetak PDF", command=self._cetak).pack(side="right")
        ttk.Button(atas, text="Hapus", command=self._hapus).pack(side="right", padx=(0, 8))
        ttk.Button(atas, text="Ubah", command=self._ubah).pack(side="right", padx=(0, 8))

        tombol = ttk.Frame(self)
        tombol.pack(fill="x", pady=(0, 10))
        self.tombol = []
        for teks, arah, warna in (("  ⬇   BARANG MASUK  ", "MASUK", w.HIJAU),
                                  ("  ⬆   BARANG KELUAR  ", "KELUAR", w.ORANYE)):
            b = tk.Button(tombol, text=teks, bg=warna, fg="white",
                          activeforeground="white",
                          font=(w.keluarga_font(), 12, "bold"), relief="flat",
                          cursor="hand2", padx=18, pady=12,
                          command=lambda a=arah: self._baru(a))
            b.pack(side="left", padx=(0, 10))
            self.tombol.append(b)
        b = ttk.Button(tombol, text="Penjualan dibayar menyusul",
                       command=self._kredit)
        b.pack(side="left", padx=(0, 8))
        self.tombol.append(b)
        b = ttk.Button(tombol, text="Penyesuaian stok",
                       command=lambda: self._baru("PENYESUAIAN"))
        b.pack(side="left")
        self.tombol.append(b)

        self.kartu = ttk.Frame(self)
        self.kartu.pack(fill="x", pady=(0, 10))

        pilih = ttk.Frame(self)
        pilih.pack(fill="x", pady=(0, 6))
        ttk.Label(pilih, text="Lihat mutasi:").pack(side="left", padx=(0, 8))
        self.var_lihat = tk.StringVar(value="Semua jenis")
        self.cb_lihat = ttk.Combobox(pilih, textvariable=self.var_lihat,
                                     state="readonly", width=30)
        self.cb_lihat.pack(side="left")
        self.cb_lihat.bind("<<ComboboxSelected>>", lambda e: self.muat())

        self.kaki = ttk.Label(self, text="", style="Sub.TLabel", wraplength=1180)
        self.kaki.pack(side="bottom", anchor="w", pady=(8, 0))

        self.tabel = w.buat_tabel(self, [
            ("tgl", "Tanggal", 95, "center"),
            ("jenis", "Jenis Barang", 175, "w"),
            ("ket", "Keterangan", 265, "w"),
            ("arah", "Mutasi", 110, "center"),
            ("jml", "Unit", 80, "e"),
            ("harga", "Harga/Unit", 110, "e"),
            ("nilai", "Nilai", 125, "e"),
            ("sisa", "Sisa Unit", 85, "e"),
            ("sisan", "Sisa Nilai", 125, "e"),
        ], tinggi=10)
        self.tabel.bind("<Double-1>", lambda e: self._ubah())

    def muat(self):
        for anak in self.kartu.winfo_children():
            anak.destroy()

        self.rekap = kasbuku.rekap_persediaan(self.aplikasi.periode_id)
        for k in self.rekap["kartu"]:
            j = k["jenis"]
            kotak = ttk.Frame(self.kartu, style="Kartu.TFrame", padding=12)
            kotak.pack(side="left", padx=(0, 10))
            ttk.Label(kotak, text=j["nama"].upper(),
                      style="KartuJudul.TLabel").pack(anchor="w")
            ttk.Label(kotak, text=w.rp(k["akhir_nilai"]),
                      style="KartuNilai.TLabel").pack(anchor="w")
            ttk.Label(kotak, style="Sub.TLabel", background=w.PUTIH,
                      text=f"{k['akhir_jumlah']:,.0f} {j['satuan']} tersisa").pack(anchor="w")
        kotak = ttk.Frame(self.kartu, style="Kartu.TFrame", padding=12)
        kotak.pack(side="left")
        ttk.Label(kotak, text="TOTAL PERSEDIAAN", style="KartuJudul.TLabel").pack(anchor="w")
        ttk.Label(kotak, text=w.rp(self.rekap["total_akhir"]),
                  style="KartuNilai.TLabel").pack(anchor="w")
        ttk.Label(kotak, style="Sub.TLabel", background=w.PUTIH,
                  text="masuk laporan posisi keuangan").pack(anchor="w")

        jenis = kasbuku.daftar_jenis()
        self.cb_lihat.configure(values=["Semua jenis"] + [j["nama"] for j in jenis])
        peta = {j["nama"]: j["id"] for j in jenis}
        jid = peta.get(self.var_lihat.get())

        self.data = kasbuku.daftar_mutasi(self.aplikasi.periode_id, jid)
        baris, tag = [], {}
        for m in self.data:
            arah = {"MASUK": "Masuk", "KELUAR": "Keluar",
                    "PENYESUAIAN": "Penyesuaian"}[m["arah"]]
            baris.append([
                w.tgl_id(m["tanggal"]), m["nama_jenis"], m["keterangan"], arah,
                f"{m['jumlah']:,.0f}", w.rp(m["harga"]), w.rp(m["nilai"]),
                f"{m['sisa_jumlah']:,.0f}", w.rp(m["sisa_nilai"]),
            ])
            if m["arah"] == "KELUAR":
                tag[len(baris) - 1] = "merah"
        w.isi_tabel(self.tabel, baris, tag)

        terkunci = engine.periode_terkunci(self.aplikasi.periode_id)
        for b in self.tombol:
            try:
                b.configure(state="disabled" if terkunci else "normal")
            except tk.TclError:
                pass
        self.kaki.configure(text=(
            "Periode ini sudah ditutup, mutasi tidak bisa diubah lagi."
            if terkunci else
            f"{len(self.data)} mutasi. Harga pokok barang keluar dihitung sendiri "
            "dengan rata-rata bergerak, lalu masuk ke Laporan Laba Rugi."))

    def _baru(self, arah: str):
        if engine.periode_terkunci(self.aplikasi.periode_id):
            w.peringatan("Periode terkunci", "Periode ini sudah ditutup buku.", self)
            return
        DialogMutasi(self, self.aplikasi, arah)

    def _kredit(self):
        if engine.periode_terkunci(self.aplikasi.periode_id):
            w.peringatan("Periode terkunci", "Periode ini sudah ditutup buku.", self)
            return
        DialogJualKredit(self, self.aplikasi)

    def _terpilih(self) -> dict | None:
        pilih = self.tabel.selection()
        if not pilih:
            return None
        idx = self.tabel.index(pilih[0])
        return self.data[idx] if 0 <= idx < len(self.data) else None

    def _ubah(self):
        m = self._terpilih()
        if not m:
            w.peringatan("Belum dipilih", "Pilih dulu baris yang mau diubah.", self)
            return
        if engine.periode_terkunci(self.aplikasi.periode_id):
            w.peringatan("Periode terkunci", "Periode ini sudah ditutup buku.", self)
            return
        DialogMutasi(self, self.aplikasi, m["arah"], jenis_id=m["jenis_id"],
                     mutasi_id=m["id"])

    def _hapus(self):
        m = self._terpilih()
        if not m:
            w.peringatan("Belum dipilih", "Pilih dulu baris yang mau dihapus.", self)
            return
        if not w.tanya("Hapus mutasi ini?",
                       f"{w.tgl_id(m['tanggal'])}  {m['nama_jenis']}\n"
                       f"{m['arah']} {m['jumlah']:,.0f} {m['satuan']} = {w.rp(m['nilai'])}\n\n"
                       "Sisa stok sesudahnya akan dihitung ulang.", self):
            return
        try:
            kasbuku.hapus_mutasi(m["id"])
        except Exception as e:
            w.galat("Gagal menghapus", str(e), self)
            return
        self.aplikasi.segarkan()

    def _cetak(self):
        from .. import pdfout
        self.aplikasi._cetak(pdfout.cetak_persediaan)
