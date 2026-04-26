# Nexus Linux Interface

Nexus is a comprehensive desktop application for Linux, designed to provide a centralized hub for system maintenance, hardware driver installation, and application management.

## Features

- **Hardware Driver Bridge**: Easily install drivers for NVIDIA, AMD, and Intel GPUs.
- **Application Hub**: Search and install applications from Flatpak (Flathub) and AUR (Arch User Repositories).
- **AI Assistant**: Integrated AI assistant (OpenAI/Gemini) to help with system troubleshooting and Linux commands.
- **System Maintenance**: Perform system updates, clean junk files, and view system logs/info.
- **Modern UI**: A sleek, dark-themed interface built with HTML/CSS and WebKit.

## Installation

1. Ensure you have the necessary dependencies:
   - Python 3
   - GTK 3
   - WebKit2GTK
   - Git
   - Flatpak (optional)
   - yay (optional, for AUR support)

2. Clone the repository:
   ```bash
   git clone https://github.com/musthytr/nexus.git
   cd nexus
   ```

3. Run the application:
   ```bash
   python nexus.py
   ```

## Usage

- Launch the app to access the Hardware, Hub, Assistant, and Maintenance sections.
- For AI features, enter your API key in the Assistant settings.
- Most system operations will open an external terminal for secure authentication.

## License

MIT
