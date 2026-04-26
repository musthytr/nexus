#!/bin/bash

# Nexus Linux Interface - Universal Installer
# Desteklenen Sistemler: Arch Linux, Debian/Ubuntu, Fedora

set -e

echo "------------------------------------------"
echo "   Nexus Linux Arayüzü Yükleyicisi        "
echo "------------------------------------------"

# OS Algılama
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    OS_LIKE=$ID_LIKE
else
    echo "Hata: İşletim sistemi algılanamadı!"
    exit 1
fi

echo "Algılanan Sistem: $NAME"

install_arch() {
    echo "Arch Linux bağımlılıkları kuruluyor..."
    sudo pacman -S --noconfirm python python-gobject webkit2gtk git flatpak
}

install_debian() {
    echo "Debian/Ubuntu bağımlılıkları kuruluyor..."
    sudo apt update
    sudo apt install -y python3 python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.0 git flatpak
}

install_fedora() {
    echo "Fedora bağımlılıkları kuruluyor..."
    sudo dnf install -y python3 python3-gobject webkit2gtk3 git flatpak
}

case "$OS" in
    arch|manjaro|cachyos)
        install_arch
        ;;
    debian|ubuntu|linuxmint|pop)
        install_debian
        ;;
    fedora)
        install_fedora
        ;;
    *)
        if [[ "$OS_LIKE" == *"arch"* ]]; then
            install_arch
        elif [[ "$OS_LIKE" == *"debian"* ]] || [[ "$OS_LIKE" == *"ubuntu"* ]]; then
            install_debian
        else
            echo "Üzgünüz, bu dağıtım henüz otomatik olarak desteklenmiyor."
            echo "Lütfen manuel kurulum yapın veya geliştiriciye bildirin."
            exit 1
        fi
        ;;
esac

echo "------------------------------------------"
echo "Bağımlılıklar başarıyla kuruldu."
echo "Nexus dosyaları indiriliyor..."

# Eğer zaten bir repo içindeyse indirmeye gerek yok, değilse klonla
if [ ! -f "nexus.py" ]; then
    git clone https://github.com/musthytr/nexus.git
    cd nexus
fi

chmod +x nexus.py

echo "------------------------------------------"
echo "Kurulum Tamamlandı!"
echo "Nexus'u başlatmak için: python3 nexus.py"
echo "------------------------------------------"
