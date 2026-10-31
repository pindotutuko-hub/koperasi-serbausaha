"""Lapisan basis data (SQLite) untuk Program Pembukuan Kantin Koperasi."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime

APP_NAME = "KantinKoperasi"
VERSI_APLIKASI = "2.0.0"
VERSI_DB = 2

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
CREATE TABLE IF NOT EXISTS jenis_persediaan (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nama       TEXT NOT NULL UNIQUE,
    satuan     TEXT DEFAULT 'unit',
    kode_akun  TEXT NOT NULL,       -- akun persediaan di neraca
    kode_hpp   TEXT NOT NULL,       -- akun harga pokok penjualan
    kode_jual  TEXT NOT NULL,       -- akun pendapatan penjualannya
    urut       INTEGER DEFAULT 0,
    aktif      INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS mutasi_persediaan (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    periode_id  INTEGER NOT NULL,
    jenis_id    INTEGER NOT NULL,
    tanggal     TEXT NOT NULL,
    arah        TEXT NOT NULL,       -- MASUK / KELUAR / PENYESUAIAN
    keterangan  TEXT,
    jumlah      REAL DEFAULT 0,      -- banyaknya unit
    harga       REAL DEFAULT 0,      -- harga per unit (MASUK: dari nota; KELUAR: dihitung sistem)
    nilai       REAL DEFAULT 0,      -- jumlah x harga
    sisa_jumlah REAL DEFAULT 0,      -- saldo unit setelah mutasi ini
    sisa_nilai  REAL DEFAULT 0,      -- saldo rupiah setelah mutasi ini
    jurnal_id   INTEGER,             -- jurnal yang dibentuk dari mutasi ini
    dibuat      TEXT,
    FOREIGN KEY (jenis_id) REFERENCES jenis_persediaan (id)
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
CREATE INDEX IF NOT EXISTS ix_mutasi_periode ON mutasi_persediaan (periode_id);
CREATE INDEX IF NOT EXISTS ix_mutasi_jenis   ON mutasi_persediaan (jenis_id, tanggal, id);
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
        migrasi(_koneksi)
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
            " VALUES (?,?,?,?,?,?,?,?)",
            (a["kode"], a["nama"], a["kategori"], a.get("subkategori") or a["kategori"],
             a["saldo_normal"], a.get("peran", ""), a.get("urut", 0), a.get("aktif", 1)),
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
    for j in data.get("jenis_persediaan", []):
        kon.execute(
            "INSERT OR IGNORE INTO jenis_persediaan"
            " (nama,satuan,kode_akun,kode_hpp,kode_jual,urut,aktif) VALUES (?,?,?,?,?,?,1)",
            (j["nama"], j.get("satuan", "unit"), j["kode_akun"],
             j["kode_hpp"], j["kode_jual"], j.get("urut", 0)),
        )

    kon.execute(
        "INSERT INTO log (waktu,aksi,detail) VALUES (?,?,?)",
        (sekarang, "BASIS DATA DIBUAT",
         "Data awal (bagan akun dan jenis persediaan) dimuat."),
    )


def migrasi(kon: sqlite3.Connection) -> None:
    """Menyesuaikan basis data lama ke struktur terbaru.

    Dipanggil setiap kali koneksi dibuka. Aman dijalankan berulang kali:
    setiap langkah memeriksa dulu apakah pekerjaannya sudah dilakukan.
    Data lama tidak pernah dihapus.
    """
    versi = kon.execute(
        "SELECT nilai FROM pengaturan WHERE kunci='versi_db'").fetchone()
    versi = int(versi["nilai"]) if versi and str(versi["nilai"]).isdigit() else 1
    if versi >= VERSI_DB:
        return

    berkas = os.path.join(folder_program(), "app", "data_awal.json")
    if not os.path.exists(berkas):
        berkas = os.path.join(folder_program(), "data_awal.json")
    data = {}
    if os.path.exists(berkas):
        with open(berkas, encoding="utf-8") as f:
            data = json.load(f)

    ada = {r["kode"] for r in kon.execute("SELECT kode FROM akun")}

    # 1. Akun baru untuk persediaan perpetual
    for a in data.get("akun", []):
        if a["kode"] not in ada:
            kon.execute(
                "INSERT INTO akun (kode,nama,kategori,subkategori,saldo_normal,peran,urut,aktif)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (a["kode"], a["nama"], a["kategori"],
                 a.get("subkategori") or a["kategori"], a["saldo_normal"],
                 a.get("peran", ""), a.get("urut", 0), a.get("aktif", 1)),
            )

    # 2. Akun persediaan lama dipisahkan dari akun persediaan perpetual.
    #
    #    Saldo persediaan dari pembukuan terdahulu tetap tinggal di akun 114
    #    dan tidak diusik, sesuai permintaan: buku persediaan baru dipakai
    #    untuk transaksi ke depan, bukan untuk menata ulang yang sudah ada.
    #    Kalau keduanya memakai akun yang sama, kartu persediaan dan laporan
    #    posisi keuangan akan menunjukkan angka yang berbeda.
    terpakai = kon.execute(
        "SELECT (SELECT COUNT(*) FROM jurnal_detail WHERE kode_akun='114')"
        " + (SELECT COUNT(*) FROM saldo_awal WHERE kode_akun='114') AS c"
    ).fetchone()["c"]
    if terpakai:
        kon.execute(
            "UPDATE akun SET nama='Persediaan Barang Toko (saldo lama)', peran=''"
            " WHERE kode='114' AND nama='Persediaan Barang Toko'")
    else:
        kon.execute("UPDATE akun SET peran='', aktif=0 WHERE kode='114'")

    # 3. Akun metode periodik dinonaktifkan — hanya bila belum pernah terpakai,
    #    supaya pembukuan lama yang memakainya tetap utuh dan terbaca.
    for kode in ("511", "512", "513", "514"):
        dipakai = kon.execute(
            "SELECT COUNT(*) c FROM jurnal_detail WHERE kode_akun=?", (kode,)).fetchone()["c"]
        if not dipakai:
            kon.execute("UPDATE akun SET aktif=0 WHERE kode=?", (kode,))

    # 4. Jenis persediaan bawaan
    for j in data.get("jenis_persediaan", []):
        kon.execute(
            "INSERT OR IGNORE INTO jenis_persediaan"
            " (nama,satuan,kode_akun,kode_hpp,kode_jual,urut,aktif) VALUES (?,?,?,?,?,?,1)",
            (j["nama"], j.get("satuan", "unit"), j["kode_akun"],
             j["kode_hpp"], j["kode_jual"], j.get("urut", 0)),
        )

    kon.execute("UPDATE pengaturan SET nilai=? WHERE kunci='versi_db'", (str(VERSI_DB),))
    kon.execute(
        "INSERT INTO log (waktu,aksi,detail) VALUES (?,?,?)",
        (datetime.now().isoformat(timespec="seconds"), "BASIS DATA DIPERBARUI",
         f"Struktur dinaikkan dari versi {versi} ke {VERSI_DB}: "
         "persediaan perpetual dua jenis, buku kas, dan akun harga pokok penjualan."),
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
