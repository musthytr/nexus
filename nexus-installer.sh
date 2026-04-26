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
    # Arch'ta genellikle tek bir güncel paket vardır
    sudo pacman -S --noconfirm python python-gobject webkit2gtk git flatpak
}

install_debian() {
    echo "Debian/Ubuntu bağımlılıkları kuruluyor..."
    sudo apt update
    # Hem 4.1 hem 4.0'ı deniyoruz, hangisi varsa o kurulur
    sudo apt install -y python3 python3-gi gir1.2-gtk-3.0 git flatpak
    sudo apt install -y gir1.2-webkit2-4.1 || sudo apt install -y gir1.2-webkit2-4.0 || echo "Uyarı: WebKit2 paketi bulunamadı, manuel kurulum gerekebilir."
}

install_fedora() {
    echo "Fedora bağımlılıkları kuruluyor..."
    # Fedora'da paket adları sürümle değişebilir
    sudo dnf install -y python3 python3-gobject git flatpak
    sudo dnf install -y webkit2gtk4.1 || sudo dnf install -y webkit2gtk4.0 || sudo dnf install -y webkit2gtk3 || echo "Uyarı: WebKit2 paketi bulunamadı."
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
        elif [[ "$OS_LIKE" == *"fedora"* ]]; then
            install_fedora
        else
            echo "Üzgünüz, bu dağıtım henüz otomatik olarak desteklenmiyor."
            exit 1
        fi
        ;;
esac

echo "------------------------------------------"
echo "Bağımlılıklar başarıyla kuruldu."
echo "Nexus dosyaları indiriliyor..."

if [ ! -f "nexus.py" ]; then
    if [ -d "nexus" ]; then cd nexus; git pull; cd ..; fi
    git clone https://github.com/musthytr/nexus.git || (cd nexus && git pull)
    cd nexus
fi

chmod +x nexus.py

echo "------------------------------------------"
echo "Kurulum Tamamlandı!"
echo "Nexus'u başlatmak için: python3 nexus.py"
echo "------------------------------------------"
