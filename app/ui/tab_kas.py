"""Tab Buku Kas — pintu masuk utama bagi petugas tanpa dasar akuntansi.

Petugas cukup menjawab tiga hal: uangnya masuk atau keluar, untuk apa, dan
berapa. Program yang menyusun jurnalnya, tanpa pernah menampilkan istilah
debit atau kredit.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import db, engine, kasbuku
from . import widgets as w


class DialogKas(tk.Toplevel):
    """Form pencatatan uang masuk atau uang keluar."""

    def __init__(self, induk, aplikasi, arah: str, jurnal_id: int | None = None):
        super().__init__(induk)
        self.aplikasi = aplikasi
        self.arah = arah
        self.jurnal_id = jurnal_id
        self.tersimpan = False

        masuk = arah == "MASUK"
        self.title(("Catat Uang Masuk" if masuk else "Catat Uang Keluar")
                   if jurnal_id is None else "Ubah Catatan Kas")
        self.resizable(False, False)
        self.transient(induk)
        self.configure(bg=w.ABU)

        warna = w.HIJAU if masuk else w.MERAH
        kop = tk.Frame(self, bg=warna)
        kop.pack(fill="x")
        tk.Label(kop, text=("UANG MASUK" if masuk else "UANG KELUAR"),
                 bg=warna, fg="white", font=(w.keluarga_font(), 13, "bold"),
                 padx=16, pady=10).pack(side="left")
        tk.Label(kop,
                 text=("Uang yang diterima kantin" if masuk
                       else "Uang yang dikeluarkan kantin"),
                 bg=warna, fg="#EAF3EA" if masuk else "#F7E6E8",
                 padx=4, pady=12).pack(side="left")

        isi = ttk.Frame(self, padding=16)
        isi.pack(fill="both", expand=True)
        isi.columnconfigure(1, weight=1)

        b = 0
        ttk.Label(isi, text="Tanggal").grid(row=b, column=0, sticky="w", pady=6)
        self.tgl = w.EntriTanggal(isi)
        self.tgl.grid(row=b, column=1, sticky="w", pady=6)

        b += 1
        ttk.Label(isi, text="Untuk apa?").grid(row=b, column=0, sticky="nw", pady=6)
        rangka = ttk.Frame(isi)
        rangka.grid(row=b, column=1, sticky="ew", pady=6)
        self.var_akun = tk.StringVar()
        self.daftar = kasbuku.akun_lawan(arah)
        self.label_akun = {}
        pilihan = []
        for a in self.daftar:
            teks = f"{a['nama']}"
            if a["keterangan"]:
                teks += f"  —  {a['keterangan']}"
            pilihan.append(teks)
            self.label_akun[teks] = a["kode"]
        self.cb = ttk.Combobox(rangka, textvariable=self.var_akun, values=pilihan,
                               state="readonly", width=52)
        self.cb.pack(fill="x")
        ttk.Label(rangka, style="Sub.TLabel",
                  text=("Pilih dari daftar. Contoh: hasil penjualan, "
                        "tarik tunai dari bank." if masuk else
                        "Pilih dari daftar. Contoh: bayar gaji, bayar listrik, "
                        "setor ke bank.")).pack(anchor="w", pady=(4, 0))

        b += 1
        ttk.Label(isi, text="Keterangan").grid(row=b, column=0, sticky="w", pady=6)
        self.var_ket = tk.StringVar()
        ttk.Entry(isi, textvariable=self.var_ket, width=54).grid(
            row=b, column=1, sticky="ew", pady=6)

        b += 1
        ttk.Label(isi, text="Jumlah uang").grid(row=b, column=0, sticky="w", pady=6)
        baris_jml = ttk.Frame(isi)
        baris_jml.grid(row=b, column=1, sticky="w", pady=6)
        ttk.Label(baris_jml, text="Rp", style="Tebal.TLabel").pack(side="left", padx=(0, 6))
        self.jml = w.EntriAngka(baris_jml, lebar=20, font=(w.keluarga_font(), 13))
        self.jml.pack(side="left")

        b += 1
        self.pesan = ttk.Label(isi, text="", style="Sub.TLabel", wraplength=460)
        self.pesan.grid(row=b, column=0, columnspan=2, sticky="w", pady=(10, 0))

        kaki = ttk.Frame(self, padding=(16, 0, 16, 16))
        kaki.pack(fill="x")
        ttk.Button(kaki, text="Batal", command=self.destroy).pack(side="right")
        self.tombol = ttk.Button(kaki, text="Simpan", style="Utama.TButton",
                                 command=self._simpan)
        self.tombol.pack(side="right", padx=(0, 8))
        if jurnal_id is None:
            ttk.Button(kaki, text="Simpan & Catat Lagi",
                       command=lambda: self._simpan(lagi=True)).pack(side="right", padx=(0, 8))

        if jurnal_id is not None:
            self._muat()

        self.grab_set()
        self.cb.focus_set()
        self.wait_window()

    def _muat(self):
        """Mengisi form dari catatan yang sudah ada."""
        kas = engine.akun_berperan("KAS")
        det = engine.detail_jurnal(self.jurnal_id)
        induk = db.koneksi().execute(
            "SELECT tanggal, keterangan FROM jurnal WHERE id=?",
            (self.jurnal_id,)).fetchone()
        if induk:
            self.tgl.set_iso(induk["tanggal"])
            self.var_ket.set(induk["keterangan"] or "")
        for d in det:
            if d["kode_akun"] == kas["kode"]:
                self.jml.set_nilai(d["debit"] or d["kredit"])
            else:
                for teks, kode in self.label_akun.items():
                    if kode == d["kode_akun"]:
                        self.var_akun.set(teks)
                        break

    def _simpan(self, lagi: bool = False):
        tanggal = self.tgl.iso()
        if not tanggal:
            w.galat("Tanggal belum benar", "Isi tanggal dengan format HH/BB/TTTT.", self)
            return
        teks = self.var_akun.get()
        if teks not in self.label_akun:
            w.galat("Belum dipilih", "Pilih dulu 'Untuk apa?' dari daftar.", self)
            return
        jumlah = self.jml.nilai()
        if jumlah <= 0:
            w.galat("Jumlah belum diisi", "Isi jumlah uangnya lebih dulu.", self)
            return
        ket = self.var_ket.get().strip()
        if not ket:
            ket = teks.split("  —  ")[0]

        try:
            kasbuku.simpan_kas(self.aplikasi.periode_id, tanggal, self.arah,
                               self.label_akun[teks], jumlah, ket,
                               jurnal_id=self.jurnal_id)
        except Exception as e:
            w.galat("Belum bisa disimpan", str(e), self)
            return

        self.tersimpan = True
        self.aplikasi.segarkan()
        if lagi and self.jurnal_id is None:
            self.jml.set_nilai(0)
            self.var_ket.set("")
            self.pesan.configure(text=f"Tersimpan: {w.rp(jumlah)}  —  {ket}",
                                 foreground=w.HIJAU)
            self.cb.focus_set()
        else:
            self.destroy()


class TabKas(ttk.Frame):
    """Buku kas: daftar uang masuk dan keluar beserta saldo berjalan."""

    def __init__(self, induk, aplikasi):
        super().__init__(induk, padding=12)
        self.aplikasi = aplikasi

        atas = ttk.Frame(self)
        atas.pack(fill="x", pady=(0, 10))
        ttk.Label(atas, text="Buku Kas", style="Judul.TLabel").pack(side="left")
        ttk.Label(atas, style="Sub.TLabel",
                  text="   Catat semua uang yang masuk dan keluar di sini.").pack(
                      side="left", padx=(4, 0))

        ttk.Button(atas, text="Cetak PDF", command=self._cetak).pack(side="right")
        ttk.Button(atas, text="Hapus", command=self._hapus).pack(side="right", padx=(0, 8))
        ttk.Button(atas, text="Ubah", command=self._ubah).pack(side="right", padx=(0, 8))

        tombol = ttk.Frame(self)
        tombol.pack(fill="x", pady=(0, 10))
        self.b_masuk = tk.Button(
            tombol, text="  ⬇   UANG MASUK  ", bg=w.HIJAU, fg="white",
            activebackground="#17632A", activeforeground="white",
            font=(w.keluarga_font(), 12, "bold"), relief="flat", cursor="hand2",
            padx=18, pady=12, command=lambda: self._baru("MASUK"))
        self.b_masuk.pack(side="left")
        self.b_keluar = tk.Button(
            tombol, text="  ⬆   UANG KELUAR  ", bg=w.MERAH, fg="white",
            activebackground="#8E0019", activeforeground="white",
            font=(w.keluarga_font(), 12, "bold"), relief="flat", cursor="hand2",
            padx=18, pady=12, command=lambda: self._baru("KELUAR"))
        self.b_keluar.pack(side="left", padx=(10, 0))

        self.ringkas = ttk.Frame(tombol)
        self.ringkas.pack(side="right")
        self.lbl_saldo = ttk.Label(self.ringkas, text="", style="KartuNilai.TLabel",
                                   background=w.ABU)
        self.lbl_saldo.pack(anchor="e")
        ttk.Label(self.ringkas, text="Sisa uang kas", style="Sub.TLabel").pack(anchor="e")

        self.kaki = ttk.Label(self, text="", style="Sub.TLabel", wraplength=1180)
        self.kaki.pack(side="bottom", anchor="w", pady=(8, 0))

        self.tabel = w.buat_tabel(self, [
            ("tgl", "Tanggal", 95, "center"),
            ("bukti", "No Bukti", 125, "center"),
            ("ket", "Keterangan", 330, "w"),
            ("untuk", "Untuk apa", 200, "w"),
            ("masuk", "Uang Masuk", 125, "e"),
            ("keluar", "Uang Keluar", 125, "e"),
            ("saldo", "Sisa Kas", 135, "e"),
        ], tinggi=11)
        self.tabel.bind("<Double-1>", lambda e: self._ubah())

    # --- data ---------------------------------------------------------- #
    def muat(self):
        self.data = kasbuku.daftar_kas(self.aplikasi.periode_id)
        baris, tag = [], {}
        baris.append(["", "", "Saldo awal periode ini", "", "", "",
                      w.rp(self.data["saldo_awal"])])
        tag[0] = "judul"
        for b in self.data["baris"]:
            baris.append([
                w.tgl_id(b["tanggal"]), b["no_bukti"], b["keterangan"], b["lawan"],
                w.rp(b["jumlah"]) if b["arah"] == "MASUK" else "",
                w.rp(b["jumlah"]) if b["arah"] == "KELUAR" else "",
                w.rp(b["saldo"]),
            ])
        baris.append(["", "", "JUMLAH", "", w.rp(self.data["total_masuk"]),
                      w.rp(self.data["total_keluar"]), w.rp(self.data["saldo_akhir"])])
        tag[len(baris) - 1] = "total"
        w.isi_tabel(self.tabel, baris, tag)

        self.lbl_saldo.configure(text=w.rp(self.data["saldo_akhir"]))
        terkunci = engine.periode_terkunci(self.aplikasi.periode_id)
        for b in (self.b_masuk, self.b_keluar):
            b.configure(state="disabled" if terkunci else "normal")
        self.kaki.configure(text=(
            "Periode ini sudah ditutup, catatan tidak bisa diubah lagi."
            if terkunci else
            f"{len(self.data['baris'])} catatan. Klik dua kali sebuah baris untuk mengubahnya. "
            "Pembelian barang dagangan tidak dicatat di sini — pakai tab Persediaan, "
            "buku kas akan terisi sendiri."))

    # --- aksi ---------------------------------------------------------- #
    def _baru(self, arah: str):
        if engine.periode_terkunci(self.aplikasi.periode_id):
            w.peringatan("Periode terkunci",
                         "Periode ini sudah ditutup buku. Buka kembali dulu "
                         "lewat tab Tutup Buku bila ingin mengubah.", self)
            return
        DialogKas(self, self.aplikasi, arah)

    def _baris_terpilih(self) -> dict | None:
        pilih = self.tabel.selection()
        if not pilih:
            return None
        idx = self.tabel.index(pilih[0]) - 1          # baris pertama = saldo awal
        if 0 <= idx < len(self.data["baris"]):
            return self.data["baris"][idx]
        return None

    def _ubah(self):
        b = self._baris_terpilih()
        if not b:
            w.peringatan("Belum dipilih", "Pilih dulu baris yang mau diubah.", self)
            return
        if engine.periode_terkunci(self.aplikasi.periode_id):
            w.peringatan("Periode terkunci", "Periode ini sudah ditutup buku.", self)
            return
        if b["sumber"] == "PERSEDIAAN":
            w.peringatan(
                "Diubah lewat tab Persediaan",
                "Baris ini berasal dari pencatatan barang masuk. Ubahlah lewat "
                "tab Persediaan supaya stok dan nilainya ikut menyesuaikan.", self)
            return
        DialogKas(self, self.aplikasi, b["arah"], jurnal_id=b["jurnal_id"])

    def _hapus(self):
        b = self._baris_terpilih()
        if not b:
            w.peringatan("Belum dipilih", "Pilih dulu baris yang mau dihapus.", self)
            return
        if engine.periode_terkunci(self.aplikasi.periode_id):
            w.peringatan("Periode terkunci", "Periode ini sudah ditutup buku.", self)
            return
        if b["sumber"] == "PERSEDIAAN":
            w.peringatan(
                "Dihapus lewat tab Persediaan",
                "Baris ini berasal dari pencatatan barang masuk. Hapuslah lewat "
                "tab Persediaan supaya stoknya ikut menyesuaikan.", self)
            return
        if not w.tanya("Hapus catatan ini?",
                       f"{w.tgl_id(b['tanggal'])}  {b['keterangan']}\n"
                       f"{w.rp(b['jumlah'])}\n\nCatatan yang dihapus tidak bisa "
                       "dikembalikan.", self):
            return
        try:
            engine.hapus_jurnal(b["jurnal_id"])
        except Exception as e:
            w.galat("Gagal menghapus", str(e), self)
            return
        self.aplikasi.segarkan()

    def _cetak(self):
        from .. import pdfout
        self.aplikasi._cetak(pdfout.cetak_buku_kas)
