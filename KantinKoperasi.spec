# -*- mode: python ; coding: utf-8 -*-
"""
Spesifikasi PyInstaller - Program Pembukuan Kantin Koperasi.

Satu berkas untuk Windows dan macOS; platform dideteksi otomatis.

  Windows : pyinstaller KantinKoperasi.spec --noconfirm
            -> dist/KantinKoperasi.exe        (satu berkas, portable)
  macOS   : pyinstaller KantinKoperasi.spec --noconfirm
            -> dist/KantinKoperasi.app        (bundel aplikasi)
"""
import sys

WINDOWS = sys.platform.startswith("win")
MACOS = sys.platform == "darwin"

datas = [
    ('app/data_awal.json', 'app'),
    ('assets/ikon.png', 'assets'),
    ('assets/ikon64.png', 'assets'),
    ('PANDUAN.md', '.'),
    ('contoh', 'contoh'),
]
if WINDOWS:
    datas.append(('assets/ikon.ico', 'assets'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'reportlab.graphics.barcode',
        'reportlab.pdfbase._fontdata',
        'openpyxl.cell._writer',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 'PyQt5', 'PySide2',
        'notebook', 'IPython', 'test', 'unittest',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

if MACOS:
    # macOS: EXE ramping + COLLECT + BUNDLE menghasilkan .app yang benar.
    exe = EXE(
        pyz, a.scripts, [],
        exclude_binaries=True,
        name='KantinKoperasi',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        target_arch=None,          # ikut arsitektur mesin pembangun
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe, a.binaries, a.zipfiles, a.datas,
        strip=False, upx=False, name='KantinKoperasi',
    )
    app = BUNDLE(
        coll,
        name='KantinKoperasi.app',
        icon='assets/ikon.icns',
        bundle_identifier='id.koperasi.pembukuankantin',
        version='1.0.1',
        info_plist={
            'CFBundleName': 'Pembukuan Kantin',
            'CFBundleDisplayName': 'Program Pembukuan Kantin Koperasi',
            'CFBundleShortVersionString': '1.0.1',
            'CFBundleVersion': '1.0.1',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '11.0',
            'NSHumanReadableCopyright': 'Program Pembukuan Kantin Koperasi',
        },
    )
else:
    # Windows / Linux: satu berkas tunggal, siap dijadikan portable.
    exe = EXE(
        pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
        name='KantinKoperasi',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='assets/ikon.ico' if WINDOWS else None,
        version='version_info.txt' if WINDOWS else None,
    )
