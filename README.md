# Nexus Linux Interface

Nexus is a comprehensive desktop application for Linux, designed to provide a centralized hub for system maintenance, hardware driver installation, and application management.

## Features

- **Hardware Driver Bridge**: Easily install drivers for NVIDIA, AMD, and Intel GPUs.
- **Application Hub**: Search and install applications from Flatpak (Flathub) and AUR (Arch User Repositories).
- **AI Assistant**: Integrated AI assistant (OpenAI/Gemini) to help with system troubleshooting and Linux commands.
- **System Maintenance**: Perform system updates, clean junk files, and view system logs/info.
- **Modern UI**: A sleek, dark-themed interface built with HTML/CSS and WebKit.

## Installation

En hızlı ve kolay kurulum için terminale şu komutu yapıştırın:

```bash
curl -sSL https://raw.githubusercontent.com/musthytr/nexus/master/nexus-installer.sh | bash
```

### Manuel Kurulum

1. Depoyu klonlayın:
   ```bash
   git clone https://github.com/musthytr/nexus.git
   cd nexus
   ```

2. Yükleyiciyi çalıştırın:
   ```bash
   chmod +x nexus-installer.sh
   ./nexus-installer.sh
   ```

3. Uygulamayı başlatın:
   ```bash
   python3 nexus.py
   ```

## Usage

- Launch the app to access the Hardware, Hub, Assistant, and Maintenance sections.
- For AI features, enter your API key in the Assistant settings.
- Most system operations will open an external terminal for secure authentication.

## License

MIT
