@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Membuat KantinKoperasi.exe
color 0B

echo.
echo ================================================================
echo   MEMBUAT BERKAS EXE - PROGRAM PEMBUKUAN KANTIN KOPERASI
echo ================================================================
echo.

REM --- 1. Periksa Python ------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python belum terpasang di komputer ini.
    echo.
    echo     Silakan unduh dari:  https://www.python.org/downloads/
    echo     PENTING: saat memasang, centang "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo [1/5] Python ditemukan: %%v

REM --- 2. Siapkan lingkungan virtual ------------------------------------
if not exist ".venv" (
    echo [2/5] Membuat lingkungan virtual ^(sekali saja, mohon tunggu^)...
    python -m venv .venv
    if errorlevel 1 (
        echo [X] Gagal membuat lingkungan virtual.
        pause
        exit /b 1
    )
) else (
    echo [2/5] Lingkungan virtual sudah ada, dilewati.
)
call .venv\Scripts\activate.bat

REM --- 3. Pasang kebutuhan ----------------------------------------------
echo [3/5] Memasang pustaka yang dibutuhkan ^(butuh internet^)...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [X] Gagal memasang pustaka. Periksa koneksi internet.
    pause
    exit /b 1
)

REM --- 4. Bersihkan hasil lama ------------------------------------------
echo [4/5] Membersihkan hasil build sebelumnya...
if exist "build" rmdir /s /q "build"
if exist "dist"  rmdir /s /q "dist"

REM --- 5. Bangun EXE ----------------------------------------------------
echo [5/5] Menyusun KantinKoperasi.exe ^(3-6 menit, jangan ditutup^)...
echo.
pyinstaller KantinKoperasi.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo [X] Proses build GAGAL. Salin pesan merah di atas untuk diperiksa.
    pause
    exit /b 1
)

if not exist "dist\KantinKoperasi.exe" (
    echo [X] Berkas EXE tidak terbentuk. Periksa pesan di atas.
    pause
    exit /b 1
)

REM --- Salin berkas pendamping ke folder dist ---------------------------
if exist "PANDUAN.md"  copy /y "PANDUAN.md"  "dist\PANDUAN.md"  >nul
if exist "contoh"      xcopy /e /i /y "contoh" "dist\contoh" >nul

echo.
echo ================================================================
echo   SELESAI!
echo.
echo   Berkas siap pakai:  dist\KantinKoperasi.exe
echo.
echo   - Bisa langsung dijalankan dengan klik dua kali.
echo   - Bisa disalin ke komputer Windows lain ^(tanpa perlu Python^).
echo   - Untuk membuat INSTALLER, jalankan: build_installer.bat
echo ================================================================
echo.
explorer dist
pause
