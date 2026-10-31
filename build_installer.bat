@echo off
chcp 65001 >nul
title Membuat Installer KantinKoperasi
color 0A

echo.
echo ================================================================
echo   MEMBUAT INSTALLER - PROGRAM PEMBUKUAN KANTIN KOPERASI
echo ================================================================
echo.

if not exist "dist\KantinKoperasi.exe" (
    echo [X] Berkas dist\KantinKoperasi.exe belum ada.
    echo     Jalankan dulu:  build_exe.bat
    echo.
    pause
    exit /b 1
)

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe"      set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if "%ISCC%"=="" (
    echo [X] Inno Setup belum terpasang.
    echo.
    echo     Unduh gratis di:  https://jrsoftware.org/isdl.php
    echo     Pasang, lalu jalankan berkas ini lagi.
    echo.
    pause
    exit /b 1
)

echo Menggunakan: %ISCC%
echo.
"%ISCC%" installer.iss
if errorlevel 1 (
    echo.
    echo [X] Gagal membuat installer. Periksa pesan di atas.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   SELESAI!
echo.
echo   Installer siap dibagikan:
echo   installer_output\KantinKoperasi_Setup_1.0.1.exe
echo ================================================================
echo.
explorer installer_output
pause
