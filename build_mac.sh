#!/usr/bin/env bash
# =============================================================================
#  Membuat aplikasi macOS - Program Pembukuan Kantin Koperasi
#
#  Cara pakai (di Mac):
#     1. Buka Terminal
#     2. Masuk ke folder ini:  cd /path/ke/koperasi-serbausaha
#     3. Jalankan           :  bash build_mac.sh
#
#  Hasil:  dist/KantinKoperasi.app          (aplikasi)
#          dist/KantinKoperasi-mac.dmg      (berkas pemasangan)
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

biru()  { printf "\033[1;34m%s\033[0m\n" "$*"; }
hijau() { printf "\033[1;32m%s\033[0m\n" "$*"; }
merah() { printf "\033[1;31m%s\033[0m\n" "$*"; }

echo
biru "================================================================"
biru "  MEMBUAT APLIKASI macOS - PEMBUKUAN KANTIN KOPERASI"
biru "================================================================"
echo

# --- 1. Python --------------------------------------------------------------
echo "[1/5] Memeriksa Python..."
if command -v python3 >/dev/null 2>&1; then
    echo "      Ditemukan: $(python3 --version)"
else
    merah "  [X] Python 3 belum terpasang."
    echo
    echo "      Pasang dengan salah satu cara berikut:"
    echo "        • Unduh dari https://www.python.org/downloads/macos/"
    echo "        • Atau lewat Homebrew:  brew install python"
    echo
    exit 1
fi

# --- 2. Lingkungan virtual --------------------------------------------------
echo "[2/5] Menyiapkan lingkungan virtual..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# --- 3. Pustaka -------------------------------------------------------------
echo "[3/5] Memasang pustaka yang dibutuhkan..."
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet

# --- 4. Bangun .app ---------------------------------------------------------
echo "[4/5] Menyusun KantinKoperasi.app (3-6 menit)..."
rm -rf build dist
pyinstaller KantinKoperasi.spec --noconfirm --clean

if [ ! -d "dist/KantinKoperasi.app" ]; then
    merah "  [X] Pembuatan aplikasi gagal. Periksa pesan di atas."
    exit 1
fi

# Tandatangan ad-hoc agar macOS mau menjalankannya tanpa keluhan tambahan
codesign --force --deep --sign - "dist/KantinKoperasi.app" 2>/dev/null \
    && echo "      Ditandatangani (ad-hoc)." \
    || echo "      Lewati penandatanganan (tidak tersedia)."

# Sertakan panduan dan contoh di sebelah aplikasi
cp -f PANDUAN.md dist/ 2>/dev/null || true
cp -Rf contoh dist/ 2>/dev/null || true

# --- 5. Buat DMG ------------------------------------------------------------
echo "[5/5] Membuat berkas DMG..."
STAGING="$(mktemp -d)"
cp -R "dist/KantinKoperasi.app" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
cp -f PANDUAN.md "$STAGING/" 2>/dev/null || true
rm -f "dist/KantinKoperasi-mac.dmg"
hdiutil create -volname "Pembukuan Kantin Koperasi" \
    -srcfolder "$STAGING" -ov -format UDZO \
    "dist/KantinKoperasi-mac.dmg" >/dev/null
rm -rf "$STAGING"

echo
hijau "================================================================"
hijau "  SELESAI!"
echo
echo "  Aplikasi  : dist/KantinKoperasi.app"
echo "  Pemasangan: dist/KantinKoperasi-mac.dmg"
echo
echo "  Membuka pertama kali: klik KANAN ikon aplikasi lalu pilih Open,"
echo "  kemudian tekan Open lagi pada kotak peringatan. Cukup sekali;"
echo "  selanjutnya bisa dibuka seperti aplikasi biasa."
echo
echo "  Ingin mode PORTABLE (data ikut pindah bersama aplikasi)?"
echo "  Buat folder bernama Data di sebelah KantinKoperasi.app"
hijau "================================================================"
echo
open dist 2>/dev/null || true
