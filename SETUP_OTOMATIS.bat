@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Setup Otomatis - Program Pembukuan Kantin Koperasi
color 0B
cd /d "%~dp0"

set "VERSI_PY=3.14.7"
set "URL_PY=https://www.python.org/ftp/python/%VERSI_PY%/python-%VERSI_PY%-amd64.exe"
set "UNDUHAN=%TEMP%\python-%VERSI_PY%-amd64.exe"

echo.
echo ================================================================
echo   SETUP OTOMATIS - PROGRAM PEMBUKUAN KANTIN KOPERASI
echo.
echo   Skrip ini akan mengerjakan semuanya sendiri:
echo     1. Memeriksa Python
echo     2. Mengunduh dan memasang Python bila belum ada
echo     3. Memasang pustaka yang dibutuhkan
echo     4. Membuat berkas KantinKoperasi.exe
echo.
echo   Syarat : komputer terhubung internet
echo   Lama   : 5 sampai 12 menit
echo ================================================================
echo.
echo   Tekan sembarang tombol untuk mulai, atau tutup jendela ini
echo   untuk membatalkan.
pause >nul
echo.

REM ================= 1. PERIKSA PYTHON =================
echo [1/5] Memeriksa Python...
set "PYEXE="
REM Abaikan "stub" Microsoft Store yang hanya membuka Store, bukan Python asli.
for /f "delims=" %%p in ('where python 2^>nul') do (
    if not defined PYEXE (
        set "KANDIDAT=%%p"
        if "!KANDIDAT:WindowsApps=!"=="!KANDIDAT!" set "PYEXE=%%p"
    )
)
if defined PYEXE (
    "!PYEXE!" -c "import sys" >nul 2>&1 || set "PYEXE="
)
if not defined PYEXE (
    py -c "import sys" >nul 2>&1 && set "PYEXE=py"
)

if defined PYEXE (
    echo       Python sudah ada:
    "!PYEXE!" --version
    goto :SIAP
)

echo       Python belum terpasang di komputer ini.
echo.

REM ================= 2. UNDUH PYTHON =================
echo [2/5] Mengunduh Python %VERSI_PY% dari python.org ^(sekitar 28 MB^)...
where curl >nul 2>&1
if not errorlevel 1 (
    curl -L --fail --progress-bar -o "%UNDUHAN%" "%URL_PY%"
) else (
    powershell -NoProfile -Command "try{[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%URL_PY%' -OutFile '%UNDUHAN%'}catch{exit 1}"
)

if not exist "%UNDUHAN%" (
    echo.
    echo   [X] Unduhan gagal. Kemungkinan internet terputus atau diblokir.
    echo.
    echo       Silakan unduh manual lewat peramban. Saya bukakan halamannya.
    start "" "https://www.python.org/downloads/windows/"
    echo       Pilih: Windows installer ^(64-bit^) pada Python %VERSI_PY%
    echo       Saat memasang, CENTANG "Add python.exe to PATH".
    echo       Sesudah terpasang, jalankan lagi berkas SETUP_OTOMATIS.bat ini.
    echo.
    pause
    exit /b 1
)
echo       Unduhan selesai.
echo.

REM ================= 3. PASANG PYTHON =================
echo [3/5] Memasang Python ^(2-4 menit, akan muncul jendela progres^)...
start /wait "" "%UNDUHAN%" /passive InstallAllUsers=0 PrependPath=1 AssociateFiles=0 Include_pip=1 Include_test=0 Include_launcher=1
echo       Pemasangan selesai. Mencari lokasi Python...

set "PYEXE="
for /f "delims=" %%d in ('dir /b /ad /o-n "%LOCALAPPDATA%\Programs\Python\Python3*" 2^>nul') do (
    if not defined PYEXE (
        if exist "%LOCALAPPDATA%\Programs\Python\%%d\python.exe" (
            set "PYEXE=%LOCALAPPDATA%\Programs\Python\%%d\python.exe"
        )
    )
)
if not defined PYEXE (
    py -c "import sys" >nul 2>&1 && set "PYEXE=py"
)
if not defined PYEXE (
    python -c "import sys" >nul 2>&1 && set "PYEXE=python"
)

if not defined PYEXE (
    echo.
    echo   [X] Python sudah terpasang, tetapi belum bisa dipanggil dari jendela ini.
    echo.
    echo       Ini normal. Solusinya sederhana:
    echo       TUTUP jendela ini, lalu KLIK LAGI berkas SETUP_OTOMATIS.bat.
    echo.
    pause
    exit /b 1
)
echo       Berhasil terpasang:
"!PYEXE!" --version
echo.

:SIAP
REM ================= 4. PASANG PUSTAKA =================
echo [4/5] Menyiapkan lingkungan dan memasang pustaka...
if not exist ".venv" (
    "!PYEXE!" -m venv .venv
    if errorlevel 1 (
        echo   [X] Gagal membuat lingkungan virtual.
        pause
        exit /b 1
    )
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo   [X] Gagal memasang pustaka. Periksa koneksi internet lalu ulangi.
    pause
    exit /b 1
)
echo       Pustaka siap.
echo.

REM ================= 5. BANGUN EXE =================
echo [5/5] Menyusun KantinKoperasi.exe ^(3-6 menit, jangan ditutup^)...
echo.
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"
pyinstaller KantinKoperasi.spec --noconfirm --clean
if not exist "dist\KantinKoperasi.exe" (
    echo.
    echo   [X] Proses build gagal. Salin pesan merah di atas untuk diperiksa.
    pause
    exit /b 1
)

if exist "PANDUAN.md" copy /y "PANDUAN.md" "dist\PANDUAN.md" >nul
if exist "contoh" xcopy /e /i /y "contoh" "dist\contoh" >nul

color 0A
echo.
echo ================================================================
echo   SEMUA SELESAI!
echo.
echo   Berkas siap pakai:  dist\KantinKoperasi.exe
echo.
echo   - Klik dua kali untuk menjalankan programnya.
echo   - Bisa disalin ke komputer Windows lain, tanpa perlu Python.
echo   - Ingin membuat installer? jalankan build_installer.bat
echo ================================================================
echo.
echo   Membuka folder hasil...
start "" explorer "%CD%\dist"
echo.
pause
