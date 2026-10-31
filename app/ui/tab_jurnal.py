"""Tab Jurnal: input manual, transaksi cepat, impor Excel, cetak PDF."""
from __future__ import annotations

import os
import tkinter as tk
from datetime import date
from tkinter import filedialog, ttk

from .. import db, engine, pdfout, xlsio
from . import widgets as w

TRANSAKSI_CEPAT = [
    ("Penjualan tunai", "Rekap penjualan kantin", "KAS", "411", "D"),
    ("Pembelian barang (tunai)", "Pembelian barang dagang", "PEMBELIAN", "KAS", "D"),
    ("Bayar beban (tunai)", "Pembayaran beban", "611", "KAS", "D"),
    ("Setor kas ke bank", "Setoran kas ke bank", "BANK", "KAS", "D"),
    ("Tarik tunai dari bank", "Penarikan tunai dari bank", "KAS", "BANK", "D"),
]


def _daftar_pilihan_akun() -> tuple[list[str], dict[str, str], dict[str, str]]:
    akun = engine.daftar_akun()
    pilihan = [f"{a['kode']} — {a['nama']}" for a in akun]
    ke_kode = {p: p.split(" — ")[0] for p in pilihan}
    dari_kode = {a["kode"]: f"{a['kode']} — {a['nama']}" for a in akun}
    return pilihan, ke_kode, dari_kode


class DialogJurnal(tk.Toplevel):
    """Formulir input / ubah satu transaksi jurnal."""

    def __init__(self, induk, periode_id: int, jurnal_id: int | None = None):
        super().__init__(induk)
        self.periode_id = periode_id
        self.jurnal_id = jurnal_id
        self.tersimpan = False
        p = engine.periode(periode_id)
        self.title(("Ubah" if jurnal_id else "Input") + " Transaksi Jurnal — "
                   + engine.nama_periode(p["tahun"], p["bulan"]))
        self.configure(bg=w.ABU)
        self.transient(induk)
        self.baris_widget: list[dict] = []
        self.pilihan, self.ke_kode, self.dari_kode = _daftar_pilihan_akun()

        self._bangun(p)
        if jurnal_id:
            self._muat(jurnal_id)
        else:
            for _ in range(2):
                self._tambah_baris()
        self.update_idletasks()
        self.geometry(f"+{induk.winfo_rootx() + 60}+{max(induk.winfo_rooty() + 30, 20)}")
        self.grab_set()
        self.entry_ket.focus_set()

    # ---------------------------------------------------------------- bangun #
    def _bangun(self, p: dict):
        atas = ttk.Frame(self, padding=(14, 12, 14, 6))
        atas.pack(fill="x")
        ttk.Label(atas, text="Tanggal").grid(row=0, column=0, sticky="w", padx=(0, 8))
        tgl_awal = date(p["tahun"], p["bulan"], min(date.today().day, 28)).isoformat()
        self.tanggal = w.EntriTanggal(atas, tgl_awal)
        self.tanggal.grid(row=1, column=0, sticky="w", padx=(0, 14))

        ttk.Label(atas, text="No. Bukti").grid(row=0, column=1, sticky="w", padx=(0, 8))
        self.var_bukti = tk.StringVar(value=engine.nomor_bukti_berikutnya(self.periode_id))
        ttk.Entry(atas, textvariable=self.var_bukti, width=16).grid(row=1, column=1, sticky="w",
                                                                   padx=(0, 14))
        ttk.Label(atas, text="Jenis").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.var_jenis = tk.StringVar(value="JU")
        jenis = ttk.Combobox(atas, textvariable=self.var_jenis, width=6, state="readonly",
                             values=engine.JENIS_JURNAL)
        jenis.grid(row=1, column=2, sticky="w", padx=(0, 14))
        ttk.Label(atas, text="Keterangan").grid(row=0, column=3, sticky="w", padx=(0, 8))
        self.var_ket = tk.StringVar()
        self.entry_ket = ttk.Entry(atas, textvariable=self.var_ket, width=48)
        self.entry_ket.grid(row=1, column=3, sticky="ew")
        atas.columnconfigure(3, weight=1)
        ttk.Label(atas, text="JU = transaksi biasa · AJP = jurnal penyesuaian (mis. penyusutan)",
                  style="Sub.TLabel").grid(row=2, column=0, columnspan=4, sticky="w", pady=(6, 0))

        cepat = ttk.Labelframe(self, text="Transaksi cepat (isi otomatis)", padding=8)
        cepat.pack(fill="x", padx=14, pady=(4, 6))
        for i, (label, ket, a, b, _) in enumerate(TRANSAKSI_CEPAT):
            ttk.Button(cepat, text=label,
                       command=lambda a=a, b=b, k=ket: self._isi_cepat(a, b, k)
                       ).grid(row=0, column=i, padx=3, sticky="w")

        tabel = ttk.Labelframe(self, text="Rincian jurnal", padding=8)
        tabel.pack(fill="both", expand=True, padx=14)
        kepala = ttk.Frame(tabel)
        kepala.pack(fill="x")
        for teks, lebar in (("Akun", 46), ("Debit", 18), ("Kredit", 18), ("", 4)):
            ttk.Label(kepala, text=teks, width=lebar, style="Tebal.TLabel",
                      anchor="w" if teks == "Akun" else "center").pack(side="left", padx=2)
        self.wadah = ttk.Frame(tabel)
        self.wadah.pack(fill="both", expand=True, pady=(4, 0))
        ttk.Button(tabel, text="+ Tambah baris", command=self._tambah_baris).pack(anchor="w",
                                                                                  pady=(6, 0))

        bawah = ttk.Frame(self, padding=(14, 8, 14, 12))
        bawah.pack(fill="x")
        self.lbl_total = ttk.Label(bawah, text="", style="Tebal.TLabel")
        self.lbl_total.pack(side="left")
        ttk.Button(bawah, text="Batal", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(bawah, text="Simpan", style="Utama.TButton",
                   command=lambda: self._simpan(False)).pack(side="right")
        if not self.jurnal_id:
            ttk.Button(bawah, text="Simpan & Input Lagi",
                       command=lambda: self._simpan(True)).pack(side="right", padx=(0, 6))

    def _tambah_baris(self, kode: str = "", debit: float = 0, kredit: float = 0):
        baris = ttk.Frame(self.wadah)
        baris.pack(fill="x", pady=1)
        var_akun = tk.StringVar(value=self.dari_kode.get(kode, ""))
        combo = ttk.Combobox(baris, textvariable=var_akun, values=self.pilihan, width=44)
        combo.pack(side="left", padx=2)
        e_debit = w.EntriAngka(baris, 18, saat_ubah=self._hitung)
        e_debit.pack(side="left", padx=2)
        e_kredit = w.EntriAngka(baris, 18, saat_ubah=self._hitung)
        e_kredit.pack(side="left", padx=2)
        if debit:
            e_debit.set_nilai(debit)
        if kredit:
            e_kredit.set_nilai(kredit)
        data = dict(bingkai=baris, var_akun=var_akun, debit=e_debit, kredit=e_kredit)
        ttk.Button(baris, text="✕", width=3,
                   command=lambda d=data: self._hapus_baris(d)).pack(side="left", padx=2)
        self.baris_widget.append(data)
        self._hitung()
        return data

    def _hapus_baris(self, data: dict):
        data["bingkai"].destroy()
        self.baris_widget.remove(data)
        self._hitung()

    def _kosongkan(self):
        for d in list(self.baris_widget):
            d["bingkai"].destroy()
        self.baris_widget.clear()

    def _isi_cepat(self, akun_debit: str, akun_kredit: str, keterangan: str):
        def kode(x):
            if x in ("KAS", "BANK", "PEMBELIAN"):
                a = engine.akun_berperan(x)
                return a["kode"] if a else ""
            return x
        self._kosongkan()
        self._tambah_baris(kode(akun_debit))
        self._tambah_baris(kode(akun_kredit))
        if not self.var_ket.get().strip():
            self.var_ket.set(keterangan)
        self.baris_widget[0]["debit"].focus_set()

    def _hitung(self):
        td = sum(d["debit"].nilai() for d in self.baris_widget)
        tk_ = sum(d["kredit"].nilai() for d in self.baris_widget)
        selisih = round(td - tk_, 2)
        teks = f"Total Debit: {w.rp(td, '0')}     Total Kredit: {w.rp(tk_, '0')}     "
        if abs(selisih) < 0.01 and td > 0:
            self.lbl_total.configure(text=teks + "BALANCE ✓", foreground=w.HIJAU)
        else:
            self.lbl_total.configure(text=teks + f"Selisih: {w.rp(selisih, '0')}",
                                     foreground=w.MERAH if td or tk_ else w.TEKS_REDUP)

    def _muat(self, jurnal_id: int):
        j = db.koneksi().execute("SELECT * FROM jurnal WHERE id=?", (jurnal_id,)).fetchone()
        self.tanggal.set_iso(j["tanggal"])
        self.var_bukti.set(j["no_bukti"] or "")
        self.var_jenis.set(j["jenis"])
        self.var_ket.set(j["keterangan"] or "")
        for d in engine.detail_jurnal(jurnal_id):
            self._tambah_baris(d["kode_akun"], d["debit"], d["kredit"])

    def _simpan(self, lanjut: bool):
        tanggal = self.tanggal.iso()
        if not tanggal:
            w.galat("Tanggal salah", "Format tanggal harus DD/MM/YYYY.", self)
            return
        detail = []
        for d in self.baris_widget:
            pilihan = d["var_akun"].get().strip()
            kode = self.ke_kode.get(pilihan, pilihan.split(" — ")[0] if pilihan else "")
            debit, kredit = d["debit"].nilai(), d["kredit"].nilai()
            if not kode and not debit and not kredit:
                continue
            detail.append(dict(kode_akun=kode, keterangan=self.var_ket.get().strip(),
                               debit=debit, kredit=kredit))
        try:
            engine.simpan_jurnal(self.periode_id, tanggal, self.var_ket.get().strip(), detail,
                                 jenis=self.var_jenis.get(), no_bukti=self.var_bukti.get().strip(),
                                 jurnal_id=self.jurnal_id)
        except ValueError as e:
            w.galat("Transaksi belum bisa disimpan", str(e), self)
            return
        self.tersimpan = True
        if lanjut and not self.jurnal_id:
            self.var_ket.set("")
            self.var_bukti.set(engine.nomor_bukti_berikutnya(self.periode_id))
            self._kosongkan()
            for _ in range(2):
                self._tambah_baris()
            self.entry_ket.focus_set()
        else:
            self.destroy()


class DialogImpor(tk.Toplevel):
    """Pratinjau dan konfirmasi impor jurnal dari berkas Excel/CSV."""

    def __init__(self, induk, periode_id: int, path: str):
        super().__init__(induk)
        self.periode_id = periode_id
        self.terimpor = 0
        self.title("Impor Jurnal dari Excel")
        self.configure(bg=w.ABU)
        self.transient(induk)
        self.hasil = xlsio.baca_berkas_impor(path, periode_id)

        ttk.Label(self, text=os.path.basename(path), style="Judul.TLabel",
                  padding=(14, 12, 14, 0)).pack(anchor="w")
        siap = [t for t in self.hasil["transaksi"] if t["seimbang"]]
        ringkas = (f"{self.hasil['jumlah_baris']} baris dibaca · "
                   f"{len(self.hasil['transaksi'])} transaksi terbentuk · "
                   f"{len(siap)} siap diimpor · {len(self.hasil['galat'])} masalah")
        ttk.Label(self, text=ringkas, style="Sub.TLabel",
                  padding=(14, 2, 14, 8)).pack(anchor="w")

        bingkai = ttk.Frame(self, padding=(14, 0))
        bingkai.pack(fill="both", expand=True)
        tabel = w.buat_tabel(bingkai, [("tgl", "Tanggal", 90, "center"),
                                       ("bukti", "No. Bukti", 110, "center"),
                                       ("ket", "Keterangan", 330, "w"),
                                       ("jns", "Jenis", 60, "center"),
                                       ("debit", "Debit", 120, "e"),
                                       ("kredit", "Kredit", 120, "e"),
                                       ("st", "Status", 110, "center")], tinggi=12)
        baris, tag = [], {}
        for i, t in enumerate(self.hasil["transaksi"]):
            baris.append([w.tgl_id(t["tanggal"]), t["no_bukti"], t["keterangan"], t["jenis"],
                          w.rp(t["total_debit"]), w.rp(t["total_kredit"]),
                          "Siap" if t["seimbang"] else "Tidak balance"])
            if not t["seimbang"]:
                tag[i] = "merah"
        w.isi_tabel(tabel, baris, tag)

        if self.hasil["galat"]:
            kotak = ttk.Labelframe(self, text="Masalah yang ditemukan", padding=8)
            kotak.pack(fill="x", padx=14, pady=(8, 0))
            teks = tk.Text(kotak, height=5, wrap="word", bg="#FFF6F6", relief="flat")
            teks.pack(fill="x")
            teks.insert("1.0", "\n".join("• " + g for g in self.hasil["galat"][:60]))
            teks.configure(state="disabled")

        bawah = ttk.Frame(self, padding=(14, 10))
        bawah.pack(fill="x")
        ttk.Label(bawah, text="Hanya transaksi berstatus 'Siap' yang akan diimpor.",
                  style="Sub.TLabel").pack(side="left")
        ttk.Button(bawah, text="Batal", command=self.destroy).pack(side="right", padx=(6, 0))
        tombol = ttk.Button(bawah, text=f"Impor {len(siap)} Transaksi", style="Utama.TButton",
                            command=self._impor)
        tombol.pack(side="right")
        if not siap:
            tombol.state(["disabled"])
        self.geometry("980x560")
        self.grab_set()

    def _impor(self):
        try:
            self.terimpor = xlsio.impor_jurnal(self.periode_id, self.hasil["transaksi"])
        except ValueError as e:
            w.galat("Impor gagal", str(e), self)
            return
        w.info("Impor selesai", f"{self.terimpor} transaksi berhasil dimasukkan ke jurnal.", self)
        self.destroy()


class TabJurnal(ttk.Frame):
    def __init__(self, induk, aplikasi):
        super().__init__(induk, padding=12)
        self.app = aplikasi
        self.var_cari = tk.StringVar()

        atas = ttk.Frame(self)
        atas.pack(fill="x")
        ttk.Label(atas, text="Jurnal Transaksi", style="Judul.TLabel").pack(side="left")
        ttk.Label(atas, text="  Satu transaksi terdiri atas beberapa baris debit & kredit "
                            "yang jumlahnya sama.", style="Sub.TLabel").pack(side="left")

        alat = ttk.Frame(self)
        alat.pack(fill="x", pady=(10, 8))
        self.btn_baru = ttk.Button(alat, text="+  Input Transaksi", style="Utama.TButton",
                                   command=self.input_baru)
        self.btn_baru.pack(side="left")
        self.btn_ubah = ttk.Button(alat, text="Ubah", command=self.ubah)
        self.btn_ubah.pack(side="left", padx=(6, 0))
        self.btn_hapus = ttk.Button(alat, text="Hapus", command=self.hapus)
        self.btn_hapus.pack(side="left", padx=(6, 0))
        ttk.Separator(alat, orient="vertical").pack(side="left", fill="y", padx=10)
        self.btn_impor = ttk.Button(alat, text="📥  Impor dari Excel", command=self.impor)
        self.btn_impor.pack(side="left")
        ttk.Button(alat, text="📄  Unduh Template Impor",
                   command=self.unduh_template).pack(side="left", padx=(6, 0))
        ttk.Separator(alat, orient="vertical").pack(side="left", fill="y", padx=10)
        ttk.Button(alat, text="🖨  Cetak PDF", command=self.cetak_pdf).pack(side="left")
        ttk.Button(alat, text="⬇  Ekspor Excel", command=self.ekspor).pack(side="left", padx=(6, 0))
        ttk.Entry(alat, textvariable=self.var_cari, width=22).pack(side="right")
        ttk.Label(alat, text="Cari ").pack(side="right")
        self.var_cari.trace_add("write", lambda *_: self.muat())

        self.tabel = w.buat_tabel(self, [
            ("tgl", "Tanggal", 90, "center"), ("bukti", "No. Bukti", 110, "center"),
            ("ket", "Keterangan", 380, "w"), ("jns", "Jenis", 60, "center"),
            ("akun", "Akun yang terlibat", 260, "w"), ("nilai", "Nilai", 130, "e"),
            ("sumber", "Sumber", 90, "center")], tinggi=18)
        self.tabel.bind("<Double-1>", lambda e: self.ubah())

        bawah = ttk.Frame(self)
        bawah.pack(fill="x", pady=(8, 0))
        self.lbl_status = ttk.Label(bawah, text="", style="Tebal.TLabel")
        self.lbl_status.pack(side="left")

    # ------------------------------------------------------------------ data #
    @property
    def periode_id(self) -> int:
        return self.app.periode_id

    def muat(self):
        terkunci = engine.periode_terkunci(self.periode_id)
        for tombol in (self.btn_baru, self.btn_ubah, self.btn_hapus, self.btn_impor):
            tombol.state(["disabled"] if terkunci else ["!disabled"])
        daftar = engine.daftar_jurnal(self.periode_id, self.var_cari.get())
        self.baris_id = []
        baris = []
        total = 0.0
        for j in daftar:
            detail = engine.detail_jurnal(j["id"])
            akun = ", ".join(f"{d['kode_akun']}" for d in detail)
            nilai = sum(d["debit"] for d in detail)
            total += nilai
            baris.append([w.tgl_id(j["tanggal"]), j["no_bukti"] or "", j["keterangan"] or "",
                          j["jenis"], akun, w.rp(nilai), j["sumber"].title()])
            self.baris_id.append(j["id"])
        w.isi_tabel(self.tabel, baris)
        p = engine.periode(self.periode_id)
        status = " — PERIODE SUDAH DITUTUP (hanya bisa dilihat)" if terkunci else ""
        self.lbl_status.configure(
            text=f"{len(daftar)} transaksi · total nilai {w.rp_lengkap(total)}{status}",
            foreground=w.ORANYE if terkunci else w.TEKS)

    def _terpilih(self) -> int | None:
        pilih = self.tabel.selection()
        if not pilih:
            return None
        return self.baris_id[self.tabel.index(pilih[0])]

    # --------------------------------------------------------------- tindakan #
    def input_baru(self):
        if self._cek_kunci():
            return
        d = DialogJurnal(self.winfo_toplevel(), self.periode_id)
        self.wait_window(d)
        if d.tersimpan:
            self.app.segarkan()

    def ubah(self):
        jid = self._terpilih()
        if jid is None:
            w.peringatan("Belum ada yang dipilih", "Pilih dulu baris transaksi yang akan diubah.",
                         self)
            return
        if self._cek_kunci():
            return
        d = DialogJurnal(self.winfo_toplevel(), self.periode_id, jid)
        self.wait_window(d)
        if d.tersimpan:
            self.app.segarkan()

    def hapus(self):
        jid = self._terpilih()
        if jid is None:
            w.peringatan("Belum ada yang dipilih", "Pilih dulu baris transaksi yang akan dihapus.",
                         self)
            return
        if self._cek_kunci():
            return
        if not w.tanya("Hapus transaksi", "Transaksi terpilih akan dihapus permanen. Lanjutkan?",
                       self):
            return
        try:
            engine.hapus_jurnal(jid)
        except ValueError as e:
            w.galat("Gagal menghapus", str(e), self)
            return
        self.app.segarkan()

    def _cek_kunci(self) -> bool:
        if engine.periode_terkunci(self.periode_id):
            w.peringatan("Periode sudah ditutup",
                         "Periode ini sudah ditutup buku. Buka kembali lewat menu "
                         "Tutup Buku bila perlu koreksi.", self)
            return True
        return False

    def unduh_template(self):
        p = engine.periode(self.periode_id)
        bawaan = os.path.join(db.folder_keluaran(),
                              f"Template_Impor_Jurnal_{db.NAMA_BULAN[p['bulan']]}{p['tahun']}.xlsx")
        path = filedialog.asksaveasfilename(
            parent=self, title="Simpan template impor", defaultextension=".xlsx",
            initialfile=os.path.basename(bawaan), initialdir=os.path.dirname(bawaan),
            filetypes=[("Excel", "*.xlsx")])
        if not path:
            return
        xlsio.buat_template_impor(path, self.periode_id)
        w.selesai_cetak(path, self)

    def impor(self):
        if self._cek_kunci():
            return
        path = filedialog.askopenfilename(
            parent=self, title="Pilih berkas jurnal",
            filetypes=[("Excel / CSV", "*.xlsx *.xlsm *.csv"), ("Semua berkas", "*.*")])
        if not path:
            return
        try:
            d = DialogImpor(self.winfo_toplevel(), self.periode_id, path)
        except Exception as e:  # berkas rusak / format tak dikenal
            w.galat("Berkas tidak bisa dibaca", str(e), self)
            return
        self.wait_window(d)
        if d.terimpor:
            self.app.segarkan()

    def cetak_pdf(self):
        path = pdfout.cetak_jurnal_umum(self.periode_id)
        w.selesai_cetak(path, self)

    def ekspor(self):
        p = engine.periode(self.periode_id)
        path = xlsio.nama_berkas_excel("Laporan_Bulanan", p)
        xlsio.ekspor_laporan_excel(self.periode_id, path)
        w.selesai_cetak(path, self)
