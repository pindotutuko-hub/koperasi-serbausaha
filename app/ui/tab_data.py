"""Tab Daftar Akun (COA) dan Saldo Awal."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import engine, pdfout
from . import widgets as w


class DialogAkun(tk.Toplevel):
    def __init__(self, induk, kode: str | None = None):
        super().__init__(induk)
        self.kode_lama = kode
        self.tersimpan = False
        self.title("Ubah Akun" if kode else "Tambah Akun Baru")
        self.configure(bg=w.ABU)
        self.transient(induk)
        data = next((a for a in engine.daftar_akun(hanya_aktif=False) if a["kode"] == kode), None)

        isi = ttk.Frame(self, padding=16)
        isi.pack(fill="both", expand=True)
        self.var = {
            "kode": tk.StringVar(value=data["kode"] if data else ""),
            "nama": tk.StringVar(value=data["nama"] if data else ""),
            "kategori": tk.StringVar(value=data["kategori"] if data else "Beban"),
            "subkategori": tk.StringVar(value=data["subkategori"] if data else "Beban"),
            "saldo_normal": tk.StringVar(value=data["saldo_normal"] if data else "Debet"),
            "peran": tk.StringVar(value=(data["peran"] if data else "") or ""),
            "aktif": tk.IntVar(value=data["aktif"] if data else 1),
        }
        baris = [
            ("Kode Akun", ttk.Entry(isi, textvariable=self.var["kode"], width=14)),
            ("Nama Akun", ttk.Entry(isi, textvariable=self.var["nama"], width=40)),
            ("Kategori", ttk.Combobox(isi, textvariable=self.var["kategori"], width=20,
                                      state="readonly", values=engine.KATEGORI)),
            ("Kelompok Laporan", ttk.Combobox(isi, textvariable=self.var["subkategori"], width=20,
                                              state="readonly", values=engine.SUBKATEGORI)),
            ("Saldo Normal", ttk.Combobox(isi, textvariable=self.var["saldo_normal"], width=14,
                                          state="readonly", values=["Debet", "Kredit"])),
            ("Peran Khusus", ttk.Combobox(isi, textvariable=self.var["peran"], width=20,
                                          state="readonly", values=engine.PERAN)),
        ]
        for i, (label, widget) in enumerate(baris):
            ttk.Label(isi, text=label).grid(row=i, column=0, sticky="w", pady=4, padx=(0, 10))
            widget.grid(row=i, column=1, sticky="w", pady=4)
        ttk.Checkbutton(isi, text="Akun aktif (muncul di pilihan jurnal)",
                        variable=self.var["aktif"]).grid(row=len(baris), column=1, sticky="w",
                                                         pady=(6, 0))
        ttk.Label(isi, text="Peran khusus dipakai program untuk menghitung HPP, arus kas, dan\n"
                            "penempatan SHU. Contoh: KAS, BANK, PERSEDIAAN, LABA_DITAHAN,\n"
                            "PEMBELIAN. Kosongkan untuk akun biasa.", style="Sub.TLabel",
                  justify="left").grid(row=len(baris) + 1, column=0, columnspan=2,
                                       sticky="w", pady=(10, 0))

        bawah = ttk.Frame(self, padding=(16, 0, 16, 14))
        bawah.pack(fill="x")
        ttk.Button(bawah, text="Batal", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(bawah, text="Simpan", style="Utama.TButton",
                   command=self._simpan).pack(side="right")
        self.grab_set()

    def _simpan(self):
        try:
            engine.simpan_akun(self.var["kode"].get(), self.var["nama"].get(),
                               self.var["kategori"].get(), self.var["subkategori"].get(),
                               self.var["saldo_normal"].get(), self.var["peran"].get(),
                               self.var["aktif"].get(), self.kode_lama)
        except ValueError as e:
            w.galat("Akun belum bisa disimpan", str(e), self)
            return
        self.tersimpan = True
        self.destroy()


class TabAkun(ttk.Frame):
    def __init__(self, induk, aplikasi):
        super().__init__(induk, padding=12)
        self.app = aplikasi
        atas = ttk.Frame(self)
        atas.pack(fill="x")
        ttk.Label(atas, text="Daftar Akun (Chart of Account)", style="Judul.TLabel").pack(side="left")
        ttk.Label(atas, text="  Daftar akun berlaku untuk semua periode.",
                  style="Sub.TLabel").pack(side="left")

        alat = ttk.Frame(self)
        alat.pack(fill="x", pady=(10, 8))
        ttk.Button(alat, text="+  Tambah Akun", style="Utama.TButton",
                   command=self.tambah).pack(side="left")
        ttk.Button(alat, text="Ubah", command=self.ubah).pack(side="left", padx=(6, 0))
        ttk.Button(alat, text="Hapus", command=self.hapus).pack(side="left", padx=(6, 0))
        ttk.Button(alat, text="🖨  Cetak PDF", command=self.cetak).pack(side="left", padx=(12, 0))

        self.tabel = w.buat_tabel(self, [
            ("kode", "Kode", 80, "center"), ("nama", "Nama Akun", 320, "w"),
            ("kat", "Kategori", 130, "center"), ("sub", "Kelompok Laporan", 160, "center"),
            ("normal", "Saldo Normal", 120, "center"), ("peran", "Peran Khusus", 150, "center"),
            ("status", "Status", 100, "center")], tinggi=18)
        self.tabel.bind("<Double-1>", lambda e: self.ubah())

    def muat(self):
        self.data = engine.daftar_akun(hanya_aktif=False)
        baris = [[a["kode"], a["nama"], a["kategori"], a["subkategori"], a["saldo_normal"],
                  a["peran"] or "-", "Aktif" if a["aktif"] else "Nonaktif"] for a in self.data]
        w.isi_tabel(self.tabel, baris)

    def _kode_terpilih(self) -> str | None:
        pilih = self.tabel.selection()
        return self.data[self.tabel.index(pilih[0])]["kode"] if pilih else None

    def tambah(self):
        d = DialogAkun(self.winfo_toplevel())
        self.wait_window(d)
        if d.tersimpan:
            self.app.segarkan()

    def ubah(self):
        kode = self._kode_terpilih()
        if not kode:
            w.peringatan("Belum ada yang dipilih", "Pilih dulu akun yang akan diubah.", self)
            return
        d = DialogAkun(self.winfo_toplevel(), kode)
        self.wait_window(d)
        if d.tersimpan:
            self.app.segarkan()

    def hapus(self):
        kode = self._kode_terpilih()
        if not kode:
            w.peringatan("Belum ada yang dipilih", "Pilih dulu akun yang akan dihapus.", self)
            return
        if not w.tanya("Hapus akun", f"Akun {kode} akan dihapus. Lanjutkan?", self):
            return
        try:
            engine.hapus_akun(kode)
        except ValueError as e:
            w.galat("Tidak bisa dihapus", str(e), self)
            return
        self.app.segarkan()

    def cetak(self):
        w.selesai_cetak(pdfout.cetak_daftar_akun(), self)


class TabSaldoAwal(ttk.Frame):
    def __init__(self, induk, aplikasi):
        super().__init__(induk, padding=12)
        self.app = aplikasi
        self.entri: dict[str, tuple] = {}

        atas = ttk.Frame(self)
        atas.pack(fill="x")
        ttk.Label(atas, text="Saldo Awal Periode", style="Judul.TLabel").pack(side="left")
        ttk.Button(atas, text="🖨  Cetak PDF", command=self.cetak).pack(side="right")
        self.btn_simpan = ttk.Button(atas, text="💾  Simpan Saldo Awal", style="Utama.TButton",
                                     command=self.simpan)
        self.btn_simpan.pack(side="right", padx=(0, 6))

        self.lbl_info = ttk.Label(self, text="", style="Sub.TLabel", wraplength=1000,
                                  justify="left")
        self.lbl_info.pack(anchor="w", pady=(6, 8))

        kepala = ttk.Frame(self)
        kepala.pack(fill="x")
        for teks, lebar, rata in (("Kode", 8, "center"), ("Nama Akun", 40, "w"),
                                  ("Saldo Normal", 14, "center"), ("Debet", 18, "center"),
                                  ("Kredit", 18, "center")):
            ttk.Label(kepala, text=teks, width=lebar, style="Tebal.TLabel",
                      anchor=rata).pack(side="left", padx=2)

        wadah = ttk.Frame(self)
        wadah.pack(fill="both", expand=True)
        self.kanvas = tk.Canvas(wadah, bg=w.ABU, highlightthickness=0)
        gulir = ttk.Scrollbar(wadah, orient="vertical", command=self.kanvas.yview)
        self.isi = ttk.Frame(self.kanvas)
        self.isi.bind("<Configure>",
                      lambda e: self.kanvas.configure(scrollregion=self.kanvas.bbox("all")))
        self.kanvas.create_window((0, 0), window=self.isi, anchor="nw")
        self.kanvas.configure(yscrollcommand=gulir.set)
        self.kanvas.pack(side="left", fill="both", expand=True)
        gulir.pack(side="right", fill="y")
        self.kanvas.bind_all("<MouseWheel>",
                             lambda e: self.kanvas.yview_scroll(int(-e.delta / 120), "units"))

        self.lbl_total = ttk.Label(self, text="", style="Tebal.TLabel")
        self.lbl_total.pack(anchor="w", pady=(8, 0))

    @property
    def periode_id(self) -> int:
        return self.app.periode_id

    def muat(self):
        for anak in self.isi.winfo_children():
            anak.destroy()
        self.entri.clear()
        p = engine.periode(self.periode_id)
        sebelum = engine.periode_sebelum(p)
        otomatis = bool(sebelum and sebelum["status"] == "TUTUP")
        terkunci = p["status"] == "TUTUP" or otomatis
        saldo = engine.saldo_awal(self.periode_id)

        if terkunci and otomatis:
            pesan = (f"Saldo awal {engine.nama_periode(p['tahun'], p['bulan'])} dihasilkan "
                     f"otomatis dari tutup buku "
                     f"{engine.nama_periode(sebelum['tahun'], sebelum['bulan'])}, "
                     "sehingga tidak diubah manual. Bila ada koreksi, buka kembali "
                     "periode sebelumnya lewat menu Tutup Buku.")
        elif p["status"] == "TUTUP":
            pesan = "Periode ini sudah ditutup — saldo awal tidak dapat diubah."
        else:
            pesan = ("Isi saldo awal hanya untuk periode pertama pemakaian program. "
                     "Total Debet harus sama dengan total Kredit.")
        self.lbl_info.configure(text=pesan, foreground=w.ORANYE if terkunci else w.TEKS_REDUP)
        self.btn_simpan.state(["disabled"] if terkunci else ["!disabled"])

        for a in engine.daftar_akun(hanya_aktif=False):
            d, k = saldo.get(a["kode"], (0, 0))
            if not a["aktif"] and not (d or k):
                continue
            baris = ttk.Frame(self.isi)
            baris.pack(fill="x", pady=1)
            ttk.Label(baris, text=a["kode"], width=8, anchor="center").pack(side="left", padx=2)
            ttk.Label(baris, text=a["nama"], width=40, anchor="w").pack(side="left", padx=2)
            ttk.Label(baris, text=a["saldo_normal"], width=14,
                      anchor="center").pack(side="left", padx=2)
            e_d = w.EntriAngka(baris, 18, saat_ubah=self._hitung)
            e_d.pack(side="left", padx=2)
            e_k = w.EntriAngka(baris, 18, saat_ubah=self._hitung)
            e_k.pack(side="left", padx=2)
            e_d.set_nilai(d)
            e_k.set_nilai(k)
            if terkunci:
                e_d.configure(state="readonly")
                e_k.configure(state="readonly")
            self.entri[a["kode"]] = (e_d, e_k)
        self._hitung()

    def _hitung(self):
        td = sum(e[0].nilai() for e in self.entri.values())
        tk_ = sum(e[1].nilai() for e in self.entri.values())
        selisih = round(td - tk_, 2)
        teks = f"Total Debet: {w.rp(td, '0')}     Total Kredit: {w.rp(tk_, '0')}     "
        if abs(selisih) < 0.01:
            self.lbl_total.configure(text=teks + "SEIMBANG ✓", foreground=w.HIJAU)
        else:
            self.lbl_total.configure(text=teks + f"Selisih: {w.rp(selisih, '0')}",
                                     foreground=w.MERAH)

    def simpan(self):
        data = {kode: (e[0].nilai(), e[1].nilai()) for kode, e in self.entri.items()}
        td = sum(v[0] for v in data.values())
        tk_ = sum(v[1] for v in data.values())
        if abs(td - tk_) >= 0.01:
            if not w.tanya("Belum seimbang",
                           f"Total Debet ({w.rp(td)}) tidak sama dengan total Kredit "
                           f"({w.rp(tk_)}).\n\nTetap simpan? Laporan akan menunjukkan "
                           "status TIDAK BALANCE sampai diperbaiki.", self):
                return
        engine.simpan_saldo_awal(self.periode_id, data)
        w.info("Tersimpan", "Saldo awal berhasil disimpan.", self)
        self.app.segarkan()

    def cetak(self):
        w.selesai_cetak(pdfout.cetak_saldo_awal(self.periode_id), self)
