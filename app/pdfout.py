"""Pembuatan laporan PDF (satu klik) memakai ReportLab."""
from __future__ import annotations

import os
from datetime import date, datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from . import db, engine

BIRU = colors.HexColor("#1F4E79")
BIRU_MUDA = colors.HexColor("#DCE6F1")
ABU = colors.HexColor("#F2F2F2")
GARIS = colors.HexColor("#9DB2C6")

gaya = getSampleStyleSheet()
S_JUDUL = ParagraphStyle("judul", parent=gaya["Normal"], fontName="Helvetica-Bold",
                         fontSize=13, alignment=TA_CENTER, spaceAfter=1, textColor=BIRU)
S_SUB = ParagraphStyle("sub", parent=gaya["Normal"], fontName="Helvetica-Bold",
                       fontSize=10.5, alignment=TA_CENTER, spaceAfter=1)
S_PERIODE = ParagraphStyle("per", parent=gaya["Normal"], fontSize=9.5, alignment=TA_CENTER)
S_SEL = ParagraphStyle("sel", parent=gaya["Normal"], fontSize=8.5, leading=10.5)
S_CATATAN = ParagraphStyle("cat", parent=gaya["Normal"], fontSize=7.5, leading=10,
                           textColor=colors.HexColor("#555555"))


# --------------------------------------------------------------------------- #
# Pembantu format
# --------------------------------------------------------------------------- #
def rp(nilai, nol: str = "-") -> str:
    """Format angka rupiah gaya Indonesia: 1.234.567 ; negatif dalam kurung."""
    n = round(float(nilai or 0))
    if n == 0:
        return nol
    teks = f"{abs(n):,}".replace(",", ".")
    return f"({teks})" if n < 0 else teks


def tgl_id(nilai) -> str:
    if not nilai:
        return ""
    if isinstance(nilai, str):
        try:
            nilai = datetime.strptime(nilai[:10], "%Y-%m-%d").date()
        except ValueError:
            return nilai
    return f"{nilai.day:02d}/{nilai.month:02d}/{nilai.year}"


def tgl_panjang(nilai: date) -> str:
    return f"{nilai.day} {db.NAMA_BULAN[nilai.month]} {nilai.year}"


def _bisa_ditulis(path: str) -> bool:
    """Cek apakah berkas bisa ditimpa. False bila sedang dibuka aplikasi lain."""
    if not os.path.exists(path):
        return True
    try:
        with open(path, "ab"):
            return True
    except OSError:
        return False


def path_bebas(path: str) -> str:
    """Kembalikan path yang aman ditulis.

    Bila berkas sedang terkunci (mis. PDF-nya masih terbuka di layar),
    dicarikan nama lain: '... (2).pdf', '... (3).pdf', dan seterusnya.
    Dengan begitu proses cetak tidak pernah gagal hanya karena berkas
    hasil cetak sebelumnya lupa ditutup.
    """
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    if _bisa_ditulis(path):
        return path
    dasar, ext = os.path.splitext(path)
    for i in range(2, 100):
        kandidat = f"{dasar} ({i}){ext}"
        if _bisa_ditulis(kandidat):
            return kandidat
    return f"{dasar}_{datetime.now():%H%M%S}{ext}"


def nama_berkas(judul: str, p: dict | None, folder: str | None = None) -> str:
    folder = folder or db.folder_keluaran()
    bagian = judul.replace("/", "-").replace(" ", "_")
    if p:
        bagian += f"_{db.NAMA_BULAN[p['bulan']]}{p['tahun']}"
    return path_bebas(os.path.join(folder, f"{bagian}.pdf"))


# --------------------------------------------------------------------------- #
# Kerangka dokumen
# --------------------------------------------------------------------------- #
def _kop(judul: str, sub_periode: str, lebar: float) -> list:
    return [
        Paragraph(db.ambil_pengaturan("nama_koperasi"), S_SUB),
        Paragraph(db.ambil_pengaturan("unit_usaha"), S_PERIODE),
        Spacer(1, 3),
        Table([[""]], colWidths=[lebar], rowHeights=[1],
              style=TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1.1, BIRU)])),
        Spacer(1, 6),
        Paragraph(judul, S_JUDUL),
        Paragraph(sub_periode, S_PERIODE),
        Spacer(1, 8),
    ]


def _kaki(canvas, dokumen):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#666666"))
    lebar, tinggi = dokumen.pagesize
    canvas.line(15 * mm, 12 * mm, lebar - 15 * mm, 12 * mm)
    canvas.drawString(15 * mm, 8 * mm,
                      f"Dicetak {datetime.now().strftime('%d/%m/%Y %H:%M')} — "
                      f"Program Pembukuan Kantin Koperasi v{db.VERSI_APLIKASI}")
    canvas.drawRightString(lebar - 15 * mm, 8 * mm, f"Halaman {dokumen.page}")
    canvas.restoreState()


def _dokumen(path: str, judul: str, mendatar: bool = False) -> tuple:
    ukuran = landscape(A4) if mendatar else A4
    dok = SimpleDocTemplate(
        path, pagesize=ukuran, title=judul,
        author=db.ambil_pengaturan("nama_koperasi"),
        leftMargin=12 * mm if mendatar else 15 * mm,
        rightMargin=12 * mm if mendatar else 15 * mm,
        topMargin=9 * mm if mendatar else 13 * mm,
        bottomMargin=14 * mm if mendatar else 16 * mm)
    return dok, dok.width


def _tabel(data, lebar_kolom, rata=None, header=True, total_baris=None,
           padat: bool = False) -> Table:
    t = Table(data, colWidths=lebar_kolom, repeatRows=2 if padat else (1 if header else 0))
    gy = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7 if padat else 8),
        ("LEADING", (0, 0), (-1, -1), 8.5 if padat else 10),
        ("TOPPADDING", (0, 0), (-1, -1), 1.2 if padat else 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.2 if padat else 3),
        ("GRID", (0, 0), (-1, -1), 0.4, GARIS),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if header:
        gy += [("BACKGROUND", (0, 0), (-1, 0), BIRU),
               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
               ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
               ("ALIGN", (0, 0), (-1, 0), "CENTER")]
    for kolom, ratanya in (rata or {}).items():
        gy.append(("ALIGN", (kolom, 1 if header else 0), (kolom, -1), ratanya))
    for baris in (total_baris or []):
        gy += [("BACKGROUND", (0, baris), (-1, baris), BIRU_MUDA),
               ("FONTNAME", (0, baris), (-1, baris), "Helvetica-Bold")]
    t.setStyle(TableStyle(gy))
    return t


def _tanda_tangan(lebar: float, tanggal_teks: str) -> Table:
    kota = db.ambil_pengaturan("kota") or ""
    ketua = db.ambil_pengaturan("ketua") or "Ketua"
    bendahara = db.ambil_pengaturan("bendahara") or "Bendahara"
    data = [
        ["", f"{kota}, {tanggal_teks}"],
        ["Mengetahui,", "Disusun oleh,"],
        ["Ketua Koperasi", "Bendahara / Petugas Pembukuan"],
        ["", ""], ["", ""],
        [f"({ketua})", f"({bendahara})"],
    ]
    t = Table(data, colWidths=[lebar * 0.5, lebar * 0.5])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("FONTNAME", (0, 5), (-1, 5), "Helvetica-Bold"),
        ("LINEABOVE", (0, 5), (-1, 5), 0, colors.white),
    ]))
    return t


def _periode_teks(p: dict) -> str:
    return engine.nama_periode(p["tahun"], p["bulan"])


def _akhir_bulan_teks(p: dict) -> str:
    return tgl_panjang(engine.hari_akhir_bulan(p["tahun"], p["bulan"]))


# --------------------------------------------------------------------------- #
# Laporan-laporan
# --------------------------------------------------------------------------- #
def cetak_jurnal_umum(periode_id: int, path: str | None = None) -> str:
    p = engine.periode(periode_id)
    baris = engine.jurnal_umum(periode_id)
    path = path or nama_berkas("Jurnal_Umum", p)
    dok, lebar = _dokumen(path, "Jurnal Umum")
    isi = _kop("JURNAL UMUM", f"Periode {_periode_teks(p)}", lebar)

    data = [["Tanggal", "No. Bukti", "Kode", "Nama Akun / Keterangan", "Jns", "Debit", "Kredit"]]
    td = tk = 0.0
    for r in baris:
        ket = r["keterangan"] or r["ket_induk"] or ""
        data.append([tgl_id(r["tanggal"]), r["no_bukti"] or "", r["kode_akun"],
                     Paragraph(f"<b>{r['nama_akun']}</b><br/><font size=7>{ket}</font>", S_SEL),
                     r["jenis"], rp(r["debit"]), rp(r["kredit"])])
        td += r["debit"] or 0
        tk += r["kredit"] or 0
    data.append(["", "", "", "TOTAL", "", rp(td), rp(tk)])
    lk = [lebar * x for x in (0.10, 0.14, 0.07, 0.36, 0.06, 0.135, 0.135)]
    isi.append(_tabel(data, lk, rata={0: "CENTER", 2: "CENTER", 4: "CENTER",
                                      5: "RIGHT", 6: "RIGHT"},
                      total_baris=[len(data) - 1]))
    status = "SEIMBANG (balance)" if abs(td - tk) < 0.01 else "TIDAK BALANCE — periksa jurnal"
    isi += [Spacer(1, 6), Paragraph(f"Status jurnal: <b>{status}</b>. "
                                    f"Jumlah transaksi: {len(set(r['no_bukti'] for r in baris))}.",
                                    S_CATATAN)]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_buku_besar(periode_id: int, kode_akun: str, path: str | None = None) -> str:
    bb = engine.buku_besar(periode_id, kode_akun)
    p = bb["periode"]
    a = bb["akun"]
    path = path or nama_berkas(f"Buku_Besar_{kode_akun}", p)
    dok, lebar = _dokumen(path, "Buku Besar")
    isi = _kop("BUKU BESAR", f"Periode {_periode_teks(p)}", lebar)

    info = [["Kode Akun", a["kode"], "Kategori", a["kategori"]],
            ["Nama Akun", a["nama"], "Saldo Normal", a["saldo_normal"]]]
    t = Table(info, colWidths=[lebar * 0.14, lebar * 0.41, lebar * 0.16, lebar * 0.29])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5), ("GRID", (0, 0), (-1, -1), 0.4, GARIS),
        ("BACKGROUND", (0, 0), (0, -1), ABU), ("BACKGROUND", (2, 0), (2, -1), ABU),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    isi += [t, Spacer(1, 8)]

    data = [["No", "Tanggal", "No. Bukti", "Keterangan", "Jns", "Debit", "Kredit", "Saldo"]]
    data.append(["", tgl_id(f"{p['tahun']}-{p['bulan']:02d}-01"), "", "Saldo Awal", "",
                 rp(bb["saldo_awal_d"]), rp(bb["saldo_awal_k"]), rp(bb["saldo_awal"])])
    for r in bb["baris"]:
        data.append([r["no"], tgl_id(r["tanggal"]), r["no_bukti"],
                     Paragraph(r["keterangan"], S_SEL), r["jenis"],
                     rp(r["debit"]), rp(r["kredit"]), rp(r["saldo"])])
    data.append(["", "", "", "SALDO AKHIR", "", rp(bb["total_debit"]),
                 rp(bb["total_kredit"]), rp(bb["saldo_akhir"])])
    lk = [lebar * x for x in (0.05, 0.09, 0.12, 0.31, 0.05, 0.125, 0.125, 0.13)]
    isi.append(_tabel(data, lk, rata={0: "CENTER", 1: "CENTER", 4: "CENTER",
                                      5: "RIGHT", 6: "RIGHT", 7: "RIGHT"},
                      total_baris=[1, len(data) - 1]))
    isi += [Spacer(1, 6),
            Paragraph(f"Mutasi JU: debit {rp(bb['mutasi_ju'][0])} / kredit {rp(bb['mutasi_ju'][1])} • "
                      f"Mutasi AJP: debit {rp(bb['mutasi_ajp'][0])} / kredit {rp(bb['mutasi_ajp'][1])}. "
                      f"Saldo akhir disajikan pada sisi normal akun ({a['saldo_normal']}).", S_CATATAN)]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_rekap_buku_besar(periode_id: int, path: str | None = None) -> str:
    rek = engine.rekap_buku_besar(periode_id)
    p = rek["periode"]
    path = path or nama_berkas("Rekap_Buku_Besar", p)
    dok, lebar = _dokumen(path, "Rekapitulasi Buku Besar", mendatar=True)
    isi = _kop("REKAPITULASI BUKU BESAR (NERACA SALDO)",
               f"Periode {_periode_teks(p)}", lebar)
    data = [["Kode", "Nama Akun", "Saldo Awal D", "Saldo Awal K", "Mutasi Debit",
             "Mutasi Kredit", "Saldo Akhir D", "Saldo Akhir K"]]
    for r in rek["baris"]:
        data.append([r["kode"], r["nama"], rp(r["awal_d"]), rp(r["awal_k"]),
                     rp(r["mut_d"]), rp(r["mut_k"]), rp(r["akhir_d"]), rp(r["akhir_k"])])
    t = rek["total"]
    data.append(["", "TOTAL", rp(t["awal_d"]), rp(t["awal_k"]), rp(t["mut_d"]),
                 rp(t["mut_k"]), rp(t["akhir_d"]), rp(t["akhir_k"])])
    lk = [lebar * x for x in (0.07, 0.29, 0.107, 0.107, 0.107, 0.107, 0.107, 0.105)]
    isi.append(_tabel(data, lk, rata={0: "CENTER", **{i: "RIGHT" for i in range(2, 8)}},
                      total_baris=[len(data) - 1]))
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_neraca_lajur(periode_id: int, path: str | None = None) -> str:
    nl = engine.neraca_lajur(periode_id)
    p = nl["periode"]
    path = path or nama_berkas("Neraca_Lajur", p)
    dok, lebar = _dokumen(path, "Neraca Lajur", mendatar=True)
    isi = _kop("NERACA LAJUR (WORKSHEET)", f"Periode {_periode_teks(p)}", lebar)

    data = [["Kode", "Nama Akun", "Neraca Saldo", "", "Penyesuaian", "",
             "NS Disesuaikan", "", "Laba / Rugi", "", "Neraca", ""],
            ["", "", "Debet", "Kredit", "Debet", "Kredit", "Debet", "Kredit",
             "Debet", "Kredit", "Debet", "Kredit"]]
    for r in nl["baris"]:
        data.append([r["kode"], r["nama"], rp(r["ns_d"]), rp(r["ns_k"]), rp(r["adj_d"]),
                     rp(r["adj_k"]), rp(r["nsd_d"]), rp(r["nsd_k"]), rp(r["lr_d"]),
                     rp(r["lr_k"]), rp(r["nrc_d"]), rp(r["nrc_k"])])
    t = nl["total"]
    data.append(["", "TOTAL", rp(t["ns_d"]), rp(t["ns_k"]), rp(t["adj_d"]), rp(t["adj_k"]),
                 rp(t["nsd_d"]), rp(t["nsd_k"]), rp(t["lr_d"]), rp(t["lr_k"]),
                 rp(t["nrc_d"]), rp(t["nrc_k"])])
    label = "SHU (Laba)" if nl["shu"] >= 0 else "Rugi"
    data.append(["", label, "", "", "", "", "", "",
                 rp(nl["shu"] if nl["shu"] > 0 else 0), rp(-nl["shu"] if nl["shu"] < 0 else 0),
                 rp(-nl["shu"] if nl["shu"] < 0 else 0), rp(nl["shu"] if nl["shu"] > 0 else 0)])
    seimbang_lr = t["lr_d"] + max(nl["shu"], 0)
    data.append(["", "JUMLAH", "", "", "", "", "", "",
                 rp(seimbang_lr), rp(seimbang_lr),
                 rp(t["nrc_d"] + max(-nl["shu"], 0)), rp(t["nrc_d"] + max(-nl["shu"], 0))])

    lk = [lebar * 0.05, lebar * 0.19] + [lebar * 0.076] * 10
    t_obj = _tabel(data, lk, rata={0: "CENTER", **{i: "RIGHT" for i in range(2, 12)}},
                   total_baris=[len(data) - 3, len(data) - 1], padat=True)
    t_obj.setStyle(TableStyle([
        ("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (1, 1)),
        ("SPAN", (2, 0), (3, 0)), ("SPAN", (4, 0), (5, 0)), ("SPAN", (6, 0), (7, 0)),
        ("SPAN", (8, 0), (9, 0)), ("SPAN", (10, 0), (11, 0)),
        ("BACKGROUND", (0, 1), (-1, 1), BIRU),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("FONTNAME", (0, len(data) - 2), (-1, len(data) - 2), "Helvetica-Bold"),
    ]))
    isi.append(t_obj)
    catatan = (f"Persediaan awal {rp(nl['persediaan_awal'])} • persediaan akhir "
               f"{rp(nl['persediaan_akhir'])} "
               f"({'hasil stock opname' if nl['opname_diisi'] else 'belum diisi — dianggap sama dengan saldo awal'}). "
               "Metode persediaan fisik/periodik: persediaan awal masuk kolom Laba/Rugi, "
               "persediaan akhir tampil di kolom Posisi Keuangan.")
    isi += [Spacer(1, 6), Paragraph(catatan, S_CATATAN)]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_laba_rugi(periode_id: int, path: str | None = None) -> str:
    lr = engine.laba_rugi(periode_id)
    p = lr["periode"]
    path = path or nama_berkas("Laporan_Laba_Rugi", p)
    dok, lebar = _dokumen(path, "Laporan Laba Rugi")
    isi = _kop("LAPORAN LABA RUGI (PERHITUNGAN HASIL USAHA)",
               f"Untuk bulan yang berakhir {_akhir_bulan_teks(p)}", lebar)

    data = [["Uraian", "Jumlah", "Total"]]
    idx_tebal, idx_judul = [], []

    def tambah(label, nilai=None, total=None, judul=False, tebal=False):
        data.append([label, rp(nilai) if nilai is not None else "",
                     rp(total) if total is not None else ""])
        if judul:
            idx_judul.append(len(data) - 1)
        if tebal:
            idx_tebal.append(len(data) - 1)

    tambah("PENDAPATAN USAHA", judul=True)
    for x in lr["pendapatan"]:
        tambah(f"   {x['nama']}", x["nilai"])
    for x in lr["potongan_penjualan"]:
        tambah(f"   ({x['nama']})", -x["nilai"])
    tambah("   Total Pendapatan Bersih", None, lr["total_pendapatan"], tebal=True)
    tambah("HARGA POKOK PENJUALAN", judul=True)
    if lr.get("metode") == "PERPETUAL":
        # Perpetual: harga pokok sudah terbentuk sendiri setiap barang keluar,
        # jadi cukup dirinci per jenis barang.
        for x in lr.get("rincian_hpp", []):
            tambah(f"   {x['nama']}", x["nilai"])
        if not lr.get("rincian_hpp"):
            tambah("   Belum ada barang keluar pada periode ini", 0)
    else:
        tambah("   Persediaan Barang Dagang (Awal)", lr["persediaan_awal"])
        tambah("   Pembelian Barang Dagang", lr["pembelian"])
        tambah("   Beban Angkut Pembelian", lr["angkut"])
        if lr["hpp_lain"]:
            tambah("   Biaya Pokok Lainnya", lr["hpp_lain"])
        tambah("   (Retur Pembelian)", -lr["retur_beli"])
        tambah("   (Potongan Pembelian)", -lr["potongan_beli"])
        tambah("   Barang Tersedia Dijual", None, lr["barang_tersedia"])
        tambah("   (Persediaan Barang Dagang Akhir)", -lr["persediaan_akhir"])
    tambah("   Total Harga Pokok Penjualan", None, lr["hpp"], tebal=True)
    tambah("LABA KOTOR", None, lr["laba_kotor"], tebal=True)
    tambah("BEBAN OPERASIONAL", judul=True)
    for x in lr["beban"]:
        tambah(f"   {x['nama']}", x["nilai"])
    tambah("   Total Beban Operasional", None, lr["total_beban"], tebal=True)
    label_shu = "SISA HASIL USAHA (SHU) / LABA BERSIH" if lr["shu"] >= 0 else "RUGI BERSIH"
    tambah(label_shu, None, lr["shu"], tebal=True)

    lk = [lebar * 0.56, lebar * 0.22, lebar * 0.22]
    t = _tabel(data, lk, rata={1: "RIGHT", 2: "RIGHT"})
    gy = [("BACKGROUND", (0, i), (-1, i), ABU) for i in idx_judul]
    gy += [("FONTNAME", (0, i), (-1, i), "Helvetica-Bold") for i in idx_judul + idx_tebal]
    gy += [("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), BIRU_MUDA),
           ("FONTSIZE", (0, len(data) - 1), (-1, len(data) - 1), 9)]
    t.setStyle(TableStyle(gy))
    isi.append(t)
    if lr.get("metode") == "PERPETUAL":
        isi += [Spacer(1, 6),
                Paragraph("Persediaan dicatat secara perpetual. Harga pokok penjualan di atas "
                          "terbentuk sendiri setiap barang keluar, dihitung dengan metode "
                          "rata-rata bergerak; rinciannya dapat dilihat pada Kartu Persediaan.",
                          S_CATATAN)]
    elif not lr["opname_diisi"]:
        isi += [Spacer(1, 6),
                Paragraph("Catatan: persediaan akhir belum diisi (stock opname), sehingga HPP "
                          "belum memperhitungkan barang terjual. Isi di menu Neraca Lajur / "
                          "Tutup Buku agar laba lebih akurat.", S_CATATAN)]
    isi += [Spacer(1, 16), _tanda_tangan(lebar, _akhir_bulan_teks(p))]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_perubahan_modal(periode_id: int, path: str | None = None) -> str:
    pm = engine.perubahan_modal(periode_id)
    p = pm["periode"]
    path = path or nama_berkas("Laporan_Perubahan_Modal", p)
    dok, lebar = _dokumen(path, "Laporan Perubahan Modal")
    isi = _kop("LAPORAN PERUBAHAN MODAL / EKUITAS",
               f"Untuk bulan yang berakhir {_akhir_bulan_teks(p)}", lebar)
    data = [["Kode", "Uraian", "Saldo Awal", "Setoran / Mutasi", "SHU Periode Ini", "Saldo Akhir"]]
    for b in pm["baris"]:
        data.append([b["kode"], b["nama"], rp(b["awal"]), rp(b["mutasi"]),
                     rp(b["shu"]), rp(b["akhir"])])
    t = pm["total"]
    data.append(["", "TOTAL MODAL", rp(t["awal"]), rp(t["mutasi"]), rp(t["shu"]), rp(t["akhir"])])
    lk = [lebar * x for x in (0.08, 0.32, 0.15, 0.15, 0.15, 0.15)]
    isi.append(_tabel(data, lk, rata={0: "CENTER", 2: "RIGHT", 3: "RIGHT", 4: "RIGHT",
                                      5: "RIGHT"}, total_baris=[len(data) - 1]))
    isi += [Spacer(1, 6),
            Paragraph("SHU periode berjalan otomatis menambah akun Laba Ditahan — tidak perlu "
                      "jurnal penutup manual. Saldo akhir kolom terakhir menjadi saldo awal "
                      "modal bulan berikutnya setelah proses tutup buku.", S_CATATAN),
            Spacer(1, 16), _tanda_tangan(lebar, _akhir_bulan_teks(p))]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_neraca(periode_id: int, path: str | None = None) -> str:
    n = engine.neraca(periode_id)
    p = n["periode"]
    path = path or nama_berkas("Laporan_Posisi_Keuangan", p)
    dok, lebar = _dokumen(path, "Laporan Posisi Keuangan")
    isi = _kop("LAPORAN POSISI KEUANGAN", f"Per {_akhir_bulan_teks(p)}", lebar)

    kiri = [("AKTIVA", None, "judul"), ("Aktiva Lancar", None, "sub")]
    for a in n["aktiva_lancar"]:
        kiri.append((f"   {a['nama']}", a["nilai"], ""))
    kiri.append(("   Total Aktiva Lancar", n["total_lancar"], "total"))
    kiri.append(("Aktiva Tetap", None, "sub"))
    for a in n["aktiva_tetap"]:
        nama = f"   ({a['nama']})" if a["kontra"] else f"   {a['nama']}"
        kiri.append((nama, a["nilai"], ""))
    kiri.append(("   Total Aktiva Tetap", n["total_tetap"], "total"))
    kiri.append(("TOTAL AKTIVA", n["total_aktiva"], "besar"))

    kanan = [("KEWAJIBAN DAN MODAL", None, "judul"), ("Kewajiban", None, "sub")]
    for a in n["kewajiban"]:
        kanan.append((f"   {a['nama']}", a["nilai"], ""))
    kanan.append(("   Total Kewajiban", n["total_kewajiban"], "total"))
    kanan.append(("Modal / Ekuitas", None, "sub"))
    for a in n["modal"]:
        kanan.append((f"   {a['nama']}", a["nilai"], ""))
    kanan.append(("   Total Modal", n["total_modal"], "total"))
    kanan.append(("TOTAL KEWAJIBAN & MODAL", n["total_pasiva"], "besar"))

    while len(kiri) < len(kanan):
        kiri.append(("", None, ""))
    while len(kanan) < len(kiri):
        kanan.append(("", None, ""))

    data, gaya_extra = [], []
    for i, ((lk_, lv, lt), (rk_, rv, rt)) in enumerate(zip(kiri, kanan)):
        data.append([lk_, rp(lv) if lv is not None else "",
                     rk_, rp(rv) if rv is not None else ""])
        for kol, tipe in ((0, lt), (2, rt)):
            if tipe in ("judul", "besar"):
                gaya_extra += [("BACKGROUND", (kol, i), (kol + 1, i),
                                BIRU if tipe == "judul" else BIRU_MUDA),
                               ("FONTNAME", (kol, i), (kol + 1, i), "Helvetica-Bold")]
                if tipe == "judul":
                    gaya_extra.append(("TEXTCOLOR", (kol, i), (kol + 1, i), colors.white))
            elif tipe in ("sub", "total"):
                gaya_extra.append(("FONTNAME", (kol, i), (kol + 1, i), "Helvetica-Bold"))
                if tipe == "total":
                    gaya_extra.append(("LINEABOVE", (kol, i), (kol + 1, i), 0.6, BIRU))

    lk = [lebar * 0.29, lebar * 0.21, lebar * 0.29, lebar * 0.21]
    t = Table(data, colWidths=lk)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("ALIGN", (3, 0), (3, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBEFORE", (2, 0), (2, -1), 0.6, GARIS),
        ("BOX", (0, 0), (-1, -1), 0.6, GARIS),
    ] + gaya_extra))
    isi.append(t)
    status = ("BALANCE — Total Aktiva = Total Kewajiban & Modal" if n["seimbang"]
              else f"TIDAK BALANCE — selisih {rp(n['total_aktiva'] - n['total_pasiva'])}")
    isi += [Spacer(1, 8), Paragraph(f"<b>{status}</b>", S_CATATAN),
            Spacer(1, 16), _tanda_tangan(lebar, _akhir_bulan_teks(p))]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_arus_kas(periode_id: int, path: str | None = None) -> str:
    ak = engine.arus_kas(periode_id)
    p = ak["periode"]
    path = path or nama_berkas("Laporan_Arus_Kas", p)
    dok, lebar = _dokumen(path, "Laporan Arus Kas")
    isi = _kop("LAPORAN ARUS KAS (METODE LANGSUNG - SEDERHANA)",
               f"Untuk bulan yang berakhir {_akhir_bulan_teks(p)}", lebar)
    data = [["Uraian", "Jumlah", "Total"]]
    tebal = []
    data.append(["Saldo Kas & Bank Awal Periode", "", rp(ak["awal"])])
    tebal.append(len(data) - 1)
    data.append(["PENERIMAAN", "", ""])
    judul = [len(data) - 1]
    for nama, nilai in ak["masuk"]:
        data.append([f"   {nama}", rp(nilai), ""])
    data.append(["   Total Penerimaan", "", rp(ak["total_masuk"])])
    tebal.append(len(data) - 1)
    data.append(["PENGELUARAN", "", ""])
    judul.append(len(data) - 1)
    for nama, nilai in ak["keluar"]:
        data.append([f"   {nama}", rp(nilai), ""])
    data.append(["   Total Pengeluaran", "", rp(ak["total_keluar"])])
    tebal.append(len(data) - 1)
    data.append(["SALDO KAS & BANK AKHIR PERIODE", "", rp(ak["akhir"])])
    tebal.append(len(data) - 1)

    lk = [lebar * 0.56, lebar * 0.22, lebar * 0.22]
    t = _tabel(data, lk, rata={1: "RIGHT", 2: "RIGHT"})
    t.setStyle(TableStyle(
        [("BACKGROUND", (0, i), (-1, i), ABU) for i in judul] +
        [("FONTNAME", (0, i), (-1, i), "Helvetica-Bold") for i in judul + tebal] +
        [("BACKGROUND", (0, len(data) - 1), (-1, len(data) - 1), BIRU_MUDA)]))
    isi += [t, Spacer(1, 6),
            Paragraph("Disusun dari mutasi akun berperan KAS dan BANK; lawan akun tiap "
                      "transaksi menjadi uraian penerimaan/pengeluaran.", S_CATATAN),
            Spacer(1, 14), _tanda_tangan(lebar, _akhir_bulan_teks(p))]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_rekap_penjualan(periode_id: int, path: str | None = None) -> str:
    rk = engine.rekap_penjualan_harian(periode_id)
    p = rk["periode"]
    path = path or nama_berkas("Rekap_Penjualan_Harian", p)
    dok, lebar = _dokumen(path, "Rekap Penjualan Harian")
    isi = _kop("REKAPITULASI PENJUALAN HARIAN", f"Periode {_periode_teks(p)}", lebar)
    data = [["No", "Tanggal", "Penjualan"]]
    for i, b in enumerate(rk["baris"], start=1):
        data.append([i, tgl_id(b["tanggal"]), rp(b["nilai"])])
    data.append(["", "TOTAL", rp(rk["total"])])
    lk = [lebar * 0.12, lebar * 0.48, lebar * 0.40]
    isi.append(_tabel(data, lk, rata={0: "CENTER", 1: "CENTER", 2: "RIGHT"},
                      total_baris=[len(data) - 1]))
    isi += [Spacer(1, 6),
            Paragraph(f"Jumlah hari transaksi: {rk['hari']} • Rata-rata per hari: "
                      f"{rp(rk['rata'])}", S_CATATAN)]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_daftar_akun(path: str | None = None) -> str:
    akun = engine.daftar_akun(hanya_aktif=False)
    path = path or nama_berkas("Daftar_Akun_COA", None)
    dok, lebar = _dokumen(path, "Daftar Akun")
    isi = _kop("DAFTAR AKUN (CHART OF ACCOUNT)",
               f"Per {tgl_panjang(date.today())}", lebar)
    data = [["Kode", "Nama Akun", "Kategori", "Kelompok", "Saldo Normal", "Peran", "Status"]]
    for a in akun:
        data.append([a["kode"], a["nama"], a["kategori"], a["subkategori"],
                     a["saldo_normal"], a["peran"] or "-",
                     "Aktif" if a["aktif"] else "Nonaktif"])
    lk = [lebar * x for x in (0.08, 0.30, 0.13, 0.15, 0.11, 0.14, 0.09)]
    isi.append(_tabel(data, lk, rata={0: "CENTER", 4: "CENTER", 6: "CENTER"}))
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_saldo_awal(periode_id: int, path: str | None = None) -> str:
    p = engine.periode(periode_id)
    saldo = engine.saldo_awal(periode_id)
    akun = engine.daftar_akun(hanya_aktif=False)
    path = path or nama_berkas("Saldo_Awal", p)
    dok, lebar = _dokumen(path, "Saldo Awal")
    isi = _kop("DAFTAR SALDO AWAL",
               f"Per 1 {db.NAMA_BULAN[p['bulan']]} {p['tahun']}", lebar)
    data = [["Kode", "Nama Akun", "Saldo Normal", "Debet", "Kredit"]]
    td = tk = 0.0
    for a in akun:
        d, k = saldo.get(a["kode"], (0, 0))
        if not (d or k):
            continue
        data.append([a["kode"], a["nama"], a["saldo_normal"], rp(d), rp(k)])
        td += d
        tk += k
    data.append(["", "TOTAL", "", rp(td), rp(tk)])
    lk = [lebar * x for x in (0.10, 0.40, 0.16, 0.17, 0.17)]
    isi.append(_tabel(data, lk, rata={0: "CENTER", 2: "CENTER", 3: "RIGHT", 4: "RIGHT"},
                      total_baris=[len(data) - 1]))
    selisih = td - tk
    isi += [Spacer(1, 6),
            Paragraph("Status: <b>" + ("SEIMBANG" if abs(selisih) < 0.01
                                       else f"TIDAK SEIMBANG, selisih {rp(selisih)}") + "</b>",
                      S_CATATAN)]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


# --------------------------------------------------------------------------- #
# Paket laporan lengkap (satu berkas PDF)
# --------------------------------------------------------------------------- #
def cetak_paket_lengkap(periode_id: int, path: str | None = None) -> str:
    """Menggabungkan seluruh laporan bulanan menjadi satu berkas PDF."""
    import tempfile

    from pypdf import PdfReader, PdfWriter  # type: ignore

    p = engine.periode(periode_id)
    path = path or nama_berkas("Laporan_Keuangan_Lengkap", p)
    with tempfile.TemporaryDirectory() as tmp:
        bagian = [
            cetak_jurnal_umum(periode_id, os.path.join(tmp, "1.pdf")),
            cetak_rekap_buku_besar(periode_id, os.path.join(tmp, "2.pdf")),
            cetak_neraca_lajur(periode_id, os.path.join(tmp, "3.pdf")),
            cetak_laba_rugi(periode_id, os.path.join(tmp, "4.pdf")),
            cetak_perubahan_modal(periode_id, os.path.join(tmp, "5.pdf")),
            cetak_neraca(periode_id, os.path.join(tmp, "6.pdf")),
            cetak_arus_kas(periode_id, os.path.join(tmp, "7.pdf")),
            cetak_rekap_penjualan(periode_id, os.path.join(tmp, "8.pdf")),
        ]
        penulis = PdfWriter()
        for b in bagian:
            for hal in PdfReader(b).pages:
                penulis.add_page(hal)
        try:
            with open(path, "wb") as f:
                penulis.write(f)
        except PermissionError:
            path = path_bebas(path)
            with open(path, "wb") as f:
                penulis.write(f)
    return path


# --------------------------------------------------------------------------- #
# Buku Kas dan Persediaan
# --------------------------------------------------------------------------- #
def cetak_buku_kas(periode_id: int, path: str | None = None) -> str:
    from . import kasbuku

    bk = kasbuku.daftar_kas(periode_id)
    p = engine.periode(periode_id)
    path = path or nama_berkas("Buku_Kas", p)
    dok, lebar = _dokumen(path, "Buku Kas", mendatar=True)
    isi = _kop("BUKU KAS",
               f"Periode {engine.nama_periode(p['tahun'], p['bulan'])}", lebar)

    data = [["Tanggal", "No Bukti", "Keterangan", "Untuk Apa",
             "Uang Masuk", "Uang Keluar", "Sisa Kas"]]
    data.append(["", "", "Saldo awal periode", "", "", "", rp(bk["saldo_awal"])])
    for b in bk["baris"]:
        data.append([
            tgl_id(b["tanggal"]), b["no_bukti"], b["keterangan"], b["lawan"],
            rp(b["jumlah"]) if b["arah"] == "MASUK" else "",
            rp(b["jumlah"]) if b["arah"] == "KELUAR" else "",
            rp(b["saldo"]),
        ])
    data.append(["", "", "JUMLAH", "", rp(bk["total_masuk"]),
                 rp(bk["total_keluar"]), rp(bk["saldo_akhir"])])

    lk = [lebar * x for x in (0.09, 0.09, 0.30, 0.19, 0.11, 0.11, 0.11)]
    isi.append(_tabel(data, lk,
                      rata={0: "CENTER", 1: "CENTER", 4: "RIGHT", 5: "RIGHT", 6: "RIGHT"},
                      total_baris=[len(data) - 1]))
    isi += [Spacer(1, 16), _tanda_tangan(lebar, _akhir_bulan_teks(p))]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path


def cetak_persediaan(periode_id: int, path: str | None = None) -> str:
    from . import kasbuku

    rk = kasbuku.rekap_persediaan(periode_id)
    p = engine.periode(periode_id)
    path = path or nama_berkas("Kartu_Persediaan", p)
    dok, lebar = _dokumen(path, "Kartu Persediaan", mendatar=True)
    isi = _kop("KARTU PERSEDIAAN (PERPETUAL)",
               f"Periode {engine.nama_periode(p['tahun'], p['bulan'])}", lebar)

    for k in rk["kartu"]:
        j = k["jenis"]
        isi.append(Paragraph(f"<b>{j['nama']}</b>  (satuan: {j['satuan']})", S_SUB))
        isi.append(Spacer(1, 4))

        data = [["Tanggal", "Keterangan", "Mutasi", "Unit", "Harga/Unit",
                 "Nilai", "Sisa Unit", "Sisa Nilai"]]
        data.append(["", "Saldo awal", "", f"{k['awal_jumlah']:,.0f}", "", "",
                     f"{k['awal_jumlah']:,.0f}", rp(k["awal_nilai"])])
        for m in k["baris"]:
            arah = {"MASUK": "Masuk", "KELUAR": "Keluar",
                    "PENYESUAIAN": "Penyesuaian"}[m["arah"]]
            data.append([
                tgl_id(m["tanggal"]), m["keterangan"], arah,
                f"{m['jumlah']:,.0f}", rp(m["harga"]), rp(m["nilai"]),
                f"{m['sisa_jumlah']:,.0f}", rp(m["sisa_nilai"]),
            ])
        data.append(["", "SALDO AKHIR", "", f"{k['akhir_jumlah']:,.0f}", "",
                     "", f"{k['akhir_jumlah']:,.0f}", rp(k["akhir_nilai"])])

        lk = [lebar * x for x in (0.09, 0.28, 0.10, 0.08, 0.11, 0.12, 0.09, 0.13)]
        isi.append(_tabel(data, lk,
                          rata={0: "CENTER", 2: "CENTER", 3: "RIGHT", 4: "RIGHT",
                                5: "RIGHT", 6: "RIGHT", 7: "RIGHT"},
                          total_baris=[len(data) - 1], padat=True))
        isi.append(Spacer(1, 12))

    ringkas = [["Jenis Persediaan", "Saldo Awal", "Barang Masuk",
                "Barang Keluar (Harga Pokok)", "Saldo Akhir"]]
    for k in rk["kartu"]:
        ringkas.append([k["jenis"]["nama"], rp(k["awal_nilai"]), rp(k["masuk_nilai"]),
                        rp(k["keluar_nilai"]), rp(k["akhir_nilai"])])
    ringkas.append(["TOTAL", rp(rk["total_awal"]), rp(rk["total_masuk"]),
                    rp(rk["total_keluar"]), rp(rk["total_akhir"])])
    lk = [lebar * x for x in (0.28, 0.18, 0.18, 0.18, 0.18)]
    isi.append(Paragraph("<b>Ringkasan</b>", S_SUB))
    isi.append(Spacer(1, 4))
    isi.append(_tabel(ringkas, lk, rata={1: "RIGHT", 2: "RIGHT", 3: "RIGHT", 4: "RIGHT"},
                      total_baris=[len(ringkas) - 1]))
    isi += [Spacer(1, 8),
            Paragraph("Harga pokok barang keluar dihitung dengan metode rata-rata "
                      "bergerak, dan jumlahnya menjadi Harga Pokok Penjualan pada "
                      "Laporan Laba Rugi.", S_CATATAN),
            Spacer(1, 14), _tanda_tangan(lebar, _akhir_bulan_teks(p))]
    dok.build(isi, onFirstPage=_kaki, onLaterPages=_kaki)
    return path
