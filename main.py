# -*- coding: utf-8 -*-
"""
Program Pembukuan Kantin Koperasi
Titik masuk aplikasi (entry point).

Jalankan dengan:  python main.py
"""
import os
import sys
import traceback


def _pasang_jalur():
    """Pastikan folder program ada di sys.path (penting untuk build PyInstaller)."""
    if getattr(sys, "frozen", False):
        dasar = os.path.dirname(sys.executable)
    else:
        dasar = os.path.dirname(os.path.abspath(__file__))
    if dasar not in sys.path:
        sys.path.insert(0, dasar)


def main():
    _pasang_jalur()
    try:
        from app.ui.utama import jalankan
    except Exception:
        _tampilkan_galat_fatal(traceback.format_exc())
        return 1
    try:
        jalankan()
    except Exception:
        _tampilkan_galat_fatal(traceback.format_exc())
        return 1
    return 0


def _tampilkan_galat_fatal(pesan):
    """Tampilkan galat agar pengguna tahu apa yang terjadi, walau GUI gagal."""
    sys.stderr.write(pesan)
    try:
        import tkinter as tk
        from tkinter import messagebox
        akar = tk.Tk()
        akar.withdraw()
        messagebox.showerror(
            "Program Pembukuan Kantin - Galat",
            "Program gagal dijalankan.\n\n"
            + pesan[-1500:]
            + "\n\nSalin pesan ini dan laporkan ke pembuat program.",
        )
        akar.destroy()
    except Exception:
        pass


if __name__ == "__main__":
    sys.exit(main())
