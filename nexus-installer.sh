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
# WebKit paket adları Arch'ta değişmiş olabilir, alternatifleri deniyoruz
sudo pacman -S --noconfirm python python-gobject git flatpak

if pacman -Si webkit2gtk-4.1 &>/dev/null; then
    sudo pacman -S --noconfirm webkit2gtk-4.1
elif pacman -Si webkit2gtk-4.0 &>/dev/null; then
    sudo pacman -S --noconfirm webkit2gtk-4.0
elif pacman -Si webkit2gtk &>/dev/null; then
    sudo pacman -S --noconfirm webkit2gtk
else
    echo "UYARI: webkit2gtk paketi bulunamadı. Lütfen manuel kurun."
fi

echo "Nexus dosyaları hazırlanıyor..."
if [ ! -d "nexus" ]; then
    git clone https://github.com/musthytr/nexus.git
    cd nexus
else
    cd nexus
    git pull
fi

chmod +x nexus.py

echo "------------------------------------------"
echo "Kurulum Tamamlandı!"
echo "Çalıştırmak için: python3 nexus.py"
echo "------------------------------------------"
