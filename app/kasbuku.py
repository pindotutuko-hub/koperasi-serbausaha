"""Buku Kas dan Mutasi Persediaan.

Modul ini adalah lapisan "bahasa awam" di atas mesin akuntansi. Tujuannya
supaya petugas yang tidak punya dasar akuntansi cukup mencatat dua hal:

    1. Uang masuk dan uang keluar          -> buku kas
    2. Barang masuk dan barang keluar      -> mutasi persediaan

Dari dua catatan itu program menyusun sendiri jurnalnya, lalu meneruskannya
ke buku besar, neraca lajur, sampai laporan keuangan. Petugas tidak pernah
diminta menentukan debit atau kredit.

Persediaan dicatat secara PERPETUAL dengan harga pokok rata-rata bergerak:
setiap kali barang masuk, harga rata-ratanya dihitung ulang; setiap kali
barang keluar, harga pokoknya diambil dari rata-rata saat itu. Dengan begitu
petugas cukup mengisi banyaknya unit yang keluar, tanpa perlu tahu harganya.
"""
from __future__ import annotations

from datetime import datetime

from . import db, engine
from .engine import bulat

# --------------------------------------------------------------------------- #
# Buku Kas
# --------------------------------------------------------------------------- #
# Akun yang tidak masuk akal dipilih sebagai lawan transaksi kas, karena
# akan dibentuk sendiri oleh program atau tidak pernah berhadapan dengan kas.
_AKUN_TERTUTUP = {"111"}                      # kas itu sendiri
_PERAN_TERTUTUP = {"PERSEDIAAN", "HPP", "SELISIH_PERSEDIAAN", "LABA_DITAHAN"}
_KATEGORI_TERTUTUP = {"HPP"}


def akun_lawan(arah: str) -> list[dict]:
    """Daftar akun yang boleh dipilih sebagai lawan transaksi kas.

    arah: 'MASUK' atau 'KELUAR'. Daftarnya disusun dengan penjelasan
    berbahasa sehari-hari supaya petugas tahu mana yang harus dipilih.
    """
    hasil = []
    for a in engine.daftar_akun():
        if a["kode"] in _AKUN_TERTUTUP or a["peran"] in _PERAN_TERTUTUP:
            continue
        if a["kategori"] in _KATEGORI_TERTUTUP:
            continue
        if arah == "MASUK" and a["kategori"] == "Beban":
            continue                           # beban tidak menghasilkan uang masuk
        if arah == "KELUAR" and a["kategori"] == "Pendapatan":
            continue                           # pendapatan tidak mengeluarkan uang
        hasil.append(dict(a, keterangan=_penjelasan(a, arah)))
    return hasil


def _penjelasan(a: dict, arah: str) -> str:
    """Kalimat pendek yang menjelaskan kapan akun ini dipilih."""
    kode, kat = a["kode"], a["kategori"]
    if kode == "112":
        return "Tarik tunai dari bank" if arah == "MASUK" else "Setor uang ke bank"
    if kode == "113":
        return ("Pelanggan melunasi utangnya" if arah == "MASUK"
                else "Memberi pinjaman / talangan")
    if kode == "211":
        return ("Berutang ke pemasok" if arah == "MASUK"
                else "Membayar utang ke pemasok")
    if kat == "Pendapatan":
        return "Uang hasil penjualan"
    if kat == "Beban":
        return "Pengeluaran rutin kantin"
    if kat == "Modal":
        return ("Terima setoran anggota / yayasan" if arah == "MASUK"
                else "Pengembalian simpanan anggota")
    if a["subkategori"] == "Aktiva Tetap":
        return "Beli barang tahan lama" if arah == "KELUAR" else "Jual barang tahan lama"
    return ""


def simpan_kas(periode_id: int, tanggal: str, arah: str, kode_lawan: str,
               jumlah: float, keterangan: str, no_bukti: str = "",
               jurnal_id: int | None = None) -> int:
    """Mencatat satu baris buku kas, lalu membentuk jurnalnya.

    arah 'MASUK'  -> Kas bertambah  (debit Kas, kredit akun lawan)
    arah 'KELUAR' -> Kas berkurang  (debit akun lawan, kredit Kas)
    """
    jumlah = bulat(jumlah)
    if jumlah <= 0:
        raise ValueError("Jumlah uang harus lebih besar dari nol.")
    if arah not in ("MASUK", "KELUAR"):
        raise ValueError("Arah kas harus MASUK atau KELUAR.")

    kas = engine.akun_berperan("KAS")
    if not kas:
        raise ValueError("Akun Kas belum ada di daftar akun.")
    if kode_lawan == kas["kode"]:
        raise ValueError("Akun lawan tidak boleh akun Kas itu sendiri.")

    peta = engine.peta_akun()
    if kode_lawan not in peta:
        raise ValueError(f"Akun {kode_lawan} tidak dikenal.")

    if arah == "MASUK":
        detail = [dict(kode_akun=kas["kode"], keterangan=keterangan, debit=jumlah, kredit=0),
                  dict(kode_akun=kode_lawan, keterangan=keterangan, debit=0, kredit=jumlah)]
    else:
        detail = [dict(kode_akun=kode_lawan, keterangan=keterangan, debit=jumlah, kredit=0),
                  dict(kode_akun=kas["kode"], keterangan=keterangan, debit=0, kredit=jumlah)]

    return engine.simpan_jurnal(periode_id, tanggal, keterangan, detail,
                                jenis="JU", no_bukti=no_bukti,
                                jurnal_id=jurnal_id, sumber="KAS")


def daftar_kas(periode_id: int) -> dict:
    """Buku kas satu periode: saldo awal, baris masuk/keluar, dan saldo berjalan."""
    kas = engine.akun_berperan("KAS")
    if not kas:
        return dict(baris=[], saldo_awal=0.0, total_masuk=0.0,
                    total_keluar=0.0, saldo_akhir=0.0)

    ad, ak = engine.saldo_awal(periode_id).get(kas["kode"], (0.0, 0.0))
    saldo_awal = bulat(ad - ak)
    saldo = saldo_awal
    baris, masuk, keluar = [], 0.0, 0.0

    rows = db.koneksi().execute(
        "SELECT j.id AS jurnal_id, j.tanggal, j.no_bukti, j.sumber,"
        "       COALESCE(NULLIF(d.keterangan,''), j.keterangan, '') AS keterangan,"
        "       d.debit, d.kredit"
        " FROM jurnal_detail d JOIN jurnal j ON j.id = d.jurnal_id"
        " WHERE j.periode_id=? AND d.kode_akun=?"
        " ORDER BY j.tanggal, j.id, d.urut", (periode_id, kas["kode"])).fetchall()

    for n, m in enumerate(rows, start=1):
        d_, k_ = bulat(m["debit"]), bulat(m["kredit"])
        arah = "MASUK" if d_ else "KELUAR"
        nilai = d_ or k_
        saldo = bulat(saldo + d_ - k_)
        if arah == "MASUK":
            masuk = bulat(masuk + nilai)
        else:
            keluar = bulat(keluar + nilai)
        baris.append(dict(
            no=n, jurnal_id=m["jurnal_id"], tanggal=m["tanggal"],
            no_bukti=m["no_bukti"] or "", keterangan=m["keterangan"],
            arah=arah, jumlah=nilai, saldo=saldo, sumber=m["sumber"] or "",
            lawan=_lawan_kas(m["jurnal_id"], kas["kode"]),
        ))
    return dict(baris=baris, saldo_awal=saldo_awal, total_masuk=masuk,
                total_keluar=keluar, saldo_akhir=saldo)


def _lawan_kas(jurnal_id: int, kode_kas: str) -> str:
    """Nama akun lawan dalam satu transaksi kas."""
    rows = db.koneksi().execute(
        "SELECT d.kode_akun, a.nama FROM jurnal_detail d"
        " LEFT JOIN akun a ON a.kode = d.kode_akun"
        " WHERE d.jurnal_id=? AND d.kode_akun<>? ORDER BY d.urut",
        (jurnal_id, kode_kas)).fetchall()
    nama = [r["nama"] or r["kode_akun"] for r in rows]
    if not nama:
        return ""
    return nama[0] if len(nama) == 1 else f"{nama[0]} (+{len(nama) - 1} lagi)"


# --------------------------------------------------------------------------- #
# Jenis persediaan
# --------------------------------------------------------------------------- #
def daftar_jenis(hanya_aktif: bool = True) -> list[dict]:
    sql = "SELECT * FROM jenis_persediaan"
    if hanya_aktif:
        sql += " WHERE aktif=1"
    sql += " ORDER BY urut, id"
    return [dict(r) for r in db.koneksi().execute(sql)]


def jenis(jenis_id: int) -> dict | None:
    r = db.koneksi().execute(
        "SELECT * FROM jenis_persediaan WHERE id=?", (jenis_id,)).fetchone()
    return dict(r) if r else None


# --------------------------------------------------------------------------- #
# Mutasi persediaan (perpetual, rata-rata bergerak)
# --------------------------------------------------------------------------- #
def saldo_persediaan(jenis_id: int, sampai_id: int | None = None) -> tuple[float, float]:
    """Saldo (unit, rupiah) sebuah jenis persediaan.

    sampai_id: bila diisi, hanya memperhitungkan mutasi sebelum id tersebut.
    Dipakai saat menyisipkan atau mengubah mutasi di tengah urutan.
    """
    sql = ("SELECT sisa_jumlah, sisa_nilai FROM mutasi_persediaan"
           " WHERE jenis_id=?")
    par: list = [jenis_id]
    if sampai_id is not None:
        sql += " AND id < ?"
        par.append(sampai_id)
    sql += " ORDER BY tanggal DESC, id DESC LIMIT 1"
    r = db.koneksi().execute(sql, par).fetchone()
    return (bulat(r["sisa_jumlah"]), bulat(r["sisa_nilai"])) if r else (0.0, 0.0)


def harga_rata_rata(jenis_id: int) -> float:
    unit, nilai = saldo_persediaan(jenis_id)
    return bulat(nilai / unit) if unit else 0.0


def simpan_mutasi(periode_id: int, jenis_id: int, tanggal: str, arah: str,
                  jumlah: float, keterangan: str, harga: float = 0.0,
                  kode_lawan: str = "", mutasi_id: int | None = None) -> int:
    """Mencatat satu mutasi persediaan dan membentuk jurnalnya.

    arah MASUK        : barang datang. 'harga' diisi dari nota pembelian.
                        Jurnal: Persediaan (D) / Kas atau Utang (K).
    arah KELUAR       : barang terjual. Harga pokok dihitung sendiri dari
                        rata-rata bergerak, petugas cukup mengisi jumlah unit.
                        Jurnal: Harga Pokok Penjualan (D) / Persediaan (K).
    arah PENYESUAIAN  : hasil stock opname, barang rusak atau hilang.
                        'jumlah' adalah selisih unit; boleh negatif.
                        Jurnal: Selisih Persediaan (D) / Persediaan (K),
                        atau kebalikannya bila barangnya justru lebih.
    """
    if engine.periode_terkunci(periode_id):
        raise ValueError("Periode ini sudah ditutup, mutasi tidak bisa diubah.")

    j = jenis(jenis_id)
    if not j:
        raise ValueError("Jenis persediaan tidak dikenal.")
    if arah not in ("MASUK", "KELUAR", "PENYESUAIAN"):
        raise ValueError("Arah mutasi harus MASUK, KELUAR, atau PENYESUAIAN.")

    p = engine.periode(periode_id)
    if not p or not str(tanggal).startswith(f"{p['tahun']:04d}-{p['bulan']:02d}"):
        raise ValueError(
            f"Tanggal harus berada di dalam periode "
            f"{db.NAMA_BULAN[p['bulan']]} {p['tahun']}.")

    jumlah = bulat(jumlah)
    if arah in ("MASUK", "KELUAR") and jumlah <= 0:
        raise ValueError("Jumlah unit harus lebih besar dari nol.")
    if arah == "PENYESUAIAN" and jumlah == 0:
        raise ValueError("Jumlah penyesuaian tidak boleh nol.")

    # Mutasi lama dihapus lebih dulu bila ini penyuntingan
    if mutasi_id is not None:
        hapus_mutasi(mutasi_id, susun_ulang=False)

    unit_ada, nilai_ada = saldo_persediaan(jenis_id)
    rata = bulat(nilai_ada / unit_ada) if unit_ada else 0.0

    if arah == "MASUK":
        harga = bulat(harga)
        if harga <= 0:
            raise ValueError("Harga per unit harus diisi untuk barang masuk.")
        nilai = bulat(jumlah * harga)
        sisa_unit, sisa_nilai = bulat(unit_ada + jumlah), bulat(nilai_ada + nilai)
    elif arah == "KELUAR":
        if jumlah > unit_ada:
            raise ValueError(
                f"Barang keluar {jumlah:,.0f} {j['satuan']} melebihi sisa stok "
                f"{unit_ada:,.0f} {j['satuan']}. Catat dulu barang masuknya.")
        harga = rata
        nilai = bulat(jumlah * rata)
        sisa_unit, sisa_nilai = bulat(unit_ada - jumlah), bulat(nilai_ada - nilai)
    else:                                            # PENYESUAIAN
        harga = rata
        nilai = bulat(jumlah * rata)
        sisa_unit, sisa_nilai = bulat(unit_ada + jumlah), bulat(nilai_ada + nilai)
        if sisa_unit < 0:
            raise ValueError("Penyesuaian membuat stok menjadi minus.")

    jid = _jurnal_mutasi(periode_id, j, tanggal, arah, nilai, keterangan, kode_lawan)

    kon = db.koneksi()
    cur = kon.execute(
        "INSERT INTO mutasi_persediaan (periode_id,jenis_id,tanggal,arah,keterangan,"
        "jumlah,harga,nilai,sisa_jumlah,sisa_nilai,jurnal_id,dibuat)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (periode_id, jenis_id, tanggal, arah, keterangan, jumlah, harga, nilai,
         sisa_unit, sisa_nilai, jid, datetime.now().isoformat(timespec="seconds")),
    )
    kon.commit()
    hitung_ulang(jenis_id)
    db.catat_log("MUTASI PERSEDIAAN",
                 f"{arah} {j['nama']}: {jumlah:,.0f} {j['satuan']} = {nilai:,.0f}")
    return cur.lastrowid


def _jurnal_mutasi(periode_id: int, j: dict, tanggal: str, arah: str,
                   nilai: float, keterangan: str, kode_lawan: str) -> int | None:
    """Membentuk jurnal yang menyertai sebuah mutasi persediaan."""
    nilai = bulat(nilai)
    if nilai == 0:
        return None

    if arah == "MASUK":
        lawan = kode_lawan or (engine.akun_berperan("KAS") or {}).get("kode", "111")
        detail = [
            dict(kode_akun=j["kode_akun"], keterangan=keterangan, debit=nilai, kredit=0),
            dict(kode_akun=lawan, keterangan=keterangan, debit=0, kredit=nilai),
        ]
    elif arah == "KELUAR":
        detail = [
            dict(kode_akun=j["kode_hpp"], keterangan=keterangan, debit=nilai, kredit=0),
            dict(kode_akun=j["kode_akun"], keterangan=keterangan, debit=0, kredit=nilai),
        ]
    else:                                            # PENYESUAIAN
        selisih = engine.akun_berperan("SELISIH_PERSEDIAAN")
        kode_selisih = selisih["kode"] if selisih else j["kode_hpp"]
        if nilai < 0:                                # barang berkurang
            detail = [
                dict(kode_akun=kode_selisih, keterangan=keterangan,
                     debit=abs(nilai), kredit=0),
                dict(kode_akun=j["kode_akun"], keterangan=keterangan,
                     debit=0, kredit=abs(nilai)),
            ]
        else:                                        # barang bertambah
            detail = [
                dict(kode_akun=j["kode_akun"], keterangan=keterangan,
                     debit=nilai, kredit=0),
                dict(kode_akun=kode_selisih, keterangan=keterangan,
                     debit=0, kredit=nilai),
            ]

    return engine.simpan_jurnal(periode_id, tanggal, keterangan, detail,
                                jenis="JU", sumber="PERSEDIAAN")


def hitung_ulang(jenis_id: int) -> None:
    """Menghitung ulang saldo berjalan seluruh mutasi satu jenis persediaan.

    Dipanggil setelah menambah, mengubah, atau menghapus mutasi, karena
    harga rata-rata bergerak membuat setiap baris bergantung pada baris
    sebelumnya. Nilai jurnal yang menyertainya ikut disesuaikan.
    """
    kon = db.koneksi()
    j = jenis(jenis_id)
    if not j:
        return

    unit = nilai_total = 0.0
    for m in kon.execute(
            "SELECT * FROM mutasi_persediaan WHERE jenis_id=?"
            " ORDER BY tanggal, id", (jenis_id,)).fetchall():
        rata = bulat(nilai_total / unit) if unit else 0.0
        if m["arah"] == "MASUK":
            harga = bulat(m["harga"])
            nilai = bulat(m["jumlah"] * harga)
            unit = bulat(unit + m["jumlah"])
            nilai_total = bulat(nilai_total + nilai)
        elif m["arah"] == "KELUAR":
            harga = rata
            nilai = bulat(m["jumlah"] * rata)
            unit = bulat(unit - m["jumlah"])
            nilai_total = bulat(nilai_total - nilai)
        else:
            harga = rata
            nilai = bulat(m["jumlah"] * rata)
            unit = bulat(unit + m["jumlah"])
            nilai_total = bulat(nilai_total + nilai)

        if (bulat(m["harga"]) != harga or bulat(m["nilai"]) != nilai
                or bulat(m["sisa_jumlah"]) != unit or bulat(m["sisa_nilai"]) != nilai_total):
            kon.execute(
                "UPDATE mutasi_persediaan SET harga=?, nilai=?, sisa_jumlah=?, sisa_nilai=?"
                " WHERE id=?", (harga, nilai, unit, nilai_total, m["id"]))
            if m["jurnal_id"]:
                _perbarui_nilai_jurnal(m["jurnal_id"], nilai)
    kon.commit()


def _perbarui_nilai_jurnal(jurnal_id: int, nilai: float) -> None:
    """Menyesuaikan angka pada jurnal bentukan agar sama dengan mutasinya."""
    kon = db.koneksi()
    nilai = abs(bulat(nilai))
    for d in kon.execute("SELECT id, debit, kredit FROM jurnal_detail"
                         " WHERE jurnal_id=?", (jurnal_id,)).fetchall():
        if d["debit"]:
            kon.execute("UPDATE jurnal_detail SET debit=? WHERE id=?", (nilai, d["id"]))
        else:
            kon.execute("UPDATE jurnal_detail SET kredit=? WHERE id=?", (nilai, d["id"]))


def hapus_mutasi(mutasi_id: int, susun_ulang: bool = True) -> None:
    kon = db.koneksi()
    m = kon.execute("SELECT * FROM mutasi_persediaan WHERE id=?",
                    (mutasi_id,)).fetchone()
    if not m:
        return
    if engine.periode_terkunci(m["periode_id"]):
        raise ValueError("Periode ini sudah ditutup, mutasi tidak bisa dihapus.")
    if m["jurnal_id"]:
        try:
            engine.hapus_jurnal(m["jurnal_id"])
        except Exception:
            pass
    kon.execute("DELETE FROM mutasi_persediaan WHERE id=?", (mutasi_id,))
    kon.commit()
    if susun_ulang:
        hitung_ulang(m["jenis_id"])


def daftar_mutasi(periode_id: int, jenis_id: int | None = None) -> list[dict]:
    sql = ("SELECT m.*, j.nama AS nama_jenis, j.satuan FROM mutasi_persediaan m"
           " JOIN jenis_persediaan j ON j.id = m.jenis_id"
           " WHERE m.periode_id=?")
    par: list = [periode_id]
    if jenis_id:
        sql += " AND m.jenis_id=?"
        par.append(jenis_id)
    sql += " ORDER BY m.tanggal, m.id"
    return [dict(r) for r in db.koneksi().execute(sql, par)]


def kartu_persediaan(jenis_id: int, periode_id: int | None = None) -> dict:
    """Kartu persediaan satu jenis: saldo awal, mutasi, dan saldo akhir."""
    j = jenis(jenis_id)
    if not j:
        return dict(jenis=None, baris=[], awal_jumlah=0.0, awal_nilai=0.0,
                    akhir_jumlah=0.0, akhir_nilai=0.0,
                    masuk_jumlah=0.0, masuk_nilai=0.0,
                    keluar_jumlah=0.0, keluar_nilai=0.0)

    kon = db.koneksi()
    if periode_id:
        p = engine.periode(periode_id)
        awal_bulan = f"{p['tahun']:04d}-{p['bulan']:02d}-01"
        r = kon.execute(
            "SELECT sisa_jumlah, sisa_nilai FROM mutasi_persediaan"
            " WHERE jenis_id=? AND tanggal < ? ORDER BY tanggal DESC, id DESC LIMIT 1",
            (jenis_id, awal_bulan)).fetchone()
        aw_j, aw_n = (bulat(r["sisa_jumlah"]), bulat(r["sisa_nilai"])) if r else (0.0, 0.0)
        mutasi = daftar_mutasi(periode_id, jenis_id)
    else:
        aw_j = aw_n = 0.0
        mutasi = [dict(r) for r in kon.execute(
            "SELECT m.*, j.nama AS nama_jenis, j.satuan FROM mutasi_persediaan m"
            " JOIN jenis_persediaan j ON j.id=m.jenis_id"
            " WHERE m.jenis_id=? ORDER BY m.tanggal, m.id", (jenis_id,))]

    masuk_j = sum(m["jumlah"] for m in mutasi if m["arah"] == "MASUK")
    masuk_n = sum(m["nilai"] for m in mutasi if m["arah"] == "MASUK")
    keluar_j = sum(m["jumlah"] for m in mutasi if m["arah"] == "KELUAR")
    keluar_n = sum(m["nilai"] for m in mutasi if m["arah"] == "KELUAR")
    sesuai_j = sum(m["jumlah"] for m in mutasi if m["arah"] == "PENYESUAIAN")
    sesuai_n = sum(m["nilai"] for m in mutasi if m["arah"] == "PENYESUAIAN")

    ak_j = bulat(aw_j + masuk_j - keluar_j + sesuai_j)
    ak_n = bulat(aw_n + masuk_n - keluar_n + sesuai_n)

    return dict(jenis=j, baris=mutasi, awal_jumlah=bulat(aw_j), awal_nilai=bulat(aw_n),
                masuk_jumlah=bulat(masuk_j), masuk_nilai=bulat(masuk_n),
                keluar_jumlah=bulat(keluar_j), keluar_nilai=bulat(keluar_n),
                penyesuaian_jumlah=bulat(sesuai_j), penyesuaian_nilai=bulat(sesuai_n),
                akhir_jumlah=ak_j, akhir_nilai=ak_n)


def simpan_penjualan_kredit(periode_id: int, jenis_id: int, tanggal: str,
                            jumlah_unit: float, nilai_jual: float,
                            keterangan: str) -> int:
    """Penjualan yang uangnya dibayar menyusul (misalnya seragam siswa).

    Dua hal tercatat sekaligus:
      1. Piutang bertambah, pendapatan penjualan bertambah
      2. Barang keluar dari persediaan, harga pokoknya terbentuk sendiri

    Pelunasannya nanti cukup dicatat di Buku Kas sebagai uang masuk dengan
    akun lawan Piutang.
    """
    j = jenis(jenis_id)
    if not j:
        raise ValueError("Jenis persediaan tidak dikenal.")
    nilai_jual = bulat(nilai_jual)
    if nilai_jual <= 0:
        raise ValueError("Nilai penjualan harus lebih besar dari nol.")

    piutang = next((a for a in engine.daftar_akun() if a["kode"] == "113"), None)
    if not piutang:
        raise ValueError("Akun Piutang (113) belum ada di daftar akun.")

    # 1. Piutang bertambah, pendapatan diakui
    engine.simpan_jurnal(
        periode_id, tanggal, keterangan,
        [dict(kode_akun=piutang["kode"], keterangan=keterangan,
              debit=nilai_jual, kredit=0),
         dict(kode_akun=j["kode_jual"], keterangan=keterangan,
              debit=0, kredit=nilai_jual)],
        jenis="JU", sumber="PIUTANG")

    # 2. Barang keluar, harga pokok terbentuk otomatis
    return simpan_mutasi(periode_id, jenis_id, tanggal, "KELUAR",
                         jumlah_unit, keterangan)


def daftar_piutang(periode_id: int) -> dict:
    """Rincian piutang satu periode: penambahan, pelunasan, dan sisanya."""
    kode = "113"
    ad, ak = engine.saldo_awal(periode_id).get(kode, (0.0, 0.0))
    saldo = bulat(ad - ak)
    awal = saldo
    baris, tambah, lunas = [], 0.0, 0.0

    rows = db.koneksi().execute(
        "SELECT j.id AS jurnal_id, j.tanggal, j.no_bukti, j.sumber,"
        "       COALESCE(NULLIF(d.keterangan,''), j.keterangan, '') AS keterangan,"
        "       d.debit, d.kredit"
        " FROM jurnal_detail d JOIN jurnal j ON j.id = d.jurnal_id"
        " WHERE j.periode_id=? AND d.kode_akun=?"
        " ORDER BY j.tanggal, j.id, d.urut", (periode_id, kode)).fetchall()

    for n, m in enumerate(rows, start=1):
        d_, k_ = bulat(m["debit"]), bulat(m["kredit"])
        saldo = bulat(saldo + d_ - k_)
        tambah = bulat(tambah + d_)
        lunas = bulat(lunas + k_)
        baris.append(dict(
            no=n, jurnal_id=m["jurnal_id"], tanggal=m["tanggal"],
            no_bukti=m["no_bukti"] or "", keterangan=m["keterangan"],
            arah="TAMBAH" if d_ else "LUNAS", jumlah=d_ or k_, saldo=saldo,
            sumber=m["sumber"] or ""))

    return dict(baris=baris, saldo_awal=awal, total_tambah=tambah,
                total_lunas=lunas, saldo_akhir=saldo)


def rekap_persediaan(periode_id: int) -> dict:
    """Ringkasan seluruh jenis persediaan dalam satu periode."""
    kartu = [kartu_persediaan(j["id"], periode_id) for j in daftar_jenis()]
    return dict(
        kartu=kartu,
        total_awal=bulat(sum(k["awal_nilai"] for k in kartu)),
        total_masuk=bulat(sum(k["masuk_nilai"] for k in kartu)),
        total_keluar=bulat(sum(k["keluar_nilai"] for k in kartu)),
        total_akhir=bulat(sum(k["akhir_nilai"] for k in kartu)),
    )
