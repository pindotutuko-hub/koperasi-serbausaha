"""Lapisan basis data (SQLite) untuk Program Pembukuan Kantin Koperasi."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime

APP_NAME = "KantinKoperasi"
VERSI_APLIKASI = "1.0.1"
VERSI_DB = 1

SKEMA = """
CREATE TABLE IF NOT EXISTS pengaturan (
    kunci TEXT PRIMARY KEY,
    nilai TEXT
);
CREATE TABLE IF NOT EXISTS akun (
    kode         TEXT PRIMARY KEY,
    nama         TEXT NOT NULL,
    kategori     TEXT NOT NULL,       -- Aset / Kewajiban / Modal / Pendapatan / HPP / Beban
    subkategori  TEXT,                -- Aktiva Lancar / Aktiva Tetap / Kewajiban / Modal / ...
    saldo_normal TEXT NOT NULL,       -- Debet / Kredit
    peran        TEXT DEFAULT '',     -- KAS / BANK / PERSEDIAAN / LABA_DITAHAN / PEMBELIAN / ...
    urut         INTEGER DEFAULT 0,
    aktif        INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS periode (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    tahun            INTEGER NOT NULL,
    bulan            INTEGER NOT NULL,
    status           TEXT DEFAULT 'AKTIF',   -- AKTIF / TUTUP
    persediaan_akhir REAL,                   -- hasil stock opname (NULL = belum opname)
    tanggal_tutup    TEXT,
    catatan          TEXT,
    UNIQUE (tahun, bulan)
);
CREATE TABLE IF NOT EXISTS saldo_awal (
    periode_id INTEGER NOT NULL,
    kode_akun  TEXT NOT NULL,
    debit      REAL DEFAULT 0,
    kredit     REAL DEFAULT 0,
    PRIMARY KEY (periode_id, kode_akun)
);
CREATE TABLE IF NOT EXISTS jurnal (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    periode_id INTEGER NOT NULL,
    tanggal    TEXT NOT NULL,
    no_bukti   TEXT,
    keterangan TEXT,
    jenis      TEXT DEFAULT 'JU',      -- JU (umum) / AJP (penyesuaian)
    sumber     TEXT DEFAULT 'MANUAL',  -- MANUAL / IMPOR / SISTEM
    dibuat     TEXT
);
CREATE TABLE IF NOT EXISTS jurnal_detail (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    jurnal_id  INTEGER NOT NULL,
    kode_akun  TEXT NOT NULL,
    keterangan TEXT,
    debit      REAL DEFAULT 0,
    kredit     REAL DEFAULT 0,
    urut       INTEGER DEFAULT 0,
    FOREIGN KEY (jurnal_id) REFERENCES jurnal (id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS log (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    waktu  TEXT,
    aksi   TEXT,
    detail TEXT
);
CREATE INDEX IF NOT EXISTS ix_jurnal_periode ON jurnal (periode_id);
CREATE INDEX IF NOT EXISTS ix_detail_jurnal  ON jurnal_detail (jurnal_id);
CREATE INDEX IF NOT EXISTS ix_detail_akun    ON jurnal_detail (kode_akun);
"""

PENGATURAN_BAWAAN = {
    # Identitas diisi sendiri oleh pengguna lewat menu Berkas > Pengaturan.
    # Nilai di bawah hanya contoh netral yang tampil sebelum diisi.
    "nama_koperasi": "KOPERASI ...",
    "unit_usaha": "UNIT USAHA KANTIN / TOKO",
    "alamat": "",
    "kota": "",
    "ketua": "Ketua Koperasi",
    "bendahara": "Bendahara",
    "versi_db": str(VERSI_DB),
}

NAMA_BULAN = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
              "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


# --------------------------------------------------------------------------- #
# Lokasi berkas
# --------------------------------------------------------------------------- #
def folder_aplikasi() -> str:
    """Folder tempat berkas aplikasi yang dijalankan berada.

    Berbeda dengan folder_program(): yang ini menunjuk ke lokasi EXE/APP di
    disk, bukan folder sementara tempat PyInstaller membongkar isinya.
    Dipakai untuk mendeteksi mode portable.
    """
    if getattr(sys, "frozen", False):
        exe = os.path.abspath(sys.executable)
        # Di macOS, .app berisi Contents/MacOS/<exe>. Naik ke folder induk .app
        # supaya folder Data berada di sebelah ikon aplikasi, bukan di dalamnya.
        bagian = exe.replace("\\", "/").split("/")
        if "Contents" in bagian and "MacOS" in bagian:
            potong = len(bagian) - 1 - bagian[::-1].index("Contents")
            induk_app = "/".join(bagian[:potong])          # .../Nama.app
            return os.path.dirname(induk_app)
        return os.path.dirname(exe)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _folder_portable() -> str | None:
    """Kembalikan folder data portable bila aplikasi dijalankan mode portable.

    Mode portable aktif bila di sebelah aplikasi terdapat:
      - folder bernama 'Data', ATAU
      - berkas penanda 'portable.txt'
    Dengan begitu seluruh data ikut berpindah bersama flashdisk, dan tidak
    ada apa pun yang ditulis ke profil pengguna di komputer tersebut.
    Bila folder itu ternyata tidak bisa ditulisi (mis. media read-only),
    mode portable dibatalkan dan program kembali memakai folder pengguna.
    """
    if os.environ.get("KANTIN_PORTABLE", "").lower() in ("0", "off", "no"):
        return None
    dasar = folder_aplikasi()
    folder = os.path.join(dasar, "Data")
    if not (os.path.isdir(folder) or os.path.exists(os.path.join(dasar, "portable.txt"))):
        return None
    try:
        os.makedirs(folder, exist_ok=True)
        uji = os.path.join(folder, ".uji_tulis")
        with open(uji, "w") as f:
            f.write("ok")
        os.remove(uji)
    except OSError:
        return None
    return folder


def mode_portable() -> bool:
    """True bila data disimpan di sebelah aplikasi (bukan di profil pengguna)."""
    return _folder_portable() is not None


def folder_data() -> str:
    """Folder penyimpanan data pengguna.

    Mode portable  : <folder aplikasi>/Data
    Mode terpasang : folder data pengguna sesuai sistem operasi
                     (tetap ada walau aplikasi di-uninstall).
    """
    folder = _folder_portable()
    if folder is None:
        if sys.platform.startswith("win"):
            basis = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        elif sys.platform == "darwin":
            basis = os.path.expanduser("~/Library/Application Support")
        else:
            basis = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        folder = os.path.join(basis, APP_NAME)
    os.makedirs(folder, exist_ok=True)
    os.makedirs(os.path.join(folder, "backup"), exist_ok=True)
    return folder


def folder_program() -> str:
    """Folder tempat berkas program/aset berada (mendukung mode PyInstaller)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def folder_keluaran() -> str:
    """Folder bawaan untuk hasil cetak PDF / ekspor Excel."""
    folder = os.path.join(folder_data(), "Laporan")
    os.makedirs(folder, exist_ok=True)
    return folder


def path_db() -> str:
    return os.path.join(folder_data(), "kantin.db")


# --------------------------------------------------------------------------- #
# Koneksi
# --------------------------------------------------------------------------- #
_koneksi: sqlite3.Connection | None = None


def koneksi() -> sqlite3.Connection:
    global _koneksi
    if _koneksi is None:
        baru = not os.path.exists(path_db())
        _koneksi = sqlite3.connect(path_db())
        _koneksi.row_factory = sqlite3.Row
        _koneksi.execute("PRAGMA foreign_keys = ON")
        _koneksi.executescript(SKEMA)
        if baru:
            isi_data_awal(_koneksi)
        lengkapi_pengaturan(_koneksi)
        _koneksi.commit()
    return _koneksi


def tutup_koneksi() -> None:
    global _koneksi
    if _koneksi is not None:
        _koneksi.commit()
        _koneksi.close()
        _koneksi = None


def catat_log(aksi: str, detail: str = "") -> None:
    koneksi().execute(
        "INSERT INTO log (waktu, aksi, detail) VALUES (?,?,?)",
        (datetime.now().isoformat(timespec="seconds"), aksi, detail),
    )
    koneksi().commit()


def lengkapi_pengaturan(kon: sqlite3.Connection) -> None:
    ada = {r["kunci"] for r in kon.execute("SELECT kunci FROM pengaturan")}
    for k, v in PENGATURAN_BAWAAN.items():
        if k not in ada:
            kon.execute("INSERT INTO pengaturan (kunci, nilai) VALUES (?,?)", (k, v))


def ambil_pengaturan(kunci: str, bawaan: str = "") -> str:
    row = koneksi().execute("SELECT nilai FROM pengaturan WHERE kunci=?", (kunci,)).fetchone()
    return row["nilai"] if row and row["nilai"] is not None else bawaan


def simpan_pengaturan(kunci: str, nilai: str) -> None:
    koneksi().execute(
        "INSERT INTO pengaturan (kunci, nilai) VALUES (?,?) "
        "ON CONFLICT(kunci) DO UPDATE SET nilai=excluded.nilai",
        (kunci, str(nilai)),
    )
    koneksi().commit()


# --------------------------------------------------------------------------- #
# Data awal (dijalankan sekali saat basis data dibuat)
# --------------------------------------------------------------------------- #
def isi_data_awal(kon: sqlite3.Connection) -> None:
    berkas = os.path.join(folder_program(), "app", "data_awal.json")
    if not os.path.exists(berkas):
        berkas = os.path.join(folder_program(), "data_awal.json")
    if not os.path.exists(berkas):
        return
    with open(berkas, encoding="utf-8") as f:
        data = json.load(f)

    for a in data.get("akun", []):
        kon.execute(
            "INSERT OR IGNORE INTO akun (kode,nama,kategori,subkategori,saldo_normal,peran,urut,aktif)"
            " VALUES (?,?,?,?,?,?,?,1)",
            (a["kode"], a["nama"], a["kategori"], a.get("subkategori") or a["kategori"],
             a["saldo_normal"], a.get("peran", ""), a.get("urut", 0)),
        )

    periode_jurnal = sorted(data.get("jurnal", {}).keys())
    periode_pertama = periode_jurnal[0] if periode_jurnal else datetime.now().strftime("%Y-%m")
    tahun, bulan = int(periode_pertama[:4]), int(periode_pertama[5:7])
    kon.execute("INSERT OR IGNORE INTO periode (tahun,bulan,status) VALUES (?,?, 'AKTIF')", (tahun, bulan))
    pid = kon.execute("SELECT id FROM periode WHERE tahun=? AND bulan=?", (tahun, bulan)).fetchone()["id"]

    for s in data.get("saldo_awal", []):
        kon.execute(
            "INSERT OR REPLACE INTO saldo_awal (periode_id,kode_akun,debit,kredit) VALUES (?,?,?,?)",
            (pid, s["kode"], s.get("debit", 0), s.get("kredit", 0)),
        )

    sekarang = datetime.now().isoformat(timespec="seconds")
    for kunci in periode_jurnal:
        th, bl = int(kunci[:4]), int(kunci[5:7])
        kon.execute("INSERT OR IGNORE INTO periode (tahun,bulan,status) VALUES (?,?, 'AKTIF')", (th, bl))
        p = kon.execute("SELECT id FROM periode WHERE tahun=? AND bulan=?", (th, bl)).fetchone()["id"]
        for n, v in enumerate(data["jurnal"][kunci], start=1):
            cur = kon.execute(
                "INSERT INTO jurnal (periode_id,tanggal,no_bukti,keterangan,jenis,sumber,dibuat)"
                " VALUES (?,?,?,?,?, 'SISTEM', ?)",
                (p, v["tanggal"], f"{kunci.replace('-', '')}-{n:03d}",
                 v.get("keterangan", ""), v.get("jenis", "JU"), sekarang),
            )
            for u, d in enumerate(v["detail"], start=1):
                kon.execute(
                    "INSERT INTO jurnal_detail (jurnal_id,kode_akun,keterangan,debit,kredit,urut)"
                    " VALUES (?,?,?,?,?,?)",
                    (cur.lastrowid, d["kode"], v.get("keterangan", ""),
                     d.get("debit", 0), d.get("kredit", 0), u),
                )
    kon.execute(
        "INSERT INTO log (waktu,aksi,detail) VALUES (?,?,?)",
        (sekarang, "BASIS DATA DIBUAT",
         "Data awal (COA, saldo awal, jurnal) dimuat dari berkas Excel koperasi."),
    )


# --------------------------------------------------------------------------- #
# Cadangan / pemulihan
# --------------------------------------------------------------------------- #
def buat_cadangan(tujuan: str | None = None) -> str:
    koneksi().commit()
    if tujuan is None:
        cap = datetime.now().strftime("%Y%m%d_%H%M%S")
        tujuan = os.path.join(folder_data(), "backup", f"kantin_{cap}.db")
    shutil.copy2(path_db(), tujuan)
    return tujuan


def pulihkan_cadangan(sumber: str) -> None:
    """Mengganti basis data aktif dengan berkas cadangan (otomatis mencadangkan yang lama)."""
    uji = sqlite3.connect(sumber)
    try:
        uji.execute("SELECT count(*) FROM akun").fetchone()
        uji.execute("SELECT count(*) FROM jurnal").fetchone()
    finally:
        uji.close()
    buat_cadangan()
    tutup_koneksi()
    shutil.copy2(sumber, path_db())
    koneksi()
