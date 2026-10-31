"""Impor jurnal dari Excel (dengan template) dan ekspor laporan ke Excel."""
from __future__ import annotations

import os
from datetime import date, datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from . import db, engine, pdfout

KOLOM_TEMPLATE = ["No Bukti", "Tanggal", "Kode Akun", "Keterangan", "Debit", "Kredit", "Jenis"]

FONT_JUDUL = Font(name="Arial", size=12, bold=True, color="1F4E79")
FONT_HEAD = Font(name="Arial", size=10, bold=True, color="FFFFFF")
FONT_BIASA = Font(name="Arial", size=10)
FONT_TEBAL = Font(name="Arial", size=10, bold=True)
FONT_INPUT = Font(name="Arial", size=10, color="0000FF")
ISI_HEAD = PatternFill("solid", fgColor="1F4E79")
ISI_KUNING = PatternFill("solid", fgColor="FFF2CC")
ISI_ABU = PatternFill("solid", fgColor="F2F2F2")
GARIS = Border(*[Side(style="thin", color="9DB2C6")] * 4)
FMT_RP = '#,##0;(#,##0);"-"'


def _lebar(ws, lebar: dict[str, int]) -> None:
    for kolom, n in lebar.items():
        ws.column_dimensions[kolom].width = n


# --------------------------------------------------------------------------- #
# Template impor
# --------------------------------------------------------------------------- #
def buat_template_impor(path: str, periode_id: int | None = None) -> str:
    akun = engine.daftar_akun()
    p = engine.periode(periode_id) if periode_id else engine.periode_berjalan()
    contoh_tgl = date(p["tahun"], p["bulan"], 1) if p else date.today()

    wb = Workbook()
    ws = wb.active
    ws.title = "Jurnal"
    ws["A1"] = "TEMPLATE IMPOR JURNAL — PROGRAM PEMBUKUAN KANTIN KOPERASI"
    ws["A1"].font = FONT_JUDUL
    ws["A2"] = (f"Periode tujuan: {engine.nama_periode(p['tahun'], p['bulan'])}. "
                "Isi mulai baris 6. Satu transaksi = beberapa baris dengan NO BUKTI yang sama; "
                "total Debit harus = total Kredit.")
    ws["A2"].font = Font(name="Arial", size=9, italic=True)
    ws["A3"] = ("Kolom Jenis: JU = transaksi biasa, AJP = jurnal penyesuaian (mis. penyusutan). "
                "Tanggal format DD/MM/YYYY atau YYYY-MM-DD. Isi Debit ATAU Kredit, jangan keduanya.")
    ws["A3"].font = Font(name="Arial", size=9, italic=True)

    for i, judul in enumerate(KOLOM_TEMPLATE, start=1):
        sel = ws.cell(5, i, judul)
        sel.font = FONT_HEAD
        sel.fill = ISI_HEAD
        sel.border = GARIS
        sel.alignment = Alignment(horizontal="center", vertical="center")

    contoh = [
        ["BKK-001", contoh_tgl, akun[0]["kode"] if akun else "111",
         "CONTOH — hapus baris ini: rekap penjualan kantin", 500000, 0, "JU"],
        ["BKK-001", contoh_tgl, "411", "CONTOH — hapus baris ini: rekap penjualan kantin",
         0, 500000, "JU"],
    ]
    for r, baris in enumerate(contoh, start=6):
        for c, nilai in enumerate(baris, start=1):
            sel = ws.cell(r, c, nilai)
            sel.font = FONT_INPUT
            sel.fill = ISI_KUNING
            sel.border = GARIS
            if c == 2:
                sel.number_format = "DD/MM/YYYY"
            if c in (5, 6):
                sel.number_format = FMT_RP
    for r in range(8, 400):
        for c in range(1, 8):
            sel = ws.cell(r, c)
            sel.border = GARIS
            sel.font = FONT_INPUT
            if c == 2:
                sel.number_format = "DD/MM/YYYY"
            if c in (5, 6):
                sel.number_format = FMT_RP

    ws_akun = wb.create_sheet("DaftarAkun")
    ws_akun["A1"] = "DAFTAR AKUN (salin kodenya ke kolom Kode Akun)"
    ws_akun["A1"].font = FONT_JUDUL
    for i, judul in enumerate(["Kode", "Nama Akun", "Kategori", "Saldo Normal"], start=1):
        sel = ws_akun.cell(3, i, judul)
        sel.font = FONT_HEAD
        sel.fill = ISI_HEAD
        sel.border = GARIS
    for r, a in enumerate(akun, start=4):
        for c, nilai in enumerate([a["kode"], a["nama"], a["kategori"], a["saldo_normal"]], start=1):
            sel = ws_akun.cell(r, c, nilai)
            sel.font = FONT_BIASA
            sel.border = GARIS
    _lebar(ws_akun, {"A": 10, "B": 38, "C": 14, "D": 14})

    if akun:
        akhir = 3 + len(akun)
        dv = DataValidation(type="list", formula1=f"=DaftarAkun!$A$4:$A${akhir}",
                            allow_blank=True, showDropDown=False)
        dv.error = "Kode akun tidak ada di Daftar Akun."
        dv.prompt = "Pilih kode akun dari daftar."
        ws.add_data_validation(dv)
        dv.add(f"C6:C399")
    dv2 = DataValidation(type="list", formula1='"JU,AJP"', allow_blank=True, showDropDown=False)
    ws.add_data_validation(dv2)
    dv2.add("G6:G399")

    _lebar(ws, {"A": 14, "B": 13, "C": 11, "D": 52, "E": 16, "F": 16, "G": 8})
    ws.freeze_panes = "A6"
    wb.save(path)
    return path


# --------------------------------------------------------------------------- #
# Pembacaan berkas impor
# --------------------------------------------------------------------------- #
def _ke_tanggal(nilai) -> str | None:
    if nilai is None or str(nilai).strip() == "":
        return None
    if isinstance(nilai, datetime):
        return nilai.date().isoformat()
    if isinstance(nilai, date):
        return nilai.isoformat()
    teks = str(nilai).strip().replace(".", "/").replace("-", "/")
    for pola in ("%d/%m/%Y", "%Y/%m/%d", "%d/%m/%y"):
        try:
            return datetime.strptime(teks, pola).date().isoformat()
        except ValueError:
            continue
    return None


def _ke_angka(nilai) -> float:
    if nilai is None or str(nilai).strip() == "":
        return 0.0
    if isinstance(nilai, (int, float)):
        return float(nilai)
    teks = str(nilai).strip().replace("Rp", "").replace(" ", "")
    teks = teks.replace(".", "").replace(",", ".") if "," in teks else teks.replace(".", "")
    try:
        return float(teks or 0)
    except ValueError:
        return 0.0


def baca_berkas_impor(path: str, periode_id: int) -> dict:
    """Membaca berkas Excel/CSV impor dan mengelompokkannya menjadi transaksi."""
    p = engine.periode(periode_id)
    kode_akun = set(engine.peta_akun().keys())
    baris_mentah: list[dict] = []
    galat: list[str] = []

    if path.lower().endswith(".csv"):
        import csv
        with open(path, newline="", encoding="utf-8-sig") as f:
            contoh = f.read(4096)
            f.seek(0)
            pemisah = ";" if contoh.count(";") > contoh.count(",") else ","
            for n, row in enumerate(csv.DictReader(f, delimiter=pemisah), start=2):
                baris_mentah.append({"_baris": n, **{(k or "").strip(): v for k, v in row.items()}})
    else:
        wb = load_workbook(path, data_only=True)
        ws = wb["Jurnal"] if "Jurnal" in wb.sheetnames else wb.worksheets[0]
        baris_judul = None
        for r in range(1, min(ws.max_row, 30) + 1):
            nilai = [str(ws.cell(r, c).value or "").strip().lower() for c in range(1, 9)]
            if "kode akun" in nilai and ("debit" in nilai or "kredit" in nilai):
                baris_judul = r
                break
        if baris_judul is None:
            return dict(transaksi=[], galat=["Baris judul kolom tidak ditemukan. Gunakan "
                                             "template impor (menu Jurnal → Unduh Template)."],
                        jumlah_baris=0)
        judul = {}
        for c in range(1, ws.max_column + 1):
            nama = str(ws.cell(baris_judul, c).value or "").strip()
            if nama:
                judul[c] = nama
        for r in range(baris_judul + 1, ws.max_row + 1):
            data = {judul[c]: ws.cell(r, c).value for c in judul}
            if all(v is None or str(v).strip() == "" for v in data.values()):
                continue
            data["_baris"] = r
            baris_mentah.append(data)

    def ambil(d: dict, *nama_kolom):
        for n in nama_kolom:
            for k, v in d.items():
                if str(k).strip().lower() == n.lower():
                    return v
        return None

    kelompok: dict[str, dict] = {}
    urut_kelompok: list[str] = []
    for d in baris_mentah:
        no_baris = d.get("_baris")
        ket = str(ambil(d, "Keterangan") or "").strip()
        if ket.upper().startswith("CONTOH"):
            continue
        kode = ambil(d, "Kode Akun", "Kode", "Akun")
        kode = str(int(kode)) if isinstance(kode, float) and kode.is_integer() else str(kode or "").strip()
        tanggal = _ke_tanggal(ambil(d, "Tanggal"))
        debit = _ke_angka(ambil(d, "Debit"))
        kredit = _ke_angka(ambil(d, "Kredit"))
        jenis = str(ambil(d, "Jenis") or "JU").strip().upper() or "JU"
        bukti = str(ambil(d, "No Bukti", "No. Bukti", "Bukti") or "").strip()

        if not kode and not debit and not kredit:
            continue
        if kode not in kode_akun:
            galat.append(f"Baris {no_baris}: kode akun '{kode}' tidak terdaftar di COA.")
            continue
        if tanggal is None:
            galat.append(f"Baris {no_baris}: tanggal kosong / format tidak dikenali.")
            continue
        if (tanggal[:4], tanggal[5:7]) != (str(p["tahun"]), f"{p['bulan']:02d}"):
            galat.append(f"Baris {no_baris}: tanggal {tanggal} di luar periode "
                         f"{engine.nama_periode(p['tahun'], p['bulan'])}.")
            continue
        if debit and kredit:
            galat.append(f"Baris {no_baris}: Debit dan Kredit terisi keduanya.")
            continue
        if not debit and not kredit:
            galat.append(f"Baris {no_baris}: Debit dan Kredit kosong.")
            continue
        if jenis not in engine.JENIS_JURNAL:
            jenis = "JU"

        kunci = bukti or f"__{tanggal}|{ket}|{jenis}"
        if kunci not in kelompok:
            kelompok[kunci] = dict(no_bukti=bukti, tanggal=tanggal, keterangan=ket,
                                   jenis=jenis, detail=[])
            urut_kelompok.append(kunci)
        g = kelompok[kunci]
        if not g["keterangan"] and ket:
            g["keterangan"] = ket
        g["detail"].append(dict(kode_akun=kode, keterangan=ket, debit=debit, kredit=kredit))

    transaksi = []
    for kunci in urut_kelompok:
        g = kelompok[kunci]
        td = sum(x["debit"] for x in g["detail"])
        tk = sum(x["kredit"] for x in g["detail"])
        g["total_debit"] = round(td, 2)
        g["total_kredit"] = round(tk, 2)
        g["seimbang"] = abs(td - tk) < 0.01
        if not g["seimbang"]:
            galat.append(f"Transaksi '{g['no_bukti'] or g['keterangan'][:30]}' "
                         f"({g['tanggal']}) tidak balance: debit {td:,.0f} vs kredit {tk:,.0f}.")
        transaksi.append(g)
    return dict(transaksi=transaksi, galat=galat, jumlah_baris=len(baris_mentah))


def impor_jurnal(periode_id: int, transaksi: list[dict]) -> int:
    jumlah = 0
    for t in transaksi:
        if not t.get("seimbang", False):
            continue
        engine.simpan_jurnal(periode_id, t["tanggal"], t["keterangan"], t["detail"],
                             jenis=t.get("jenis", "JU"), no_bukti=t.get("no_bukti", ""),
                             sumber="IMPOR")
        jumlah += 1
    return jumlah


# --------------------------------------------------------------------------- #
# Ekspor laporan ke Excel
# --------------------------------------------------------------------------- #
def _tulis_tabel(ws, judul: str, sub: str, header: list[str], baris: list[list],
                 baris_tebal: list[int] | None = None, kolom_angka: tuple = ()) -> None:
    ws["A1"] = db.ambil_pengaturan("nama_koperasi")
    ws["A1"].font = Font(name="Arial", size=11, bold=True)
    ws["A2"] = judul
    ws["A2"].font = FONT_JUDUL
    ws["A3"] = sub
    ws["A3"].font = Font(name="Arial", size=9, italic=True)
    for i, h in enumerate(header, start=1):
        sel = ws.cell(5, i, h)
        sel.font = FONT_HEAD
        sel.fill = ISI_HEAD
        sel.border = GARIS
        sel.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for r, data in enumerate(baris, start=6):
        for c, nilai in enumerate(data, start=1):
            sel = ws.cell(r, c, nilai)
            sel.font = FONT_TEBAL if (baris_tebal and (r - 6) in baris_tebal) else FONT_BIASA
            sel.border = GARIS
            if c in kolom_angka:
                sel.number_format = FMT_RP
            if baris_tebal and (r - 6) in baris_tebal:
                sel.fill = ISI_ABU
    ws.freeze_panes = "A6"


def ekspor_laporan_excel(periode_id: int, path: str) -> str:
    p = engine.periode(periode_id)
    per = engine.nama_periode(p["tahun"], p["bulan"])
    nl = engine.neraca_lajur(periode_id)
    lr = engine.laba_rugi(periode_id, nl)
    pm = engine.perubahan_modal(periode_id, nl)
    nr = engine.neraca(periode_id, nl)
    rek = engine.rekap_buku_besar(periode_id)

    wb = Workbook()

    ws = wb.active
    ws.title = "JurnalUmum"
    baris = [[engine.bulat(0) if False else r["tanggal"], r["no_bukti"], r["kode_akun"],
              r["nama_akun"], r["keterangan"] or r["ket_induk"], r["jenis"],
              r["debit"] or 0, r["kredit"] or 0]
             for r in engine.jurnal_umum(periode_id)]
    total_d = sum(b[6] for b in baris)
    total_k = sum(b[7] for b in baris)
    baris.append(["", "", "", "TOTAL", "", "", total_d, total_k])
    _tulis_tabel(ws, "JURNAL UMUM", f"Periode {per}",
                 ["Tanggal", "No Bukti", "Kode", "Nama Akun", "Keterangan", "Jenis",
                  "Debit", "Kredit"], baris, [len(baris) - 1], (7, 8))
    _lebar(ws, {"A": 12, "B": 14, "C": 8, "D": 26, "E": 46, "F": 7, "G": 16, "H": 16})

    ws = wb.create_sheet("RekapBukuBesar")
    baris = [[r["kode"], r["nama"], r["awal_d"], r["awal_k"], r["mut_d"], r["mut_k"],
              r["akhir_d"], r["akhir_k"]] for r in rek["baris"]]
    t = rek["total"]
    baris.append(["", "TOTAL", t["awal_d"], t["awal_k"], t["mut_d"], t["mut_k"],
                  t["akhir_d"], t["akhir_k"]])
    _tulis_tabel(ws, "REKAPITULASI BUKU BESAR", f"Periode {per}",
                 ["Kode", "Nama Akun", "Saldo Awal D", "Saldo Awal K", "Mutasi Debit",
                  "Mutasi Kredit", "Saldo Akhir D", "Saldo Akhir K"],
                 baris, [len(baris) - 1], (3, 4, 5, 6, 7, 8))
    _lebar(ws, {"A": 8, "B": 30, "C": 15, "D": 15, "E": 15, "F": 15, "G": 15, "H": 15})

    ws = wb.create_sheet("NeracaLajur")
    baris = [[r["kode"], r["nama"], r["ns_d"], r["ns_k"], r["adj_d"], r["adj_k"],
              r["nsd_d"], r["nsd_k"], r["lr_d"], r["lr_k"], r["nrc_d"], r["nrc_k"]]
             for r in nl["baris"]]
    t = nl["total"]
    baris.append(["", "TOTAL", t["ns_d"], t["ns_k"], t["adj_d"], t["adj_k"], t["nsd_d"],
                  t["nsd_k"], t["lr_d"], t["lr_k"], t["nrc_d"], t["nrc_k"]])
    baris.append(["", "SHU (Laba/Rugi)", "", "", "", "", "", "",
                  max(nl["shu"], 0), max(-nl["shu"], 0), max(-nl["shu"], 0), max(nl["shu"], 0)])
    _tulis_tabel(ws, "NERACA LAJUR (WORKSHEET)", f"Periode {per}",
                 ["Kode", "Nama Akun", "NS Debet", "NS Kredit", "AJP Debet", "AJP Kredit",
                  "NSD Debet", "NSD Kredit", "L/R Debet", "L/R Kredit", "Neraca Debet",
                  "Neraca Kredit"], baris, [len(baris) - 2, len(baris) - 1],
                 tuple(range(3, 13)))
    _lebar(ws, dict({"A": 8, "B": 30}, **{get_column_letter(i): 14 for i in range(3, 13)}))

    ws = wb.create_sheet("LabaRugi")
    baris = [["PENDAPATAN USAHA", None, None]]
    tebal = [0]
    for x in lr["pendapatan"]:
        baris.append([f"   {x['nama']}", x["nilai"], None])
    for x in lr["potongan_penjualan"]:
        baris.append([f"   ({x['nama']})", -x["nilai"], None])
    baris.append(["   Total Pendapatan Bersih", None, lr["total_pendapatan"]])
    tebal.append(len(baris) - 1)
    baris.append(["HARGA POKOK PENJUALAN", None, None])
    tebal.append(len(baris) - 1)
    for label, nilai in (("Persediaan Awal", lr["persediaan_awal"]),
                         ("Pembelian Barang Dagang", lr["pembelian"]),
                         ("Beban Angkut Pembelian", lr["angkut"]),
                         ("(Retur Pembelian)", -lr["retur_beli"]),
                         ("(Potongan Pembelian)", -lr["potongan_beli"])):
        baris.append([f"   {label}", nilai, None])
    baris.append(["   Barang Tersedia Dijual", None, lr["barang_tersedia"]])
    baris.append(["   (Persediaan Akhir)", -lr["persediaan_akhir"], None])
    baris.append(["   Total HPP", None, lr["hpp"]])
    tebal.append(len(baris) - 1)
    baris.append(["LABA KOTOR", None, lr["laba_kotor"]])
    tebal.append(len(baris) - 1)
    baris.append(["BEBAN OPERASIONAL", None, None])
    tebal.append(len(baris) - 1)
    for x in lr["beban"]:
        baris.append([f"   {x['nama']}", x["nilai"], None])
    baris.append(["   Total Beban Operasional", None, lr["total_beban"]])
    tebal.append(len(baris) - 1)
    baris.append(["SISA HASIL USAHA (SHU)", None, lr["shu"]])
    tebal.append(len(baris) - 1)
    _tulis_tabel(ws, "LAPORAN LABA RUGI", f"Untuk bulan yang berakhir 31 {per}",
                 ["Uraian", "Jumlah", "Total"], baris, tebal, (2, 3))
    _lebar(ws, {"A": 48, "B": 18, "C": 18})

    ws = wb.create_sheet("PerubahanModal")
    baris = [[b["kode"], b["nama"], b["awal"], b["mutasi"], b["shu"], b["akhir"]]
             for b in pm["baris"]]
    t = pm["total"]
    baris.append(["", "TOTAL MODAL", t["awal"], t["mutasi"], t["shu"], t["akhir"]])
    _tulis_tabel(ws, "LAPORAN PERUBAHAN MODAL", f"Periode {per}",
                 ["Kode", "Uraian", "Saldo Awal", "Setoran/Mutasi", "SHU Periode", "Saldo Akhir"],
                 baris, [len(baris) - 1], (3, 4, 5, 6))
    _lebar(ws, {"A": 8, "B": 30, "C": 18, "D": 18, "E": 18, "F": 18})

    ws = wb.create_sheet("Neraca")
    baris, tebal = [], []
    baris.append(["AKTIVA LANCAR", None])
    tebal.append(0)
    for a in nr["aktiva_lancar"]:
        baris.append([f"   {a['nama']}", a["nilai"]])
    baris.append(["Total Aktiva Lancar", nr["total_lancar"]])
    tebal.append(len(baris) - 1)
    baris.append(["AKTIVA TETAP", None])
    tebal.append(len(baris) - 1)
    for a in nr["aktiva_tetap"]:
        baris.append([f"   {a['nama']}", a["nilai"]])
    baris.append(["Total Aktiva Tetap", nr["total_tetap"]])
    tebal.append(len(baris) - 1)
    baris.append(["TOTAL AKTIVA", nr["total_aktiva"]])
    tebal.append(len(baris) - 1)
    baris.append(["", None])
    baris.append(["KEWAJIBAN", None])
    tebal.append(len(baris) - 1)
    for a in nr["kewajiban"]:
        baris.append([f"   {a['nama']}", a["nilai"]])
    baris.append(["Total Kewajiban", nr["total_kewajiban"]])
    tebal.append(len(baris) - 1)
    baris.append(["MODAL", None])
    tebal.append(len(baris) - 1)
    for a in nr["modal"]:
        baris.append([f"   {a['nama']}", a["nilai"]])
    baris.append(["Total Modal", nr["total_modal"]])
    tebal.append(len(baris) - 1)
    baris.append(["TOTAL KEWAJIBAN & MODAL", nr["total_pasiva"]])
    tebal.append(len(baris) - 1)
    _tulis_tabel(ws, "LAPORAN POSISI KEUANGAN (NERACA)",
                 f"Per akhir {per}", ["Uraian", "Jumlah"], baris, tebal, (2,))
    _lebar(ws, {"A": 46, "B": 20})

    ws = wb.create_sheet("SaldoAwal")
    saldo = engine.saldo_awal(periode_id)
    baris = [[a["kode"], a["nama"], a["saldo_normal"], saldo.get(a["kode"], (0, 0))[0],
              saldo.get(a["kode"], (0, 0))[1]]
             for a in engine.daftar_akun(hanya_aktif=False)
             if any(saldo.get(a["kode"], (0, 0)))]
    baris.append(["", "TOTAL", "", sum(b[3] for b in baris), sum(b[4] for b in baris)])
    _tulis_tabel(ws, "SALDO AWAL", f"Per 1 {per}",
                 ["Kode", "Nama Akun", "Saldo Normal", "Debet", "Kredit"],
                 baris, [len(baris) - 1], (4, 5))
    _lebar(ws, {"A": 8, "B": 32, "C": 14, "D": 18, "E": 18})

    wb.save(path)
    return path


def ekspor_buku_besar_excel(periode_id: int, kode_akun: str, path: str) -> str:
    bb = engine.buku_besar(periode_id, kode_akun)
    p = bb["periode"]
    wb = Workbook()
    ws = wb.active
    ws.title = f"BB-{kode_akun}"
    baris = [["", "", "Saldo Awal", "", bb["saldo_awal_d"], bb["saldo_awal_k"],
              bb["saldo_awal"]]]
    for r in bb["baris"]:
        baris.append([r["no"], r["tanggal"], r["no_bukti"], r["keterangan"],
                      r["debit"], r["kredit"], r["saldo"]])
    baris.append(["", "", "", "SALDO AKHIR", bb["total_debit"], bb["total_kredit"],
                  bb["saldo_akhir"]])
    _tulis_tabel(ws, f"BUKU BESAR — {bb['akun']['kode']} {bb['akun']['nama']}",
                 f"Periode {engine.nama_periode(p['tahun'], p['bulan'])}",
                 ["No", "Tanggal", "No Bukti", "Keterangan", "Debit", "Kredit", "Saldo"],
                 baris, [0, len(baris) - 1], (5, 6, 7))
    _lebar(ws, {"A": 6, "B": 12, "C": 14, "D": 50, "E": 16, "F": 16, "G": 18})
    wb.save(path)
    return path


def nama_berkas_excel(judul: str, p: dict | None, folder: str | None = None) -> str:
    folder = folder or db.folder_keluaran()
    bagian = judul.replace(" ", "_")
    if p:
        bagian += f"_{db.NAMA_BULAN[p['bulan']]}{p['tahun']}"
    return pdfout.path_bebas(os.path.join(folder, f"{bagian}.xlsx"))
