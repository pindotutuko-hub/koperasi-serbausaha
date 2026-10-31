"""Mesin akuntansi: perhitungan buku besar, neraca lajur, dan laporan keuangan.

Metode persediaan: FISIK / PERIODIK.
  - Pembelian barang dagang dicatat ke akun berperan PEMBELIAN (511), bukan ke Persediaan.
  - Persediaan akhir diisi dari stock opname tiap akhir bulan (per periode).
  - HPP = Persediaan Awal + Pembelian + Angkut - Retur - Potongan - Persediaan Akhir.
"""
from __future__ import annotations

from datetime import date, datetime

from . import db

KATEGORI = ["Aset", "Kewajiban", "Modal", "Pendapatan", "HPP", "Beban"]
KATEGORI_NERACA = ("Aset", "Kewajiban", "Modal")
KATEGORI_LR = ("Pendapatan", "HPP", "Beban")
SUBKATEGORI = ["Aktiva Lancar", "Aktiva Tetap", "Kewajiban", "Modal",
               "Pendapatan", "HPP", "Beban"]
PERAN = ["", "KAS", "BANK", "PERSEDIAAN", "LABA_DITAHAN", "PEMBELIAN",
         "ANGKUT_BELI", "RETUR_BELI", "POTONGAN_BELI", "RETUR_JUAL"]
JENIS_JURNAL = ["JU", "AJP"]


def bulat(x: float) -> float:
    return round(float(x or 0), 2)


# --------------------------------------------------------------------------- #
# Periode
# --------------------------------------------------------------------------- #
def nama_periode(tahun: int, bulan: int) -> str:
    return f"{db.NAMA_BULAN[bulan]} {tahun}"


def hari_akhir_bulan(tahun: int, bulan: int) -> date:
    if bulan == 12:
        return date(tahun, 12, 31)
    return date(tahun, bulan + 1, 1).fromordinal(date(tahun, bulan + 1, 1).toordinal() - 1)


def daftar_periode() -> list[dict]:
    rows = db.koneksi().execute(
        "SELECT * FROM periode ORDER BY tahun, bulan").fetchall()
    return [dict(r) for r in rows]


def periode(periode_id: int) -> dict | None:
    r = db.koneksi().execute("SELECT * FROM periode WHERE id=?", (periode_id,)).fetchone()
    return dict(r) if r else None


def periode_berjalan() -> dict:
    """Periode AKTIF paling awal; bila tak ada, periode terakhir."""
    r = db.koneksi().execute(
        "SELECT * FROM periode WHERE status='AKTIF' ORDER BY tahun, bulan LIMIT 1").fetchone()
    if r is None:
        r = db.koneksi().execute(
            "SELECT * FROM periode ORDER BY tahun DESC, bulan DESC LIMIT 1").fetchone()
    if r is None:
        hari_ini = date.today()
        return tambah_periode(hari_ini.year, hari_ini.month)
    return dict(r)


def tambah_periode(tahun: int, bulan: int) -> dict:
    kon = db.koneksi()
    kon.execute("INSERT OR IGNORE INTO periode (tahun,bulan,status) VALUES (?,?, 'AKTIF')",
                (tahun, bulan))
    kon.commit()
    return dict(kon.execute("SELECT * FROM periode WHERE tahun=? AND bulan=?",
                            (tahun, bulan)).fetchone())


def periode_sesudah(p: dict) -> dict | None:
    th, bl = (p["tahun"] + 1, 1) if p["bulan"] == 12 else (p["tahun"], p["bulan"] + 1)
    r = db.koneksi().execute("SELECT * FROM periode WHERE tahun=? AND bulan=?", (th, bl)).fetchone()
    return dict(r) if r else None


def periode_sebelum(p: dict) -> dict | None:
    th, bl = (p["tahun"] - 1, 12) if p["bulan"] == 1 else (p["tahun"], p["bulan"] - 1)
    r = db.koneksi().execute("SELECT * FROM periode WHERE tahun=? AND bulan=?", (th, bl)).fetchone()
    return dict(r) if r else None


def periode_terkunci(periode_id: int) -> bool:
    p = periode(periode_id)
    return bool(p and p["status"] == "TUTUP")


def set_persediaan_akhir(periode_id: int, nilai: float | None) -> None:
    db.koneksi().execute("UPDATE periode SET persediaan_akhir=? WHERE id=?", (nilai, periode_id))
    db.koneksi().commit()


# --------------------------------------------------------------------------- #
# Akun
# --------------------------------------------------------------------------- #
def daftar_akun(hanya_aktif: bool = True) -> list[dict]:
    sql = "SELECT * FROM akun"
    if hanya_aktif:
        sql += " WHERE aktif=1"
    sql += " ORDER BY urut, kode"
    return [dict(r) for r in db.koneksi().execute(sql)]


def peta_akun() -> dict[str, dict]:
    return {a["kode"]: a for a in daftar_akun(hanya_aktif=False)}


def akun_berperan(peran: str) -> dict | None:
    r = db.koneksi().execute("SELECT * FROM akun WHERE peran=? AND aktif=1 LIMIT 1",
                            (peran,)).fetchone()
    return dict(r) if r else None


def simpan_akun(kode: str, nama: str, kategori: str, subkategori: str,
                saldo_normal: str, peran: str = "", aktif: int = 1,
                kode_lama: str | None = None) -> None:
    kon = db.koneksi()
    kode = str(kode).strip()
    if not kode or not nama.strip():
        raise ValueError("Kode akun dan nama akun wajib diisi.")
    if kategori not in KATEGORI:
        raise ValueError("Kategori tidak dikenal.")
    if saldo_normal not in ("Debet", "Kredit"):
        raise ValueError("Saldo normal harus Debet atau Kredit.")
    if peran:
        lain = kon.execute("SELECT kode FROM akun WHERE peran=? AND kode<>?",
                           (peran, kode_lama or kode)).fetchone()
        if lain:
            raise ValueError(f"Peran {peran} sudah dipakai akun {lain['kode']}. "
                             "Satu peran hanya boleh untuk satu akun.")
    if kode_lama and kode_lama != kode:
        if kon.execute("SELECT 1 FROM akun WHERE kode=?", (kode,)).fetchone():
            raise ValueError(f"Kode akun {kode} sudah dipakai.")
        kon.execute("UPDATE jurnal_detail SET kode_akun=? WHERE kode_akun=?", (kode, kode_lama))
        kon.execute("UPDATE saldo_awal SET kode_akun=? WHERE kode_akun=?", (kode, kode_lama))
        kon.execute("DELETE FROM akun WHERE kode=?", (kode_lama,))
    urut = kon.execute("SELECT urut FROM akun WHERE kode=?", (kode,)).fetchone()
    urut = urut["urut"] if urut else int(kode) if str(kode).isdigit() else 999
    kon.execute(
        "INSERT INTO akun (kode,nama,kategori,subkategori,saldo_normal,peran,urut,aktif)"
        " VALUES (?,?,?,?,?,?,?,?)"
        " ON CONFLICT(kode) DO UPDATE SET nama=excluded.nama, kategori=excluded.kategori,"
        " subkategori=excluded.subkategori, saldo_normal=excluded.saldo_normal,"
        " peran=excluded.peran, aktif=excluded.aktif",
        (kode, nama.strip(), kategori, subkategori, saldo_normal, peran, urut, aktif))
    kon.commit()


def hapus_akun(kode: str) -> None:
    kon = db.koneksi()
    dipakai = kon.execute("SELECT count(*) c FROM jurnal_detail WHERE kode_akun=?",
                          (kode,)).fetchone()["c"]
    if dipakai:
        raise ValueError(f"Akun {kode} sudah dipakai di {dipakai} baris jurnal. "
                         "Nonaktifkan saja akunnya agar riwayat tetap utuh.")
    kon.execute("DELETE FROM saldo_awal WHERE kode_akun=?", (kode,))
    kon.execute("DELETE FROM akun WHERE kode=?", (kode,))
    kon.commit()


# --------------------------------------------------------------------------- #
# Saldo awal & mutasi
# --------------------------------------------------------------------------- #
def saldo_awal(periode_id: int) -> dict[str, tuple[float, float]]:
    rows = db.koneksi().execute(
        "SELECT kode_akun, debit, kredit FROM saldo_awal WHERE periode_id=?", (periode_id,))
    return {r["kode_akun"]: (bulat(r["debit"]), bulat(r["kredit"])) for r in rows}


def simpan_saldo_awal(periode_id: int, data: dict[str, tuple[float, float]]) -> None:
    kon = db.koneksi()
    kon.execute("DELETE FROM saldo_awal WHERE periode_id=?", (periode_id,))
    for kode, (d, k) in data.items():
        if bulat(d) or bulat(k):
            kon.execute("INSERT INTO saldo_awal (periode_id,kode_akun,debit,kredit)"
                        " VALUES (?,?,?,?)", (periode_id, kode, bulat(d), bulat(k)))
    kon.commit()


def mutasi(periode_id: int, jenis: str | None = None) -> dict[str, tuple[float, float]]:
    sql = ("SELECT d.kode_akun, SUM(d.debit) db, SUM(d.kredit) kr"
           " FROM jurnal_detail d JOIN jurnal j ON j.id=d.jurnal_id"
           " WHERE j.periode_id=?")
    par: list = [periode_id]
    if jenis:
        sql += " AND j.jenis=?"
        par.append(jenis)
    sql += " GROUP BY d.kode_akun"
    return {r["kode_akun"]: (bulat(r["db"]), bulat(r["kr"]))
            for r in db.koneksi().execute(sql, par)}


def _sisi(nilai: float) -> tuple[float, float]:
    """Pecah nilai bersih (positif = debit) menjadi pasangan (debit, kredit)."""
    n = bulat(nilai)
    return (n, 0.0) if n >= 0 else (0.0, -n)


# --------------------------------------------------------------------------- #
# Neraca lajur (inti seluruh laporan)
# --------------------------------------------------------------------------- #
def neraca_lajur(periode_id: int) -> dict:
    p = periode(periode_id)
    akun = daftar_akun(hanya_aktif=False)
    awal = saldo_awal(periode_id)
    mut_ju = mutasi(periode_id, "JU")
    mut_ajp = mutasi(periode_id, "AJP")

    baris = []
    for a in akun:
        kode = a["kode"]
        ad, ak = awal.get(kode, (0.0, 0.0))
        jd, jk = mut_ju.get(kode, (0.0, 0.0))
        pd_, pk = mut_ajp.get(kode, (0.0, 0.0))
        if not (ad or ak or jd or jk or pd_ or pk) and not a["aktif"]:
            continue
        ns = (ad + jd) - (ak + jk)
        nsd = ns + (pd_ - pk)
        r = dict(a)
        r.update(
            awal_d=ad, awal_k=ak, mut_d=jd, mut_k=jk,
            ns_d=_sisi(ns)[0], ns_k=_sisi(ns)[1],
            adj_d=pd_, adj_k=pk,
            nsd_d=_sisi(nsd)[0], nsd_k=_sisi(nsd)[1],
            nsd=nsd, lr_d=0.0, lr_k=0.0, nrc_d=0.0, nrc_k=0.0,
        )
        baris.append(r)

    akun_persediaan = next((r for r in baris if r["peran"] == "PERSEDIAAN"), None)
    persediaan_awal = akun_persediaan["nsd"] if akun_persediaan else 0.0
    if p and p["persediaan_akhir"] is not None:
        persediaan_akhir = bulat(p["persediaan_akhir"])
    else:
        persediaan_akhir = persediaan_awal  # belum opname -> dianggap tidak berubah

    for r in baris:
        if r["kategori"] in KATEGORI_LR:
            r["lr_d"], r["lr_k"] = r["nsd_d"], r["nsd_k"]
        else:
            r["nrc_d"], r["nrc_k"] = r["nsd_d"], r["nsd_k"]
        if r["peran"] == "PERSEDIAAN":
            # metode periodik: persediaan awal masuk HPP, persediaan akhir tampil di Neraca
            r["lr_d"], r["lr_k"] = _sisi(r["nsd"])[0], _sisi(r["nsd"])[1]
            r["lr_k"] += persediaan_akhir
            r["nrc_d"], r["nrc_k"] = _sisi(persediaan_akhir)

    tot = {k: bulat(sum(r[k] for r in baris)) for k in
           ("awal_d", "awal_k", "mut_d", "mut_k", "ns_d", "ns_k", "adj_d", "adj_k",
            "nsd_d", "nsd_k", "lr_d", "lr_k", "nrc_d", "nrc_k")}
    shu = bulat(tot["lr_k"] - tot["lr_d"])
    seimbang = (abs(tot["ns_d"] - tot["ns_k"]) < 0.01
                and abs(tot["nsd_d"] - tot["nsd_k"]) < 0.01)
    return dict(periode=p, baris=baris, total=tot, shu=shu, seimbang=seimbang,
                persediaan_awal=bulat(persediaan_awal),
                persediaan_akhir=bulat(persediaan_akhir),
                opname_diisi=bool(p and p["persediaan_akhir"] is not None))


def _nilai_peran(baris: list[dict], peran: str) -> float:
    r = next((x for x in baris if x["peran"] == peran), None)
    if not r:
        return 0.0
    return bulat(r["nsd"] if r["saldo_normal"] == "Debet" else -r["nsd"])


# --------------------------------------------------------------------------- #
# Laporan Laba Rugi
# --------------------------------------------------------------------------- #
def laba_rugi(periode_id: int, nl: dict | None = None) -> dict:
    nl = nl or neraca_lajur(periode_id)
    baris = nl["baris"]

    pendapatan, potongan = [], []
    for r in baris:
        if r["kategori"] != "Pendapatan":
            continue
        nilai = bulat(-r["nsd"]) if r["saldo_normal"] == "Kredit" else bulat(r["nsd"])
        (potongan if r["saldo_normal"] == "Debet" else pendapatan).append(
            dict(kode=r["kode"], nama=r["nama"], nilai=nilai))
    total_pendapatan = bulat(sum(x["nilai"] for x in pendapatan)
                             - sum(x["nilai"] for x in potongan))

    persediaan_awal = nl["persediaan_awal"]
    persediaan_akhir = nl["persediaan_akhir"]
    pembelian = _nilai_peran(baris, "PEMBELIAN")
    angkut = _nilai_peran(baris, "ANGKUT_BELI")
    retur_beli = _nilai_peran(baris, "RETUR_BELI")
    potongan_beli = _nilai_peran(baris, "POTONGAN_BELI")
    peran_hpp = {"PEMBELIAN", "ANGKUT_BELI", "RETUR_BELI", "POTONGAN_BELI"}
    hpp_lain = bulat(sum(r["nsd"] for r in baris
                         if r["kategori"] == "HPP" and r["peran"] not in peran_hpp))

    pembelian_bersih = bulat(pembelian + angkut - retur_beli - potongan_beli + hpp_lain)
    tersedia = bulat(persediaan_awal + pembelian_bersih)
    hpp = bulat(tersedia - persediaan_akhir)
    laba_kotor = bulat(total_pendapatan - hpp)

    beban = [dict(kode=r["kode"], nama=r["nama"], nilai=bulat(r["nsd"]))
             for r in baris if r["kategori"] == "Beban"]
    total_beban = bulat(sum(x["nilai"] for x in beban))
    shu = bulat(laba_kotor - total_beban)

    return dict(periode=nl["periode"], pendapatan=pendapatan, potongan_penjualan=potongan,
                total_pendapatan=total_pendapatan, persediaan_awal=persediaan_awal,
                pembelian=pembelian, angkut=angkut, retur_beli=retur_beli,
                potongan_beli=potongan_beli, hpp_lain=hpp_lain,
                barang_tersedia=tersedia, persediaan_akhir=persediaan_akhir,
                hpp=hpp, laba_kotor=laba_kotor, beban=beban, total_beban=total_beban,
                shu=shu, opname_diisi=nl["opname_diisi"])


# --------------------------------------------------------------------------- #
# Laporan Perubahan Modal
# --------------------------------------------------------------------------- #
def perubahan_modal(periode_id: int, nl: dict | None = None) -> dict:
    nl = nl or neraca_lajur(periode_id)
    lr = laba_rugi(periode_id, nl)
    baris = []
    for r in nl["baris"]:
        if r["kategori"] != "Modal":
            continue
        awal = bulat(r["awal_k"] - r["awal_d"])
        mutasi_modal = bulat((r["mut_k"] + r["adj_k"]) - (r["mut_d"] + r["adj_d"]))
        shu = lr["shu"] if r["peran"] == "LABA_DITAHAN" else 0.0
        baris.append(dict(kode=r["kode"], nama=r["nama"], awal=awal,
                          mutasi=mutasi_modal, shu=shu,
                          akhir=bulat(awal + mutasi_modal + shu)))
    total = dict(awal=bulat(sum(b["awal"] for b in baris)),
                 mutasi=bulat(sum(b["mutasi"] for b in baris)),
                 shu=bulat(sum(b["shu"] for b in baris)),
                 akhir=bulat(sum(b["akhir"] for b in baris)))
    return dict(periode=nl["periode"], baris=baris, total=total, shu=lr["shu"])


# --------------------------------------------------------------------------- #
# Neraca
# --------------------------------------------------------------------------- #
def neraca(periode_id: int, nl: dict | None = None) -> dict:
    nl = nl or neraca_lajur(periode_id)
    lr = laba_rugi(periode_id, nl)

    lancar, tetap, kewajiban, modal = [], [], [], []
    for r in nl["baris"]:
        if r["kategori"] not in KATEGORI_NERACA:
            continue
        nilai = bulat(r["nrc_d"] - r["nrc_k"])          # positif = saldo debit
        if r["kategori"] == "Aset":
            item = dict(kode=r["kode"], nama=r["nama"], nilai=nilai,
                        kontra=(r["saldo_normal"] == "Kredit"))
            (tetap if r["subkategori"] == "Aktiva Tetap" else lancar).append(item)
        elif r["kategori"] == "Kewajiban":
            kewajiban.append(dict(kode=r["kode"], nama=r["nama"], nilai=bulat(-nilai)))
        else:
            nilai_modal = bulat(-nilai)
            if r["peran"] == "LABA_DITAHAN":
                nilai_modal = bulat(nilai_modal + lr["shu"])
            modal.append(dict(kode=r["kode"], nama=r["nama"], nilai=nilai_modal))

    total_lancar = bulat(sum(x["nilai"] for x in lancar))
    total_tetap = bulat(sum(x["nilai"] for x in tetap))
    total_aktiva = bulat(total_lancar + total_tetap)
    total_kewajiban = bulat(sum(x["nilai"] for x in kewajiban))
    total_modal = bulat(sum(x["nilai"] for x in modal))
    total_pasiva = bulat(total_kewajiban + total_modal)
    return dict(periode=nl["periode"], aktiva_lancar=lancar, aktiva_tetap=tetap,
                kewajiban=kewajiban, modal=modal, total_lancar=total_lancar,
                total_tetap=total_tetap, total_aktiva=total_aktiva,
                total_kewajiban=total_kewajiban, total_modal=total_modal,
                total_pasiva=total_pasiva, shu=lr["shu"],
                seimbang=abs(total_aktiva - total_pasiva) < 0.01)


# --------------------------------------------------------------------------- #
# Buku besar
# --------------------------------------------------------------------------- #
def buku_besar(periode_id: int, kode_akun: str) -> dict:
    a = db.koneksi().execute("SELECT * FROM akun WHERE kode=?", (kode_akun,)).fetchone()
    if a is None:
        raise ValueError(f"Akun {kode_akun} tidak ditemukan.")
    a = dict(a)
    ad, ak = saldo_awal(periode_id).get(kode_akun, (0.0, 0.0))
    normal_debit = a["saldo_normal"] == "Debet"
    saldo = bulat((ad - ak) if normal_debit else (ak - ad))

    rows = db.koneksi().execute(
        "SELECT j.tanggal, j.no_bukti, j.jenis, d.keterangan, j.keterangan AS ket_induk,"
        "       d.debit, d.kredit"
        " FROM jurnal_detail d JOIN jurnal j ON j.id=d.jurnal_id"
        " WHERE j.periode_id=? AND d.kode_akun=?"
        " ORDER BY j.tanggal, j.id, d.urut", (periode_id, kode_akun)).fetchall()

    baris, tot_d, tot_k = [], 0.0, 0.0
    ju_d = ju_k = ajp_d = ajp_k = 0.0
    for i, r in enumerate(rows, start=1):
        d, k = bulat(r["debit"]), bulat(r["kredit"])
        saldo = bulat(saldo + ((d - k) if normal_debit else (k - d)))
        tot_d += d
        tot_k += k
        if r["jenis"] == "AJP":
            ajp_d += d
            ajp_k += k
        else:
            ju_d += d
            ju_k += k
        baris.append(dict(no=i, tanggal=r["tanggal"], no_bukti=r["no_bukti"] or "",
                          jenis=r["jenis"], keterangan=r["keterangan"] or r["ket_induk"] or "",
                          debit=d, kredit=k, saldo=saldo))
    return dict(akun=a, periode=periode(periode_id),
                saldo_awal_d=ad, saldo_awal_k=ak,
                saldo_awal=bulat((ad - ak) if normal_debit else (ak - ad)),
                mutasi_ju=(bulat(ju_d), bulat(ju_k)), mutasi_ajp=(bulat(ajp_d), bulat(ajp_k)),
                total_debit=bulat(tot_d), total_kredit=bulat(tot_k),
                saldo_akhir=saldo, baris=baris)


def rekap_buku_besar(periode_id: int) -> dict:
    nl = neraca_lajur(periode_id)
    baris = []
    for r in nl["baris"]:
        awal = bulat(r["awal_d"] - r["awal_k"])
        mut_d = bulat(r["mut_d"] + r["adj_d"])
        mut_k = bulat(r["mut_k"] + r["adj_k"])
        if not (awal or mut_d or mut_k):
            continue
        akhir = bulat(r["nsd"])
        baris.append(dict(kode=r["kode"], nama=r["nama"], saldo_normal=r["saldo_normal"],
                          awal_d=_sisi(awal)[0], awal_k=_sisi(awal)[1],
                          mut_d=mut_d, mut_k=mut_k,
                          akhir_d=_sisi(akhir)[0], akhir_k=_sisi(akhir)[1]))
    total = {k: bulat(sum(b[k] for b in baris)) for k in
             ("awal_d", "awal_k", "mut_d", "mut_k", "akhir_d", "akhir_k")}
    return dict(periode=nl["periode"], baris=baris, total=total)


# --------------------------------------------------------------------------- #
# Laporan tambahan
# --------------------------------------------------------------------------- #
def arus_kas(periode_id: int) -> dict:
    """Mutasi Kas & Bank (metode langsung sederhana) beserta lawan akunnya."""
    akun = peta_akun()
    kode_kas = [k for k, a in akun.items() if a["peran"] in ("KAS", "BANK")]
    if not kode_kas:
        return dict(periode=periode(periode_id), awal=0, masuk=[], keluar=[],
                    total_masuk=0, total_keluar=0, akhir=0)
    awal_map = saldo_awal(periode_id)
    awal = bulat(sum(awal_map.get(k, (0, 0))[0] - awal_map.get(k, (0, 0))[1] for k in kode_kas))

    rows = db.koneksi().execute(
        "SELECT j.id, d.kode_akun, d.debit, d.kredit"
        " FROM jurnal_detail d JOIN jurnal j ON j.id=d.jurnal_id"
        " WHERE j.periode_id=? ORDER BY j.id, d.urut", (periode_id,)).fetchall()
    per_jurnal: dict[int, list] = {}
    for r in rows:
        per_jurnal.setdefault(r["id"], []).append(r)

    masuk: dict[str, float] = {}
    keluar: dict[str, float] = {}
    for _, detail in per_jurnal.items():
        kas_lines = [d for d in detail if d["kode_akun"] in kode_kas]
        lawan = [d for d in detail if d["kode_akun"] not in kode_kas]
        if not kas_lines:
            continue
        net_kas = bulat(sum(d["debit"] - d["kredit"] for d in kas_lines))
        if abs(net_kas) < 0.01:
            continue
        bobot_total = sum(abs(d["debit"] - d["kredit"]) for d in lawan) or 1
        sasaran = masuk if net_kas > 0 else keluar
        if not lawan:
            sasaran["Mutasi antar kas/bank"] = bulat(
                sasaran.get("Mutasi antar kas/bank", 0) + abs(net_kas))
            continue
        for d in lawan:
            bobot = abs(d["debit"] - d["kredit"]) / bobot_total
            nama = akun.get(d["kode_akun"], {}).get("nama", d["kode_akun"])
            sasaran[nama] = bulat(sasaran.get(nama, 0) + abs(net_kas) * bobot)

    total_masuk = bulat(sum(masuk.values()))
    total_keluar = bulat(sum(keluar.values()))
    return dict(periode=periode(periode_id), awal=awal,
                masuk=sorted(masuk.items(), key=lambda x: -x[1]),
                keluar=sorted(keluar.items(), key=lambda x: -x[1]),
                total_masuk=total_masuk, total_keluar=total_keluar,
                akhir=bulat(awal + total_masuk - total_keluar))


def rekap_penjualan_harian(periode_id: int) -> dict:
    rows = db.koneksi().execute(
        "SELECT j.tanggal, SUM(d.kredit - d.debit) nilai"
        " FROM jurnal_detail d JOIN jurnal j ON j.id=d.jurnal_id"
        " JOIN akun a ON a.kode=d.kode_akun"
        " WHERE j.periode_id=? AND a.kategori='Pendapatan'"
        " GROUP BY j.tanggal ORDER BY j.tanggal", (periode_id,)).fetchall()
    baris = [dict(tanggal=r["tanggal"], nilai=bulat(r["nilai"])) for r in rows]
    total = bulat(sum(b["nilai"] for b in baris))
    rata = bulat(total / len(baris)) if baris else 0.0
    return dict(periode=periode(periode_id), baris=baris, total=total, rata=rata,
                hari=len(baris))


# --------------------------------------------------------------------------- #
# Jurnal
# --------------------------------------------------------------------------- #
def daftar_jurnal(periode_id: int, cari: str = "") -> list[dict]:
    sql = ("SELECT j.*, (SELECT SUM(debit) FROM jurnal_detail WHERE jurnal_id=j.id) total"
           " FROM jurnal j WHERE j.periode_id=?")
    par: list = [periode_id]
    if cari.strip():
        sql += " AND (j.keterangan LIKE ? OR j.no_bukti LIKE ? OR j.tanggal LIKE ?)"
        par += [f"%{cari}%"] * 3
    sql += " ORDER BY j.tanggal, j.id"
    return [dict(r) for r in db.koneksi().execute(sql, par)]


def detail_jurnal(jurnal_id: int) -> list[dict]:
    return [dict(r) for r in db.koneksi().execute(
        "SELECT d.*, a.nama AS nama_akun FROM jurnal_detail d"
        " LEFT JOIN akun a ON a.kode=d.kode_akun"
        " WHERE d.jurnal_id=? ORDER BY d.urut, d.id", (jurnal_id,))]


def jurnal_umum(periode_id: int) -> list[dict]:
    return [dict(r) for r in db.koneksi().execute(
        "SELECT j.tanggal, j.no_bukti, j.jenis, j.keterangan AS ket_induk, d.kode_akun,"
        "       COALESCE(a.nama,'(akun tidak ada)') nama_akun, d.keterangan, d.debit, d.kredit"
        " FROM jurnal j JOIN jurnal_detail d ON d.jurnal_id=j.id"
        " LEFT JOIN akun a ON a.kode=d.kode_akun"
        " WHERE j.periode_id=? ORDER BY j.tanggal, j.id, d.urut", (periode_id,))]


def nomor_bukti_berikutnya(periode_id: int, jenis: str = "JU") -> str:
    p = periode(periode_id)
    awalan = f"{jenis}/{p['tahun']}{p['bulan']:02d}/"
    row = db.koneksi().execute(
        "SELECT no_bukti FROM jurnal WHERE periode_id=? AND no_bukti LIKE ?"
        " ORDER BY no_bukti DESC LIMIT 1", (periode_id, awalan + "%")).fetchone()
    urut = int(row["no_bukti"].split("/")[-1]) + 1 if row and row["no_bukti"] else 1
    return f"{awalan}{urut:03d}"


def validasi_jurnal(periode_id: int, tanggal: str, detail: list[dict]) -> list[str]:
    salah = []
    p = periode(periode_id)
    if p is None:
        return ["Periode tidak ditemukan."]
    if p["status"] == "TUTUP":
        salah.append(f"Periode {nama_periode(p['tahun'], p['bulan'])} sudah ditutup "
                     "— buka kembali dulu bila ingin mengubah.")
    try:
        tgl = datetime.strptime(tanggal, "%Y-%m-%d").date()
        if (tgl.year, tgl.month) != (p["tahun"], p["bulan"]):
            salah.append(f"Tanggal {tanggal} di luar periode "
                         f"{nama_periode(p['tahun'], p['bulan'])}.")
    except ValueError:
        salah.append("Format tanggal harus YYYY-MM-DD.")

    isi = [d for d in detail if (bulat(d.get("debit")) or bulat(d.get("kredit")))]
    if len(isi) < 2:
        salah.append("Transaksi minimal berisi 2 baris (satu debit dan satu kredit).")
    kode_ada = set(peta_akun().keys())
    for i, d in enumerate(isi, start=1):
        if d.get("kode_akun") not in kode_ada:
            salah.append(f"Baris {i}: kode akun '{d.get('kode_akun')}' tidak terdaftar.")
        if bulat(d.get("debit")) and bulat(d.get("kredit")):
            salah.append(f"Baris {i}: isi Debit ATAU Kredit, jangan keduanya.")
        if bulat(d.get("debit")) < 0 or bulat(d.get("kredit")) < 0:
            salah.append(f"Baris {i}: nilai tidak boleh negatif.")
    td = bulat(sum(bulat(d.get("debit")) for d in isi))
    tk = bulat(sum(bulat(d.get("kredit")) for d in isi))
    if abs(td - tk) >= 0.01:
        salah.append(f"Tidak balance: total debit {td:,.0f} vs total kredit {tk:,.0f} "
                     f"(selisih {abs(td - tk):,.0f}).")
    return salah


def simpan_jurnal(periode_id: int, tanggal: str, keterangan: str, detail: list[dict],
                  jenis: str = "JU", no_bukti: str = "", jurnal_id: int | None = None,
                  sumber: str = "MANUAL") -> int:
    salah = validasi_jurnal(periode_id, tanggal, detail)
    if salah:
        raise ValueError("\n".join("• " + s for s in salah))
    kon = db.koneksi()
    no_bukti = no_bukti.strip() or nomor_bukti_berikutnya(periode_id, jenis)
    if jurnal_id:
        kon.execute("UPDATE jurnal SET tanggal=?, no_bukti=?, keterangan=?, jenis=?"
                    " WHERE id=?", (tanggal, no_bukti, keterangan, jenis, jurnal_id))
        kon.execute("DELETE FROM jurnal_detail WHERE jurnal_id=?", (jurnal_id,))
    else:
        cur = kon.execute(
            "INSERT INTO jurnal (periode_id,tanggal,no_bukti,keterangan,jenis,sumber,dibuat)"
            " VALUES (?,?,?,?,?,?,?)",
            (periode_id, tanggal, no_bukti, keterangan, jenis, sumber,
             datetime.now().isoformat(timespec="seconds")))
        jurnal_id = cur.lastrowid
    urut = 0
    for d in detail:
        if not (bulat(d.get("debit")) or bulat(d.get("kredit"))):
            continue
        urut += 1
        kon.execute("INSERT INTO jurnal_detail (jurnal_id,kode_akun,keterangan,debit,kredit,urut)"
                    " VALUES (?,?,?,?,?,?)",
                    (jurnal_id, d["kode_akun"], d.get("keterangan") or keterangan,
                     bulat(d.get("debit")), bulat(d.get("kredit")), urut))
    kon.commit()
    return jurnal_id


def hapus_jurnal(jurnal_id: int) -> None:
    kon = db.koneksi()
    r = kon.execute("SELECT periode_id FROM jurnal WHERE id=?", (jurnal_id,)).fetchone()
    if r and periode_terkunci(r["periode_id"]):
        raise ValueError("Periode sudah ditutup — buka kembali dulu sebelum menghapus jurnal.")
    kon.execute("DELETE FROM jurnal_detail WHERE jurnal_id=?", (jurnal_id,))
    kon.execute("DELETE FROM jurnal WHERE id=?", (jurnal_id,))
    kon.commit()


# --------------------------------------------------------------------------- #
# Tutup buku
# --------------------------------------------------------------------------- #
def cek_siap_tutup(periode_id: int) -> list[str]:
    masalah = []
    p = periode(periode_id)
    if p is None:
        return ["Periode tidak ditemukan."]
    if p["status"] == "TUTUP":
        masalah.append("Periode ini sudah ditutup.")
    sebelum = periode_sebelum(p)
    if sebelum and sebelum["status"] == "AKTIF":
        masalah.append(f"Periode {nama_periode(sebelum['tahun'], sebelum['bulan'])} "
                       "belum ditutup. Tutup buku harus urut.")
    nl = neraca_lajur(periode_id)
    if not nl["seimbang"]:
        masalah.append("Neraca saldo belum balance — periksa jurnal.")
    n = neraca(periode_id, nl)
    if not n["seimbang"]:
        masalah.append("Neraca belum balance (Total Aktiva ≠ Total Kewajiban + Modal).")
    rows = db.koneksi().execute(
        "SELECT j.id, j.no_bukti, SUM(d.debit) td, SUM(d.kredit) tk"
        " FROM jurnal j JOIN jurnal_detail d ON d.jurnal_id=j.id"
        " WHERE j.periode_id=? GROUP BY j.id HAVING ABS(td-tk) > 0.01", (periode_id,)).fetchall()
    for r in rows:
        masalah.append(f"Jurnal {r['no_bukti']} tidak balance "
                       f"({r['td']:,.0f} vs {r['tk']:,.0f}).")
    if not akun_berperan("LABA_DITAHAN"):
        masalah.append("Belum ada akun berperan LABA_DITAHAN. Tetapkan lewat menu Akun (COA).")
    return masalah


def tutup_buku(periode_id: int, catatan: str = "") -> dict:
    masalah = cek_siap_tutup(periode_id)
    if masalah:
        raise ValueError("\n".join("• " + m for m in masalah))
    p = periode(periode_id)
    nl = neraca_lajur(periode_id)
    n = neraca(periode_id, nl)
    lr = laba_rugi(periode_id, nl)

    th, bl = (p["tahun"] + 1, 1) if p["bulan"] == 12 else (p["tahun"], p["bulan"] + 1)
    berikut = tambah_periode(th, bl)

    kon = db.koneksi()
    kon.execute("DELETE FROM saldo_awal WHERE periode_id=?", (berikut["id"],))
    ld = akun_berperan("LABA_DITAHAN")
    for r in nl["baris"]:
        if r["kategori"] not in KATEGORI_NERACA:
            continue
        nilai = bulat(r["nrc_d"] - r["nrc_k"])
        if ld and r["kode"] == ld["kode"]:
            nilai = bulat(nilai - lr["shu"])      # SHU periode ini menambah Laba Ditahan (kredit)
        if abs(nilai) < 0.01:
            continue
        d, k = _sisi(nilai)
        kon.execute("INSERT INTO saldo_awal (periode_id,kode_akun,debit,kredit)"
                    " VALUES (?,?,?,?)", (berikut["id"], r["kode"], d, k))
    kon.execute("UPDATE periode SET status='TUTUP', tanggal_tutup=?, catatan=? WHERE id=?",
                (datetime.now().isoformat(timespec="seconds"), catatan, periode_id))
    kon.commit()
    db.catat_log(
        "TUTUP BUKU",
        f"{nama_periode(p['tahun'], p['bulan'])} ditutup. SHU {lr['shu']:,.0f}; "
        f"total aktiva {n['total_aktiva']:,.0f}; saldo awal "
        f"{nama_periode(th, bl)} dibuat otomatis.")
    return dict(periode=p, berikut=periode(berikut["id"]), shu=lr["shu"],
                total_aktiva=n["total_aktiva"], persediaan_akhir=nl["persediaan_akhir"])


def batal_tutup_buku(periode_id: int) -> None:
    p = periode(periode_id)
    if p is None or p["status"] != "TUTUP":
        raise ValueError("Periode ini tidak dalam status tutup buku.")
    berikut = periode_sesudah(p)
    if berikut and berikut["status"] == "TUTUP":
        raise ValueError(
            f"Periode {nama_periode(berikut['tahun'], berikut['bulan'])} sudah ditutup. "
            "Buka kembali periode terakhir lebih dulu (urut mundur).")
    kon = db.koneksi()
    if berikut:
        kon.execute("DELETE FROM saldo_awal WHERE periode_id=?", (berikut["id"],))
        punya_jurnal = kon.execute("SELECT count(*) c FROM jurnal WHERE periode_id=?",
                                   (berikut["id"],)).fetchone()["c"]
        if not punya_jurnal:
            kon.execute("DELETE FROM periode WHERE id=?", (berikut["id"],))
    kon.execute("UPDATE periode SET status='AKTIF', tanggal_tutup=NULL WHERE id=?", (periode_id,))
    kon.commit()
    db.catat_log("BATAL TUTUP BUKU",
                 f"{nama_periode(p['tahun'], p['bulan'])} dibuka kembali; "
                 "saldo awal periode berikutnya dihapus.")


# --------------------------------------------------------------------------- #
# Ringkasan untuk beranda
# --------------------------------------------------------------------------- #
def ringkasan(periode_id: int) -> dict:
    nl = neraca_lajur(periode_id)
    lr = laba_rugi(periode_id, nl)
    n = neraca(periode_id, nl)
    kas = bulat(sum(r["nrc_d"] - r["nrc_k"] for r in nl["baris"] if r["peran"] == "KAS"))
    bank = bulat(sum(r["nrc_d"] - r["nrc_k"] for r in nl["baris"] if r["peran"] == "BANK"))
    jml = db.koneksi().execute(
        "SELECT count(*) c FROM jurnal WHERE periode_id=?", (periode_id,)).fetchone()["c"]
    return dict(periode=nl["periode"], kas=kas, bank=bank,
                pendapatan=lr["total_pendapatan"], hpp=lr["hpp"], beban=lr["total_beban"],
                shu=lr["shu"], total_aktiva=n["total_aktiva"], total_modal=n["total_modal"],
                seimbang=nl["seimbang"] and n["seimbang"], jumlah_transaksi=jml,
                opname_diisi=nl["opname_diisi"], persediaan=nl["persediaan_akhir"])
