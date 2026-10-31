"""Komponen antarmuka yang dipakai berulang: gaya, tabel, input angka, pesan."""
from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk
from datetime import date, datetime
from tkinter import font as tkfont
from tkinter import messagebox, ttk

# Palet warna
BIRU = "#1F4E79"
BIRU_MUDA = "#DCE6F1"
BIRU_HOVER = "#2E6DA4"
HIJAU = "#1E7B34"
MERAH = "#B00020"
ORANYE = "#B26B00"
ABU = "#F5F7FA"
ABU_GARIS = "#D3DCE6"
PUTIH = "#FFFFFF"
TEKS = "#1A1A1A"
TEKS_REDUP = "#5A6673"


def keluarga_font() -> str:
    tersedia = set(tkfont.families())
    for nama in ("Segoe UI", "Noto Sans", "DejaVu Sans", "Helvetica", "Arial"):
        if nama in tersedia:
            return nama
    return "TkDefaultFont"


def pasang_gaya(akar: tk.Tk) -> None:
    f = keluarga_font()
    akar.option_add("*Font", (f, 10))
    gaya = ttk.Style(akar)
    try:
        gaya.theme_use("clam")
    except tk.TclError:
        pass
    gaya.configure(".", font=(f, 10), background=ABU, foreground=TEKS)
    gaya.configure("TFrame", background=ABU)
    gaya.configure("Kartu.TFrame", background=PUTIH, relief="flat")
    gaya.configure("Kop.TFrame", background=BIRU)
    gaya.configure("TLabel", background=ABU, foreground=TEKS)
    gaya.configure("Kartu.TLabel", background=PUTIH)
    gaya.configure("KartuJudul.TLabel", background=PUTIH, foreground=TEKS_REDUP, font=(f, 9))
    gaya.configure("KartuNilai.TLabel", background=PUTIH, foreground=BIRU, font=(f, 15, "bold"))
    gaya.configure("Kop.TLabel", background=BIRU, foreground=PUTIH, font=(f, 11, "bold"))
    gaya.configure("KopKecil.TLabel", background=BIRU, foreground="#C8DAF0", font=(f, 9))
    gaya.configure("Judul.TLabel", font=(f, 13, "bold"), foreground=BIRU)
    gaya.configure("Sub.TLabel", foreground=TEKS_REDUP, font=(f, 9))
    gaya.configure("Tebal.TLabel", font=(f, 10, "bold"))

    gaya.configure("TButton", font=(f, 10), padding=(10, 6))
    gaya.configure("Utama.TButton", font=(f, 10, "bold"), foreground=PUTIH,
                   background=BIRU, padding=(12, 7), borderwidth=0)
    gaya.map("Utama.TButton", background=[("active", BIRU_HOVER), ("disabled", "#9AA7B4")])
    gaya.configure("Bahaya.TButton", font=(f, 10, "bold"), foreground=PUTIH,
                   background=MERAH, padding=(12, 7), borderwidth=0)
    gaya.map("Bahaya.TButton", background=[("active", "#D32F2F"), ("disabled", "#C9A0A8")])
    gaya.configure("Hijau.TButton", font=(f, 10, "bold"), foreground=PUTIH,
                   background=HIJAU, padding=(12, 7), borderwidth=0)
    gaya.map("Hijau.TButton", background=[("active", "#2E9E48"), ("disabled", "#9BBFA5")])

    gaya.configure("TNotebook", background=ABU, borderwidth=0)
    gaya.configure("TNotebook.Tab", font=(f, 10), padding=(14, 8))
    gaya.map("TNotebook.Tab", background=[("selected", PUTIH)],
             foreground=[("selected", BIRU)])
    gaya.configure("Treeview", font=(f, 10), rowheight=24, background=PUTIH,
                   fieldbackground=PUTIH, borderwidth=1)
    gaya.configure("Treeview.Heading", font=(f, 10, "bold"), background=BIRU_MUDA,
                   foreground=BIRU, relief="flat", padding=(4, 6))
    gaya.map("Treeview.Heading", background=[("active", BIRU_MUDA)])
    gaya.configure("TEntry", fieldbackground=PUTIH, padding=4)
    gaya.configure("TCombobox", fieldbackground=PUTIH, padding=4)
    gaya.configure("TLabelframe", background=ABU)
    gaya.configure("TLabelframe.Label", background=ABU, foreground=BIRU,
                   font=(f, 10, "bold"))


# --------------------------------------------------------------------------- #
# Format angka & tanggal
# --------------------------------------------------------------------------- #
def rp(nilai, nol: str = "-") -> str:
    n = round(float(nilai or 0))
    if n == 0:
        return nol
    teks = f"{abs(n):,}".replace(",", ".")
    return f"({teks})" if n < 0 else teks


def rp_lengkap(nilai) -> str:
    return "Rp " + rp(nilai, "0")


def ke_angka(teks: str) -> float:
    teks = str(teks or "").strip().replace("Rp", "").replace(" ", "")
    negatif = teks.startswith("(") and teks.endswith(")")
    teks = teks.strip("()")
    if "," in teks and "." in teks:
        teks = teks.replace(".", "").replace(",", ".")
    else:
        teks = teks.replace(".", "").replace(",", ".")
    try:
        nilai = float(teks or 0)
    except ValueError:
        nilai = 0.0
    return -nilai if negatif else nilai


def tgl_id(nilai) -> str:
    if not nilai:
        return ""
    if isinstance(nilai, str):
        try:
            nilai = datetime.strptime(nilai[:10], "%Y-%m-%d").date()
        except ValueError:
            return nilai
    return f"{nilai.day:02d}/{nilai.month:02d}/{nilai.year}"


def dari_tgl_id(teks: str) -> str | None:
    teks = str(teks or "").strip().replace(".", "/").replace("-", "/")
    for pola in ("%d/%m/%Y", "%Y/%m/%d", "%d/%m/%y"):
        try:
            return datetime.strptime(teks, pola).date().isoformat()
        except ValueError:
            continue
    return None


# --------------------------------------------------------------------------- #
# Widget
# --------------------------------------------------------------------------- #
class EntriAngka(ttk.Entry):
    """Entry angka rupiah: mengetik angka saja, otomatis diberi pemisah ribuan."""

    def __init__(self, induk, lebar=16, saat_ubah=None, **kw):
        self.var = tk.StringVar()
        super().__init__(induk, textvariable=self.var, width=lebar, justify="right", **kw)
        self.saat_ubah = saat_ubah
        self.var.trace_add("write", self._ubah)
        self.bind("<FocusOut>", lambda e: self.rapikan())
        self.bind("<FocusIn>", lambda e: self.select_range(0, "end"))
        self._sedang = False

    def _ubah(self, *_):
        if self._sedang:
            return
        if self.saat_ubah:
            self.saat_ubah()

    def rapikan(self):
        nilai = self.nilai()
        self._sedang = True
        self.var.set(rp(nilai, "") if nilai else "")
        self._sedang = False

    def nilai(self) -> float:
        return ke_angka(self.var.get())

    def set_nilai(self, nilai):
        self._sedang = True
        self.var.set(rp(nilai, "") if nilai else "")
        self._sedang = False


class EntriTanggal(ttk.Frame):
    """Input tanggal DD/MM/YYYY dengan tombol pemilih tanggal sederhana."""

    def __init__(self, induk, nilai: str | None = None, **kw):
        super().__init__(induk, **kw)
        self.var = tk.StringVar(value=tgl_id(nilai or date.today().isoformat()))
        self.entry = ttk.Entry(self, textvariable=self.var, width=12, justify="center")
        self.entry.pack(side="left")
        ttk.Button(self, text="📅", width=3, command=self._pilih).pack(side="left", padx=(3, 0))

    def iso(self) -> str | None:
        return dari_tgl_id(self.var.get())

    def set_iso(self, nilai: str):
        self.var.set(tgl_id(nilai))

    def _pilih(self):
        awal = self.iso() or date.today().isoformat()
        hasil = KalenderDialog(self.winfo_toplevel(), awal).hasil
        if hasil:
            self.set_iso(hasil)


class KalenderDialog(tk.Toplevel):
    """Pemilih tanggal ringkas tanpa pustaka tambahan."""

    def __init__(self, induk, iso_awal: str):
        super().__init__(induk)
        self.title("Pilih Tanggal")
        self.resizable(False, False)
        self.hasil = None
        self.transient(induk)
        awal = datetime.strptime(iso_awal, "%Y-%m-%d").date()
        self.tahun, self.bulan = awal.year, awal.month
        self.bingkai = ttk.Frame(self, padding=10)
        self.bingkai.pack()
        self._gambar()
        self.grab_set()
        self.wait_window()

    def _gambar(self):
        import calendar

        from .. import db
        for w in self.bingkai.winfo_children():
            w.destroy()
        atas = ttk.Frame(self.bingkai)
        atas.pack(fill="x", pady=(0, 6))
        ttk.Button(atas, text="◀", width=3, command=lambda: self._geser(-1)).pack(side="left")
        ttk.Label(atas, text=f"{db.NAMA_BULAN[self.bulan]} {self.tahun}",
                  style="Tebal.TLabel").pack(side="left", expand=True)
        ttk.Button(atas, text="▶", width=3, command=lambda: self._geser(1)).pack(side="right")
        grid = ttk.Frame(self.bingkai)
        grid.pack()
        for i, h in enumerate(["Sn", "Sl", "Rb", "Km", "Jm", "Sb", "Mg"]):
            ttk.Label(grid, text=h, width=4, anchor="center",
                      style="Sub.TLabel").grid(row=0, column=i, padx=1, pady=1)
        for r, minggu in enumerate(calendar.Calendar().monthdayscalendar(self.tahun, self.bulan), 1):
            for c, hari in enumerate(minggu):
                if hari == 0:
                    continue
                ttk.Button(grid, text=str(hari), width=4,
                           command=lambda h=hari: self._pilih(h)).grid(row=r, column=c, padx=1, pady=1)

    def _geser(self, arah: int):
        b = self.bulan + arah
        if b < 1:
            self.tahun, self.bulan = self.tahun - 1, 12
        elif b > 12:
            self.tahun, self.bulan = self.tahun + 1, 1
        else:
            self.bulan = b
        self._gambar()

    def _pilih(self, hari: int):
        self.hasil = date(self.tahun, self.bulan, hari).isoformat()
        self.destroy()


def buat_tabel(induk, kolom: list[tuple], tinggi: int = 15, pilih: str = "browse") -> ttk.Treeview:
    """kolom = [(id, judul, lebar, rata), ...]"""
    bingkai = ttk.Frame(induk)
    bingkai.pack(fill="both", expand=True)
    tabel = ttk.Treeview(bingkai, columns=[k[0] for k in kolom], show="headings",
                         height=tinggi, selectmode=pilih)
    for kid, judul, lebar, rata in kolom:
        tabel.heading(kid, text=judul, anchor="center")
        tabel.column(kid, width=lebar, anchor=rata, stretch=(rata == "w"))
    vs = ttk.Scrollbar(bingkai, orient="vertical", command=tabel.yview)
    hs = ttk.Scrollbar(bingkai, orient="horizontal", command=tabel.xview)
    tabel.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
    tabel.grid(row=0, column=0, sticky="nsew")
    vs.grid(row=0, column=1, sticky="ns")
    hs.grid(row=1, column=0, sticky="ew")
    bingkai.rowconfigure(0, weight=1)
    bingkai.columnconfigure(0, weight=1)
    tabel.tag_configure("genap", background="#FAFCFF")
    tabel.tag_configure("total", background=BIRU_MUDA, font=(keluarga_font(), 10, "bold"))
    tabel.tag_configure("judul", background="#EDF2F8", font=(keluarga_font(), 10, "bold"))
    tabel.tag_configure("merah", foreground=MERAH)
    return tabel


def isi_tabel(tabel: ttk.Treeview, baris: list[list], tag_khusus: dict[int, str] | None = None):
    tabel.delete(*tabel.get_children())
    for i, data in enumerate(baris):
        tag = (tag_khusus or {}).get(i, "genap" if i % 2 else "")
        tabel.insert("", "end", values=data, tags=(tag,))


class Kartu(ttk.Frame):
    """Kotak ringkasan angka di beranda."""

    def __init__(self, induk, judul: str, nilai: str = "-", warna: str = BIRU):
        super().__init__(induk, style="Kartu.TFrame", padding=(14, 10))
        self.lbl_judul = ttk.Label(self, text=judul, style="KartuJudul.TLabel")
        self.lbl_judul.pack(anchor="w")
        self.lbl_nilai = ttk.Label(self, text=nilai, style="KartuNilai.TLabel", foreground=warna)
        self.lbl_nilai.pack(anchor="w", pady=(2, 0))

    def set(self, nilai: str, warna: str | None = None):
        self.lbl_nilai.configure(text=nilai)
        if warna:
            self.lbl_nilai.configure(foreground=warna)


# --------------------------------------------------------------------------- #
# Pesan & berkas
# --------------------------------------------------------------------------- #
def info(judul: str, pesan: str, induk=None):
    messagebox.showinfo(judul, pesan, parent=induk)


def galat(judul: str, pesan: str, induk=None):
    messagebox.showerror(judul, _perjelas(pesan), parent=induk)


def _perjelas(pesan: str) -> str:
    """Ubah pesan galat teknis menjadi penjelasan yang bisa ditindaklanjuti."""
    p = str(pesan)
    kecil = p.lower()
    if "permission denied" in kecil or "errno 13" in kecil or "being used by another" in kecil:
        return (
            "Berkas hasil cetak sedang dibuka aplikasi lain, sehingga tidak "
            "bisa ditimpa.\n\n"
            "Cara mengatasi: tutup jendela PDF atau Excel yang sedang terbuka, "
            "lalu ulangi perintah cetak.\n\n"
            "Rincian teknis:\n" + p
        )
    if "no space left" in kecil:
        return "Ruang penyimpanan komputer penuh. Kosongkan sebagian berkas lalu ulangi.\n\n" + p
    return p


def peringatan(judul: str, pesan: str, induk=None):
    messagebox.showwarning(judul, pesan, parent=induk)


def tanya(judul: str, pesan: str, induk=None) -> bool:
    return messagebox.askyesno(judul, pesan, parent=induk)


def buka_berkas(path: str):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


def selesai_cetak(path: str, induk=None):
    """Memberi tahu pengguna berkas sudah jadi, lalu membukanya."""
    if tanya("Berkas siap",
             f"Berkas berhasil dibuat:\n\n{path}\n\nBuka sekarang?", induk):
        buka_berkas(path)
