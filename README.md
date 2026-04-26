# Nexus Linux Interface (Arch Linux Only)

⚠️ **SADECE ARCH LINUX İÇİNDİR / FOR ARCH LINUX ONLY** ⚠️

Nexus, Arch Linux kullanıcıları için özel olarak tasarlanmış, sistem bakımı, sürücü kurulumu ve uygulama yönetimini tek bir merkezden yapmanızı sağlayan bir masaüstü arayüzüdür.

## Özellikler

- **Arch Sürücü Köprüsü**: NVIDIA, AMD ve Intel sürücülerini pacman üzerinden kolayca kurun.
- **Uygulama Merkezi**: Flatpak ve AUR (yay) desteği ile uygulama arayın ve yükleyin.
- **AI Asistanı**: Sistem sorunlarını çözmek için entegre AI desteği.
- **Sistem Bakımı**: pacman güncellemeleri ve sistem temizliği.
- **Modern Arayüz**: Web teknolojileriyle güçlendirilmiş şık tasarım.

## Kurulum (Sadece Arch)

Terminalinizi açın ve şu komutu yapıştırın:

```bash
curl -sSL https://raw.githubusercontent.com/musthytr/nexus/master/nexus-installer.sh | bash
```

### Manuel Kurulum

```bash
git clone https://github.com/musthytr/nexus.git
cd nexus
chmod +x nexus-installer.sh
./nexus-installer.sh
python3 nexus.py
```

## Uyarı

Bu yazılım `pacman` ve Arch Linux dosya yapısını kullanır. Debian, Ubuntu veya Fedora gibi sistemlerde **çalışmaz**.

## Lisans

MIT
