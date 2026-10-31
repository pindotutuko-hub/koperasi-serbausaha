@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Membuat Versi Portable - Pembukuan Kantin Koperasi
color 0B
cd /d "%~dp0"

echo.
echo ================================================================
echo   MEMBUAT VERSI PORTABLE - PEMBUKUAN KANTIN KOPERASI
echo.
echo   Hasilnya satu folder yang bisa disalin ke flashdisk dan
echo   langsung dipakai di komputer Windows mana pun, tanpa
echo   dipasang, dan tanpa meninggalkan data di komputer itu.
echo ================================================================
echo.

REM --- Pastikan EXE sudah ada --------------------------------------------
if not exist "dist\KantinKoperasi.exe" (
    echo   Berkas EXE belum ada. Menjalankan proses build lebih dulu...
    echo.
    call SETUP_OTOMATIS.bat
    if not exist "dist\KantinKoperasi.exe" (
        echo.
        echo   [X] EXE masih belum terbentuk. Perbaiki galat di atas dulu.
        pause
        exit /b 1
    )
)

set "TUJUAN=PembukuanKantin-Portable"

echo [1/3] Menyiapkan folder %TUJUAN%...
if exist "%TUJUAN%" rmdir /s /q "%TUJUAN%"
mkdir "%TUJUAN%"
mkdir "%TUJUAN%\Data"

echo [2/3] Menyalin berkas...
copy /y "dist\KantinKoperasi.exe" "%TUJUAN%\" >nul
if exist "PANDUAN.md" copy /y "PANDUAN.md" "%TUJUAN%\" >nul
if exist "contoh" xcopy /e /i /y "contoh" "%TUJUAN%\contoh" >nul

echo [3/3] Menulis penanda portable...
> "%TUJUAN%\portable.txt" echo Penanda mode portable.
>>"%TUJUAN%\portable.txt" echo.
>>"%TUJUAN%\portable.txt" echo Selama berkas ini ^(atau folder Data^) ada di sebelah
>>"%TUJUAN%\portable.txt" echo KantinKoperasi.exe, seluruh data pembukuan disimpan di
>>"%TUJUAN%\portable.txt" echo folder Data, bukan di komputer yang dipakai.
>>"%TUJUAN%\portable.txt" echo.
>>"%TUJUAN%\portable.txt" echo Hapus berkas ini DAN folder Data bila ingin program
>>"%TUJUAN%\portable.txt" echo kembali menyimpan data di profil pengguna komputer.

> "%TUJUAN%\BACA SAYA.txt" echo PROGRAM PEMBUKUAN KANTIN KOPERASI - VERSI PORTABLE
>>"%TUJUAN%\BACA SAYA.txt" echo ==================================================
>>"%TUJUAN%\BACA SAYA.txt" echo.
>>"%TUJUAN%\BACA SAYA.txt" echo CARA PAKAI
>>"%TUJUAN%\BACA SAYA.txt" echo   Klik dua kali KantinKoperasi.exe. Tidak perlu dipasang.
>>"%TUJUAN%\BACA SAYA.txt" echo.
>>"%TUJUAN%\BACA SAYA.txt" echo DATA TERSIMPAN DI MANA
>>"%TUJUAN%\BACA SAYA.txt" echo   Di folder Data, di sebelah program ini. Seluruh pembukuan
>>"%TUJUAN%\BACA SAYA.txt" echo   ikut berpindah bila folder ini disalin ke flashdisk atau
>>"%TUJUAN%\BACA SAYA.txt" echo   komputer lain. Komputer yang dipakai tidak ditulisi apa pun.
>>"%TUJUAN%\BACA SAYA.txt" echo.
>>"%TUJUAN%\BACA SAYA.txt" echo PERINGATAN WINDOWS SAAT PERTAMA DIBUKA
>>"%TUJUAN%\BACA SAYA.txt" echo   Bila muncul "Windows protected your PC", klik More info
>>"%TUJUAN%\BACA SAYA.txt" echo   lalu Run anyway. Itu karena program belum bersertifikat
>>"%TUJUAN%\BACA SAYA.txt" echo   digital, bukan karena berisi virus.
>>"%TUJUAN%\BACA SAYA.txt" echo.
>>"%TUJUAN%\BACA SAYA.txt" echo JANGAN LUPA MENCADANGKAN
>>"%TUJUAN%\BACA SAYA.txt" echo   Flashdisk mudah hilang atau rusak. Sesekali salin seluruh
>>"%TUJUAN%\BACA SAYA.txt" echo   folder Data ke komputer atau penyimpanan awan.
>>"%TUJUAN%\BACA SAYA.txt" echo.
>>"%TUJUAN%\BACA SAYA.txt" echo Panduan lengkap ada di berkas PANDUAN.md

color 0A
echo.
echo ================================================================
echo   SELESAI!
echo.
echo   Folder siap pakai:  %TUJUAN%\
echo.
echo   Salin seluruh folder itu ke flashdisk. Di komputer mana pun,
echo   klik dua kali KantinKoperasi.exe - data tetap ikut di dalamnya.
echo ================================================================
echo.
start "" explorer "%CD%\%TUJUAN%"
pause
