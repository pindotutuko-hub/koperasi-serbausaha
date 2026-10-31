"""Tab Buku Besar, Neraca Lajur, dan Laporan Keuangan."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .. import engine, pdfout, xlsio
from . import widgets as w


# =========================================================================== #
# Buku Besar
# =========================================================================== #
class TabBukuBesar(ttk.Frame):
    def __init__(self, induk, aplikasi):
        super().__init__(induk, padding=12)
        self.app = aplikasi
        self.var_akun = tk.StringVar()
        self.var_mode = tk.StringVar(value="akun")

        atas = ttk.Frame(self)
        atas.pack(fill="x")
        ttk.Label(atas, text="Buku Besar", style="Judul.TLabel").pack(side="left")
        ttk.Radiobutton(atas, text="Per akun", value="akun", variable=self.var_mode,
                        command=self.muat).pack(side="left", padx=(16, 4))
        ttk.Radiobutton(atas, text="Rekap semua akun", value="rekap", variable=self.var_mode,
                        command=self.muat).pack(side="left")

        alat = ttk.Frame(self)
        alat.pack(fill="x", pady=(10, 8))
        ttk.Label(alat, text="Pilih akun: ").pack(side="left")
        self.combo = ttk.Combobox(alat, textvariable=self.var_akun, width=42, state="readonly")
        self.combo.pack(side="left")
        self.combo.bind("<<ComboboxSelected>>", lambda e: self.muat())
        ttk.Button(alat, text="🖨  Cetak PDF", command=self.cetak).pack(side="left", padx=(12, 0))
        ttk.Button(alat, text="⬇  Ekspor Excel", command=self.ekspor).pack(side="left", padx=(6, 0))

        self.ringkas = ttk.Frame(self)
        self.ringkas.pack(fill="x", pady=(0, 8))
        self.lbl_ringkas = ttk.Label(self.ringkas, text="", style="Tebal.TLabel")
        self.lbl_ringkas.pack(side="left")

        self.wadah = ttk.Frame(self)
        self.wadah.pack(fill="both", expand=True)
        self.tabel = None

    @property
    def periode_id(self) -> int:
        return self.app.periode_id

    def _tabel_akun(self):
        for anak in self.wadah.winfo_children():
            anak.destroy()
        self.tabel = w.buat_tabel(self.wadah, [
            ("no", "No", 50, "center"), ("tgl", "Tanggal", 90, "center"),
            ("bukti", "No. Bukti", 110, "center"), ("ket", "Keterangan", 420, "w"),
            ("jns", "Jenis", 60, "center"), ("debit", "Debit", 130, "e"),
            ("kredit", "Kredit", 130, "e"), ("saldo", "Saldo Berjalan", 140, "e")], tinggi=16)

    def _tabel_rekap(self):
        for anak in self.wadah.winfo_children():
            anak.destroy()
        self.tabel = w.buat_tabel(self.wadah, [
            ("kode", "Kode", 70, "center"), ("nama", "Nama Akun", 300, "w"),
            ("ad", "Saldo Awal D", 130, "e"), ("ak", "Saldo Awal K", 130, "e"),
            ("md", "Mutasi Debit", 130, "e"), ("mk", "Mutasi Kredit", 130, "e"),
            ("kd", "Saldo Akhir D", 130, "e"), ("kk", "Saldo Akhir K", 130, "e")], tinggi=16)

    def muat(self):
        akun = engine.daftar_akun()
        nilai = [f"{a['kode']} — {a['nama']}" for a in akun]
        self.combo.configure(values=nilai)
        if self.var_akun.get() not in nilai and nilai:
            self.var_akun.set(nilai[0])
        rekap = self.var_mode.get() == "rekap"
        self.combo.configure(state="disabled" if rekap else "readonly")
        if rekap:
            self._tabel_rekap()
            data = engine.rekap_buku_besar(self.periode_id)
            baris = [[r["kode"], r["nama"], w.rp(r["awal_d"]), w.rp(r["awal_k"]),
                      w.rp(r["mut_d"]), w.rp(r["mut_k"]), w.rp(r["akhir_d"]), w.rp(r["akhir_k"])]
                     for r in data["baris"]]
            t = data["total"]
            baris.append(["", "TOTAL", w.rp(t["awal_d"]), w.rp(t["awal_k"]), w.rp(t["mut_d"]),
                          w.rp(t["mut_k"]), w.rp(t["akhir_d"]), w.rp(t["akhir_k"])])
            w.isi_tabel(self.tabel, baris, {len(baris) - 1: "total"})
            self.lbl_ringkas.configure(
                text=f"{len(data['baris'])} akun bermutasi · total mutasi debit "
                     f"{w.rp_lengkap(t['mut_d'])} = kredit {w.rp_lengkap(t['mut_k'])}",
                foreground=w.TEKS)
            return

        self._tabel_akun()
        if not self.var_akun.get():
            return
        kode = self.var_akun.get().split(" — ")[0]
        bb = engine.buku_besar(self.periode_id, kode)
        baris = [["", "", "", "Saldo Awal", "", w.rp(bb["saldo_awal_d"]),
                  w.rp(bb["saldo_awal_k"]), w.rp(bb["saldo_awal"])]]
        for r in bb["baris"]:
            baris.append([r["no"], w.tgl_id(r["tanggal"]), r["no_bukti"], r["keterangan"],
                          r["jenis"], w.rp(r["debit"]), w.rp(r["kredit"]), w.rp(r["saldo"])])
        baris.append(["", "", "", "SALDO AKHIR", "", w.rp(bb["total_debit"]),
                      w.rp(bb["total_kredit"]), w.rp(bb["saldo_akhir"])])
        w.isi_tabel(self.tabel, baris, {0: "judul", len(baris) - 1: "total"})
        self.lbl_ringkas.configure(
            text=f"Saldo normal {bb['akun']['saldo_normal']} · saldo awal "
                 f"{w.rp_lengkap(bb['saldo_awal'])} · mutasi {len(bb['baris'])} baris · "
                 f"saldo akhir {w.rp_lengkap(bb['saldo_akhir'])}", foreground=w.TEKS)

    def cetak(self):
        if self.var_mode.get() == "rekap":
            path = pdfout.cetak_rekap_buku_besar(self.periode_id)
        else:
            path = pdfout.cetak_buku_besar(self.periode_id, self.var_akun.get().split(" — ")[0])
        w.selesai_cetak(path, self)

    def ekspor(self):
        p = engine.periode(self.periode_id)
        if self.var_mode.get() == "rekap":
            path = xlsio.nama_berkas_excel("Laporan_Bulanan", p)
            xlsio.ekspor_laporan_excel(self.periode_id, path)
        else:
            kode = self.var_akun.get().split(" — ")[0]
            path = xlsio.nama_berkas_excel(f"Buku_Besar_{kode}", p)
            xlsio.ekspor_buku_besar_excel(self.periode_id, kode, path)
        w.selesai_cetak(path, self)


# =========================================================================== #
# Neraca Lajur
# =========================================================================== #
class TabNeracaLajur(ttk.Frame):
    def __init__(self, induk, aplikasi):
        super().__init__(induk, padding=12)
        self.app = aplikasi

        atas = ttk.Frame(self)
        atas.pack(fill="x")
        ttk.Label(atas, text="Neraca Lajur (Worksheet)", style="Judul.TLabel").pack(side="left")
        ttk.Label(atas, text="  Neraca Saldo → Penyesuaian → Laba Rugi → Neraca",
                  style="Sub.TLabel").pack(side="left")

        opname = ttk.Labelframe(self, text="Persediaan akhir (stock opname)", padding=8)
        opname.pack(fill="x", pady=(10, 8))
        ttk.Label(opname, text="Nilai persediaan barang hasil hitung fisik akhir bulan: Rp"
                  ).pack(side="left")
        self.entry_opname = w.EntriAngka(opname, 18)
        self.entry_opname.pack(side="left", padx=6)
        self.btn_simpan_opname = ttk.Button(opname, text="Simpan", command=self.simpan_opname)
        self.btn_simpan_opname.pack(side="left")
        self.btn_kosong_opname = ttk.Button(opname, text="Kosongkan", command=self.hapus_opname)
        self.btn_kosong_opname.pack(side="left", padx=(6, 0))
        self.lbl_opname = ttk.Label(opname, text="", style="Sub.TLabel")
        self.lbl_opname.pack(side="left", padx=(12, 0))
        ttk.Button(opname, text="🖨  Cetak PDF", command=self.cetak).pack(side="right")
        ttk.Button(opname, text="⬇  Ekspor Excel",
                   command=self.ekspor).pack(side="right", padx=(0, 6))

        self.tabel = w.buat_tabel(self, [
            ("kode", "Kode", 60, "center"), ("nama", "Nama Akun", 220, "w"),
            ("nsd", "NS Debet", 110, "e"), ("nsk", "NS Kredit", 110, "e"),
            ("ajd", "AJP Debet", 100, "e"), ("ajk", "AJP Kredit", 100, "e"),
            ("dsd", "NSD Debet", 110, "e"), ("dsk", "NSD Kredit", 110, "e"),
            ("lrd", "L/R Debet", 110, "e"), ("lrk", "L/R Kredit", 110, "e"),
            ("nrd", "Neraca Debet", 110, "e"), ("nrk", "Neraca Kredit", 110, "e")], tinggi=18)

        bawah = ttk.Frame(self)
        bawah.pack(fill="x", pady=(8, 0))
        self.lbl_status = ttk.Label(bawah, text="", style="Tebal.TLabel")
        self.lbl_status.pack(side="left")

    @property
    def periode_id(self) -> int:
        return self.app.periode_id

    def muat(self):
        nl = engine.neraca_lajur(self.periode_id)
        p = nl["periode"]
        terkunci = p["status"] == "TUTUP"
        for tombol in (self.btn_simpan_opname, self.btn_kosong_opname):
            tombol.state(["disabled"] if terkunci else ["!disabled"])
        self.entry_opname.configure(state="disabled" if terkunci else "normal")
        self.entry_opname.set_nilai(p["persediaan_akhir"] or 0)
        self.lbl_opname.configure(
            text="(sudah diisi)" if nl["opname_diisi"]
            else "(belum diisi — dianggap sama dengan persediaan awal, HPP = pembelian saja)")

        baris = [[r["kode"], r["nama"], w.rp(r["ns_d"]), w.rp(r["ns_k"]), w.rp(r["adj_d"]),
                  w.rp(r["adj_k"]), w.rp(r["nsd_d"]), w.rp(r["nsd_k"]), w.rp(r["lr_d"]),
                  w.rp(r["lr_k"]), w.rp(r["nrc_d"]), w.rp(r["nrc_k"])] for r in nl["baris"]]
        t = nl["total"]
        baris.append(["", "TOTAL", w.rp(t["ns_d"]), w.rp(t["ns_k"]), w.rp(t["adj_d"]),
                      w.rp(t["adj_k"]), w.rp(t["nsd_d"]), w.rp(t["nsd_k"]), w.rp(t["lr_d"]),
                      w.rp(t["lr_k"]), w.rp(t["nrc_d"]), w.rp(t["nrc_k"])])
        shu = nl["shu"]
        baris.append(["", "SHU (Laba)" if shu >= 0 else "Rugi", "", "", "", "", "", "",
                      w.rp(max(shu, 0)), w.rp(max(-shu, 0)), w.rp(max(-shu, 0)), w.rp(max(shu, 0))])
        jml_lr = t["lr_d"] + max(shu, 0)
        jml_nr = t["nrc_d"] + max(-shu, 0)
        baris.append(["", "JUMLAH", "", "", "", "", "", "", w.rp(jml_lr), w.rp(jml_lr),
                      w.rp(jml_nr), w.rp(jml_nr)])
        w.isi_tabel(self.tabel, baris, {len(baris) - 3: "total", len(baris) - 2: "judul",
                                        len(baris) - 1: "total"})
        if nl["seimbang"]:
            self.lbl_status.configure(text=f"BALANCE ✓   SHU periode ini: {w.rp_lengkap(shu)}",
                                      foreground=w.HIJAU if shu >= 0 else w.ORANYE)
        else:
            self.lbl_status.configure(
                text=f"TIDAK BALANCE — selisih {w.rp(t['nsd_d'] - t['nsd_k'])}. Periksa jurnal.",
                foreground=w.MERAH)

    def simpan_opname(self):
        engine.set_persediaan_akhir(self.periode_id, self.entry_opname.nilai())
        self.app.segarkan()

    def hapus_opname(self):
        engine.set_persediaan_akhir(self.periode_id, None)
        self.app.segarkan()

    def cetak(self):
        w.selesai_cetak(pdfout.cetak_neraca_lajur(self.periode_id), self)

    def ekspor(self):
        p = engine.periode(self.periode_id)
        path = xlsio.nama_berkas_excel("Laporan_Bulanan", p)
        xlsio.ekspor_laporan_excel(self.periode_id, path)
        w.selesai_cetak(path, self)


# =========================================================================== #
# Laporan Keuangan
# =========================================================================== #
class TabLaporan(ttk.Frame):
    LAPORAN = [("Laba Rugi", "laba_rugi"), ("Perubahan Modal", "perubahan_modal"),
               ("Neraca", "neraca"), ("Arus Kas", "arus_kas"),
               ("Rekap Penjualan Harian", "rekap_penjualan")]

    def __init__(self, induk, aplikasi):
        super().__init__(induk, padding=12)
        self.app = aplikasi

        atas = ttk.Frame(self)
        atas.pack(fill="x")
        ttk.Label(atas, text="Laporan Keuangan", style="Judul.TLabel").pack(side="left")
        ttk.Button(atas, text="📦  Cetak Semua Laporan (1 PDF)", style="Utama.TButton",
                   command=self.cetak_paket).pack(side="right")
        ttk.Button(atas, text="⬇  Ekspor Semua ke Excel",
                   command=self.ekspor).pack(side="right", padx=(0, 6))
        ttk.Button(atas, text="🖨  Cetak Laporan Ini",
                   command=self.cetak).pack(side="right", padx=(0, 6))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, pady=(10, 0))
        self.tabel: dict[str, ttk.Treeview] = {}
        for judul, kunci in self.LAPORAN:
            bingkai = ttk.Frame(self.notebook, padding=8)
            self.notebook.add(bingkai, text=judul)
            if kunci in ("laba_rugi", "arus_kas"):
                kolom = [("uraian", "Uraian", 460, "w"), ("jumlah", "Jumlah", 170, "e"),
                         ("total", "Total", 170, "e")]
            elif kunci == "perubahan_modal":
                kolom = [("kode", "Kode", 70, "center"), ("nama", "Uraian", 260, "w"),
                         ("awal", "Saldo Awal", 150, "e"), ("mutasi", "Setoran/Mutasi", 150, "e"),
                         ("shu", "SHU Periode", 150, "e"), ("akhir", "Saldo Akhir", 150, "e")]
            elif kunci == "neraca":
                kolom = [("a", "AKTIVA", 300, "w"), ("b", "Jumlah", 160, "e"),
                         ("c", "KEWAJIBAN & MODAL", 300, "w"), ("d", "Jumlah", 160, "e")]
            else:
                kolom = [("no", "No", 60, "center"), ("tgl", "Tanggal", 160, "center"),
                         ("nilai", "Penjualan", 180, "e")]
            self.tabel[kunci] = w.buat_tabel(bingkai, kolom, tinggi=16)

        self.lbl_info = ttk.Label(self, text="", style="Sub.TLabel")
        self.lbl_info.pack(anchor="w", pady=(8, 0))

    @property
    def periode_id(self) -> int:
        return self.app.periode_id

    def kunci_aktif(self) -> str:
        return self.LAPORAN[self.notebook.index(self.notebook.select())][1]

    # ------------------------------------------------------------------ muat #
    def muat(self):
        nl = engine.neraca_lajur(self.periode_id)
        self._laba_rugi(engine.laba_rugi(self.periode_id, nl))
        self._perubahan_modal(engine.perubahan_modal(self.periode_id, nl))
        self._neraca(engine.neraca(self.periode_id, nl))
        self._arus_kas(engine.arus_kas(self.periode_id))
        self._penjualan(engine.rekap_penjualan_harian(self.periode_id))
        p = nl["periode"]
        self.lbl_info.configure(
            text=f"Periode {engine.nama_periode(p['tahun'], p['bulan'])} · "
                 f"{'sudah ditutup' if p['status'] == 'TUTUP' else 'masih aktif'} · "
                 "semua laporan dihitung otomatis dari jurnal dan saldo awal.")

    def _laba_rugi(self, lr: dict):
        baris, tag = [], {}

        def tambah(label, jumlah=None, total=None, gaya=""):
            baris.append([label, w.rp(jumlah) if jumlah is not None else "",
                          w.rp(total) if total is not None else ""])
            if gaya:
                tag[len(baris) - 1] = gaya

        tambah("PENDAPATAN USAHA", gaya="judul")
        for x in lr["pendapatan"]:
            tambah("    " + x["nama"], x["nilai"])
        for x in lr["potongan_penjualan"]:
            tambah(f"    ({x['nama']})", -x["nilai"])
        tambah("    Total Pendapatan Bersih", None, lr["total_pendapatan"], "total")
        tambah("HARGA POKOK PENJUALAN", gaya="judul")
        tambah("    Persediaan Barang Dagang (Awal)", lr["persediaan_awal"])
        tambah("    Pembelian Barang Dagang", lr["pembelian"])
        tambah("    Beban Angkut Pembelian", lr["angkut"])
        tambah("    (Retur Pembelian)", -lr["retur_beli"])
        tambah("    (Potongan Pembelian)", -lr["potongan_beli"])
        tambah("    Barang Tersedia Dijual", None, lr["barang_tersedia"])
        tambah("    (Persediaan Barang Dagang Akhir)", -lr["persediaan_akhir"])
        tambah("    Total Harga Pokok Penjualan", None, lr["hpp"], "total")
        tambah("LABA KOTOR", None, lr["laba_kotor"], "total")
        tambah("BEBAN OPERASIONAL", gaya="judul")
        for x in lr["beban"]:
            tambah("    " + x["nama"], x["nilai"])
        tambah("    Total Beban Operasional", None, lr["total_beban"], "total")
        tambah("SISA HASIL USAHA (SHU)" if lr["shu"] >= 0 else "RUGI BERSIH",
               None, lr["shu"], "total")
        w.isi_tabel(self.tabel["laba_rugi"], baris, tag)

    def _perubahan_modal(self, pm: dict):
        baris = [[b["kode"], b["nama"], w.rp(b["awal"]), w.rp(b["mutasi"]), w.rp(b["shu"]),
                  w.rp(b["akhir"])] for b in pm["baris"]]
        t = pm["total"]
        baris.append(["", "TOTAL MODAL", w.rp(t["awal"]), w.rp(t["mutasi"]), w.rp(t["shu"]),
                      w.rp(t["akhir"])])
        w.isi_tabel(self.tabel["perubahan_modal"], baris, {len(baris) - 1: "total"})

    def _neraca(self, n: dict):
        kiri = [("AKTIVA LANCAR", None, "judul")]
        kiri += [(f"    {a['nama']}", a["nilai"], "") for a in n["aktiva_lancar"]]
        kiri.append(("    Total Aktiva Lancar", n["total_lancar"], "total"))
        kiri.append(("AKTIVA TETAP", None, "judul"))
        kiri += [(f"    {a['nama']}", a["nilai"], "") for a in n["aktiva_tetap"]]
        kiri.append(("    Total Aktiva Tetap", n["total_tetap"], "total"))
        kiri.append(("TOTAL AKTIVA", n["total_aktiva"], "total"))
        kanan = [("KEWAJIBAN", None, "judul")]
        kanan += [(f"    {a['nama']}", a["nilai"], "") for a in n["kewajiban"]]
        kanan.append(("    Total Kewajiban", n["total_kewajiban"], "total"))
        kanan.append(("MODAL / EKUITAS", None, "judul"))
        kanan += [(f"    {a['nama']}", a["nilai"], "") for a in n["modal"]]
        kanan.append(("    Total Modal", n["total_modal"], "total"))
        kanan.append(("TOTAL KEWAJIBAN & MODAL", n["total_pasiva"], "total"))
        while len(kiri) < len(kanan):
            kiri.append(("", None, ""))
        while len(kanan) < len(kiri):
            kanan.append(("", None, ""))
        baris, tag = [], {}
        for i, ((lk, lv, lt), (rk, rv, rt)) in enumerate(zip(kiri, kanan)):
            baris.append([lk, w.rp(lv) if lv is not None else "",
                          rk, w.rp(rv) if rv is not None else ""])
            if "total" in (lt, rt) or "judul" in (lt, rt):
                tag[i] = "total" if "total" in (lt, rt) else "judul"
        w.isi_tabel(self.tabel["neraca"], baris, tag)

    def _arus_kas(self, ak: dict):
        baris, tag = [], {}

        def tambah(label, jumlah=None, total=None, gaya=""):
            baris.append([label, w.rp(jumlah) if jumlah is not None else "",
                          w.rp(total) if total is not None else ""])
            if gaya:
                tag[len(baris) - 1] = gaya

        tambah("Saldo Kas & Bank Awal Periode", None, ak["awal"], "total")
        tambah("PENERIMAAN", gaya="judul")
        for nama, nilai in ak["masuk"]:
            tambah("    " + nama, nilai)
        tambah("    Total Penerimaan", None, ak["total_masuk"], "total")
        tambah("PENGELUARAN", gaya="judul")
        for nama, nilai in ak["keluar"]:
            tambah("    " + nama, nilai)
        tambah("    Total Pengeluaran", None, ak["total_keluar"], "total")
        tambah("SALDO KAS & BANK AKHIR PERIODE", None, ak["akhir"], "total")
        w.isi_tabel(self.tabel["arus_kas"], baris, tag)

    def _penjualan(self, rk: dict):
        baris = [[i, w.tgl_id(b["tanggal"]), w.rp(b["nilai"])]
                 for i, b in enumerate(rk["baris"], start=1)]
        baris.append(["", f"TOTAL ({rk['hari']} hari, rata-rata {w.rp(rk['rata'])})",
                      w.rp(rk["total"])])
        w.isi_tabel(self.tabel["rekap_penjualan"], baris, {len(baris) - 1: "total"})

    # ---------------------------------------------------------------- cetak  #
    def cetak(self):
        fungsi = {"laba_rugi": pdfout.cetak_laba_rugi,
                  "perubahan_modal": pdfout.cetak_perubahan_modal,
                  "neraca": pdfout.cetak_neraca,
                  "arus_kas": pdfout.cetak_arus_kas,
                  "rekap_penjualan": pdfout.cetak_rekap_penjualan}[self.kunci_aktif()]
        w.selesai_cetak(fungsi(self.periode_id), self)

    def cetak_paket(self):
        try:
            path = pdfout.cetak_paket_lengkap(self.periode_id)
        except Exception as e:
            w.galat("Gagal menggabungkan PDF", str(e), self)
            return
        w.selesai_cetak(path, self)

    def ekspor(self):
        p = engine.periode(self.periode_id)
        path = xlsio.nama_berkas_excel("Laporan_Bulanan", p)
        xlsio.ekspor_laporan_excel(self.periode_id, path)
        w.selesai_cetak(path, self)
