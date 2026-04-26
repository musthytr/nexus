#!/bin/bash

# Nexus Linux Interface - Arch Linux Installer
# SADECE ARCH LINUX VE TÜREVLERİ İÇİNDİR

set -e

echo "------------------------------------------"
echo "   Nexus Linux (Arch Only) Yükleyici     "
echo "------------------------------------------"

if [ ! -f /etc/arch-release ]; then
    echo "HATA: Bu yazılım sadece Arch Linux için tasarlanmıştır."
    exit 1
fi

echo "Bağımlılıklar kuruluyor (pacman)..."
sudo pacman -S --noconfirm python python-gobject webkit2gtk git flatpak

echo "Nexus dosyaları hazırlanıyor..."
if [ ! -f "nexus.py" ]; then
    git clone https://github.com/musthytr/nexus.git
    cd nexus
fi

chmod +x nexus.py

echo "------------------------------------------"
echo "Kurulum Tamamlandı!"
echo "Çalıştırmak için: python3 nexus.py"
echo "------------------------------------------"
