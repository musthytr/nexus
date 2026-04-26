import gi
import http.server
import socketserver
import json
import os
import subprocess
import urllib.request
import threading
from urllib.parse import urlparse, parse_qs

# Arch Linux için özel olarak yapılandırılmıştır
try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('WebKit2', '4.0')
    from gi.repository import Gtk, WebKit2, GLib
except ImportError:
    pass

PORT = 8080

def get_system_info():
    distro_id = "unknown"
    id_like = ""
    if os.path.exists('/etc/os-release'):
        with open('/etc/os-release') as f:
            for line in f:
                if line.startswith('ID='): distro_id = line.strip().split('=')[1].strip('"').strip("'")
                elif line.startswith('ID_LIKE='): id_like = line.strip().split('=')[1].strip('"').strip("'")
    return {"distro": distro_id, "id_like": id_like}

def launch_external_terminal(cmd):
    """Open a system terminal window to run the given command.
    The user can interactively enter sudo password in the terminal.
    """
    wrapped = f'{cmd}; echo "\n\n[İşlem tamamlandı. Kapatmak için bir tuşa basın.]"; read -n1'
    
    terminals = [
        ['kitty', '--', 'bash', '-c', wrapped],
        ['alacritty', '-e', 'bash', '-c', wrapped],
        ['konsole', '-e', 'bash', '-c', wrapped],
        ['gnome-terminal', '--', 'bash', '-c', wrapped],
        ['xfce4-terminal', '-e', f'bash -c "{wrapped}"'],
        ['xterm', '-e', f'bash -c "{wrapped}"'],
    ]
    
    for term_cmd in terminals:
        try:
            subprocess.Popen(term_cmd)
            return
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"Terminal error ({term_cmd[0]}): {e}")
            continue
    
    print("HATA: Hiçbir terminal emülatörü bulunamadı!")

HTML_CONTENT = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-width=1.0">
    <title>Nexus (Arch Only)</title>
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        :root {
            --bg-color: #0f172a;
            --surface-color: rgba(30, 41, 59, 0.7);
            --border-color: rgba(255, 255, 255, 0.1);
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #64748b;
            --accent-primary: #3b82f6;
            --accent-secondary: #8b5cf6;
            --accent-success: #10b981;
            --accent-warning: #f59e0b;
            --accent-danger: #ef4444;
            --radius-md: 16px;
            --radius-sm: 8px;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }
        body { background: var(--bg-color); color: var(--text-primary); height: 100vh; display: flex; overflow: hidden; }
        .sidebar { width: 240px; background: rgba(15, 23, 42, 0.9); border-right: 1px solid var(--border-color); padding: 24px; display: flex; flex-direction: column; gap: 8px; z-index: 10; }
        .logo { font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 12px; margin-bottom: 32px; }
        .logo i { color: var(--accent-primary); }
        .nav-item { padding: 12px 16px; border-radius: var(--radius-sm); cursor: pointer; display: flex; align-items: center; gap: 12px; color: var(--text-secondary); transition: all 0.2s; }
        .nav-item:hover, .nav-item.active { background: rgba(255, 255, 255, 0.05); color: var(--text-primary); }
        .nav-item.active i { color: var(--accent-primary); }
        .main-content { flex: 1; padding: 40px; overflow-y: auto; display: flex; flex-direction: column; position: relative; }
        .glass-card { background: var(--surface-color); backdrop-filter: blur(12px); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 24px; transition: transform 0.2s; }
        .btn { padding: 10px 20px; border-radius: var(--radius-sm); border: none; font-weight: 500; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 8px; transition: all 0.2s; color: white; }
        .btn-primary { background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)); }
        .input-field { width: 100%; padding: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); background: rgba(0,0,0,0.2); color: white; outline: none; margin-bottom: 16px; }
        .select-field { width: 100%; padding: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); background: rgba(0,0,0,0.2); color: white; outline: none; margin-bottom: 16px; }
        .apps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-top: 24px; }
        .app-card { display: flex; flex-direction: column; gap: 16px; }
        .app-header { display: flex; gap: 16px; align-items: center; }
        .app-icon { width: 48px; height: 48px; border-radius: 12px; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 24px; }
        .chat-container { flex: 1; display: flex; flex-direction: column; background: rgba(0,0,0,0.2); border-radius: var(--radius-md); border: 1px solid var(--border-color); overflow: hidden; margin-top: 20px; }
        .chat-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
        .message { padding: 16px; border-radius: var(--radius-md); max-width: 80%; line-height: 1.5; font-size: 14px; }
        .message.user { background: rgba(59, 130, 246, 0.2); align-self: flex-end; }
        .message.ai { background: rgba(255, 255, 255, 0.05); align-self: flex-start; }
        .chat-input-area { display: flex; gap: 12px; padding: 16px; background: rgba(0,0,0,0.3); border-top: 1px solid var(--border-color); }
        .maintenance-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px; }
        .m-card { display: flex; flex-direction: column; gap: 12px; justify-content: center; align-items: center; text-align: center; cursor: pointer; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="logo"><i class="ph-fill ph-planet"></i> Nexus</div>
        <div class="nav-item active" onclick="loadView('bridge')" data-view="bridge"><i class="ph ph-cpu"></i> Donanım</div>
        <div class="nav-item" onclick="loadView('hub')" data-view="hub"><i class="ph ph-storefront"></i> Merkez</div>
        <div class="nav-item" onclick="loadView('assistant')" data-view="assistant"><i class="ph ph-robot"></i> Asistan</div>
        <div class="nav-item" onclick="loadView('maintenance')" data-view="maintenance"><i class="ph ph-wrench"></i> Sistem Bakımı</div>
    </div>
    <div class="main-content" id="content"></div>

    <script>
        let isArch = true; // Sadece Arch odaklı
        let chatHistory = [];
        const views = {
            bridge: `
                <h1>Sürücü <span style="color: var(--accent-primary)">Kurulumu</span> (Arch Linux)</h1>
                <p>Ekran kartı sürücülerini pacman üzerinden kurun.</p>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 24px;">
                    <div class="glass-card m-card" onclick="installDrivers('nvidia')"><h3>NVIDIA</h3><p>nvidia & nvidia-utils</p></div>
                    <div class="glass-card m-card" onclick="installDrivers('amd')"><h3>AMD</h3><p>mesa & vulkan-radeon</p></div>
                    <div class="glass-card m-card" onclick="installDrivers('intel')"><h3>Intel</h3><p>mesa & vulkan-intel</p></div>
                </div>
            `,
            hub: `
                <h1>Uygulama <span style="color: var(--accent-primary)">Merkezi</span></h1>
                <div class="checkbox-group" style="display:flex; gap:20px; margin-bottom:20px;">
                    <label><input type="checkbox" id="chk-flatpak" checked> Flatpak</label>
                    <label><input type="checkbox" id="chk-aur" checked> AUR (yay)</label>
                </div>
                <div style="display:flex; gap:12px; margin-bottom: 32px;">
                    <input type="text" id="search-input" placeholder="Uygulama ara..." class="input-field" style="margin-bottom:0; flex:1;">
                    <button class="btn btn-primary" onclick="searchApps()">Ara</button>
                </div>
                <div id="results" class="apps-grid"></div>
            `,
            assistant: `
                <h1>AI <span style="color: var(--accent-secondary)">Asistanı</span></h1>
                <input type="password" id="ai-key" class="input-field" placeholder="API Key" onchange="saveKey()">
                <div class="chat-container">
                    <div class="chat-messages" id="chat-messages"></div>
                    <div class="chat-input-area">
                        <input type="text" id="chat-input" class="input-field" style="margin-bottom:0;" placeholder="Mesajınızı yazın...">
                        <button class="btn btn-primary" onclick="sendChat()">Gönder</button>
                    </div>
                </div>
            `,
            maintenance: `
                <h1>Sistem <span style="color: var(--accent-success)">Bakımı</span></h1>
                <div class="maintenance-grid">
                    <div class="glass-card m-card" onclick="runMaintenance('update')"><h3>Güncelle</h3><p>pacman -Syu</p></div>
                    <div class="glass-card m-card" onclick="runMaintenance('clean')"><h3>Temizle</h3><p>paccache & orphans</p></div>
                </div>
            `
        };

        function loadView(name) {
            document.getElementById('content').innerHTML = views[name];
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.querySelector(`.nav-item[data-view="${name}"]`).classList.add('active');
        }
        loadView('bridge');

        window.installDrivers = (gpu) => fetch('http://localhost:8080/api/install_driver', {method:'POST', body:JSON.stringify({gpu})});
        window.runMaintenance = (action) => fetch('http://localhost:8080/api/maintenance', {method:'POST', body:JSON.stringify({action})});
        window.searchApps = async () => {
            const q = document.getElementById('search-input').value;
            const res = await fetch(`http://localhost:8080/api/search?q=${q}&flatpak=true&aur=true`);
            const data = await res.json();
            let h = '';
            data.results.forEach(a => {
                h += `<div class="glass-card app-card"><h3>${a.name}</h3><p>${a.summary}</p><button class="btn btn-primary" onclick="installApp('${a.source}','${a.id}')">Yükle</button></div>`;
            });
            document.getElementById('results').innerHTML = h;
        };
        window.installApp = (type, id) => fetch('http://localhost:8080/api/install', {method:'POST', body:JSON.stringify({type, pkg:id})});
    </script>
</body>
</html>"""

class NexusHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode('utf-8'))
        elif parsed.path == '/api/system':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_system_info()).encode('utf-8'))
        elif parsed.path == '/api/search':
            qs = parse_qs(parsed.query)
            query = qs.get('q', [''])[0]
            results = []
            # Flathub & AUR RPC (Basitleştirilmiş)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"results": []}).encode('utf-8'))

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        cmd = ""
        if parsed.path == '/api/install':
            if data['type'] == 'aur': cmd = f"yay -S --noconfirm {data['pkg']}"
            else: cmd = f"flatpak install -y flathub {data['pkg']}"
        elif parsed.path == '/api/install_driver':
            if data['gpu'] == 'nvidia': cmd = "sudo pacman -S --noconfirm nvidia nvidia-utils"
            elif data['gpu'] == 'amd': cmd = "sudo pacman -S --noconfirm mesa vulkan-radeon"
            elif data['gpu'] == 'intel': cmd = "sudo pacman -S --noconfirm mesa vulkan-intel"
        elif parsed.path == '/api/maintenance':
            if data['action'] == 'update': cmd = "sudo pacman -Syu"
            elif data['action'] == 'clean': cmd = "sudo pacman -Scc && sudo pacman -Rns $(pacman -Qtdq)"
            
        if cmd: launch_external_terminal(cmd)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"success":true}')

def start_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), NexusHandler) as httpd:
        httpd.serve_forever()

if __name__ == '__main__':
    threading.Thread(target=start_server, daemon=True).start()
    try:
        win = Gtk.Window(title="Nexus (Arch Linux Only)")
        win.set_default_size(1024, 768)
        win.connect("destroy", Gtk.main_quit)
        webview = WebKit2.WebView()
        webview.load_uri(f"http://localhost:{PORT}")
        win.add(webview)
        win.show_all()
        Gtk.main()
    except Exception as e:
        print(e)
        while True: threading.Event().wait(100)
