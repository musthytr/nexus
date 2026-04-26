import gi
import http.server
import socketserver
import json
import os
import subprocess
import urllib.request
import threading
from urllib.parse import urlparse, parse_qs

try:
    gi.require_version('Gtk', '3.0')
    # Try 4.1 first, then 4.0
    try:
        gi.require_version('WebKit2', '4.1')
    except:
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
    print("HATA: Hiçbir terminal emülatörü bulunamadı!")

HTML_CONTENT = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nexus (Arch Linux)</title>
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
        .apps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-top: 24px; }
        .app-card { display: flex; flex-direction: column; gap: 16px; }
        .app-header { display: flex; gap: 16px; align-items: center; }
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
        let chatHistory = [];
        const views = {
            bridge: `
                <h1>Sürücü <span style="color: var(--accent-primary)">Kurulumu</span></h1>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 24px;">
                    <div class="glass-card m-card" onclick="installDrivers('nvidia')"><h3>NVIDIA</h3><p>nvidia & utils</p></div>
                    <div class="glass-card m-card" onclick="installDrivers('amd')"><h3>AMD</h3><p>mesa & radeon</p></div>
                    <div class="glass-card m-card" onclick="installDrivers('intel')"><h3>Intel</h3><p>mesa & intel</p></div>
                </div>
            `,
            hub: `
                <h1>Paket <span style="color: var(--accent-primary)">Merkezi</span></h1>
                <p>Pacman, AUR ve Flathub üzerinde arama yapın.</p>
                <div style="display:flex; gap:12px; margin-top: 20px;">
                    <input type="text" id="search-input" placeholder="Paket adı..." class="input-field" style="margin-bottom:0; flex:1;">
                    <button class="btn btn-primary" onclick="searchApps()">Ara</button>
                </div>
                <div id="results" class="apps-grid"></div>
            `,
            assistant: `
                <h1>AI <span style="color: var(--accent-secondary)">Asistanı</span></h1>
                <div class="chat-container">
                    <div class="chat-messages" id="chat-messages"></div>
                    <div class="chat-input-area">
                        <input type="text" id="chat-input" class="input-field" style="margin-bottom:0;" placeholder="Mesaj...">
                        <button class="btn btn-primary" onclick="sendChat()">Gönder</button>
                    </div>
                </div>
            `,
            maintenance: `
                <h1>Sistem <span style="color: var(--accent-success)">Bakımı</span></h1>
                <div class="maintenance-grid">
                    <div class="glass-card m-card" onclick="runMaintenance('update')"><h3>Güncelle</h3><p>Sistem ve Flatpak</p></div>
                    <div class="glass-card m-card" onclick="runMaintenance('clean')"><h3>Temizle</h3><p>Cache ve Yetimler</p></div>
                </div>
            `
        };

        function loadView(name) {
            document.getElementById('content').innerHTML = views[name];
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.querySelector(`.nav-item[data-view="${name}"]`).classList.add('active');
            if(name === 'hub') {
                document.getElementById('search-input').addEventListener('keypress', e => { if(e.key === 'Enter') searchApps(); });
            }
        }
        loadView('bridge');

        window.installDrivers = (gpu) => fetch('http://localhost:8080/api/install_driver', {method:'POST', body:JSON.stringify({gpu})});
        window.runMaintenance = (action) => fetch('http://localhost:8080/api/maintenance', {method:'POST', body:JSON.stringify({action})});
        
        window.searchApps = async () => {
            const q = document.getElementById('search-input').value;
            const res = await fetch(`http://localhost:8080/api/search?q=${encodeURIComponent(q)}`);
            const data = await res.json();
            let h = '';
            data.results.forEach(a => {
                const color = a.source === 'aur' ? 'var(--accent-warning)' : (a.source === 'pacman' ? 'var(--accent-success)' : 'var(--accent-primary)');
                h += `
                <div class="glass-card app-card">
                    <div style="display:flex; justify-content:space-between; align-items:start">
                        <h3>${a.name}</h3>
                        <span style="font-size:10px; padding:2px 6px; background:${color}; border-radius:4px; color:white">${a.source.toUpperCase()}</span>
                    </div>
                    <p style="font-size:13px; color:var(--text-secondary); flex:1">${a.summary}</p>
                    <button class="btn btn-primary" onclick="installApp('${a.source}','${a.id}')">Yükle</button>
                </div>`;
            });
            document.getElementById('results').innerHTML = h || '<p>Sonuç bulunamadı.</p>';
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
        elif parsed.path == '/api/search':
            qs = parse_qs(parsed.query)
            query = qs.get('q', [''])[0]
            results = []
            
            # 1. Pacman Search
            try:
                out = subprocess.check_output(['pacman', '-Ss', query], text=True)
                lines = out.splitlines()
                for i in range(0, len(lines), 2):
                    if i+1 < len(lines):
                        parts = lines[i].split('/')
                        repo = parts[0]
                        name_ver = parts[1].split(' ')
                        results.append({'source': 'pacman', 'id': name_ver[0], 'name': name_ver[0], 'summary': lines[i+1].strip()})
            except: pass

            # 2. AUR Search (yay)
            try:
                out = subprocess.check_output(['yay', '-Ss', '--color', 'never', query], text=True)
                lines = out.splitlines()
                for i in range(0, len(lines), 2):
                    if i+1 < len(lines):
                        if lines[i].startswith('aur/'):
                            name = lines[i].split('/')[1].split(' ')[0]
                            results.append({'source': 'aur', 'id': name, 'name': name, 'summary': lines[i+1].strip()})
            except: pass

            # 3. Flathub Search
            try:
                url = "https://flathub.org/api/v2/search"
                payload = json.dumps({"query": query}).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    for hit in data.get('hits', [])[:5]:
                        results.append({'source': 'flathub', 'id': hit['app_id'], 'name': hit['name'], 'summary': hit['summary']})
            except: pass

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"results": results[:30]}).encode('utf-8'))

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(content_length).decode('utf-8'))
        
        cmd = ""
        if parsed.path == '/api/install':
            if data['type'] == 'pacman': cmd = f"sudo pacman -S --noconfirm {data['pkg']}"
            elif data['type'] == 'aur': cmd = f"yay -S --noconfirm {data['pkg']}"
            else: cmd = f"flatpak install -y flathub {data['pkg']}"
        elif parsed.path == '/api/install_driver':
            if data['gpu'] == 'nvidia': cmd = "sudo pacman -S --noconfirm nvidia nvidia-utils"
            elif data['gpu'] == 'amd': cmd = "sudo pacman -S --noconfirm mesa vulkan-radeon"
            elif data['gpu'] == 'intel': cmd = "sudo pacman -S --noconfirm mesa vulkan-intel"
        elif parsed.path == '/api/maintenance':
            if data['action'] == 'update': cmd = "sudo pacman -Syu && flatpak update -y"
            elif data['action'] == 'clean': cmd = "sudo pacman -Scc --noconfirm && flatpak uninstall --unused -y"
            
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
        win = Gtk.Window(title="Nexus (Arch Linux)")
        win.set_default_size(1024, 768)
        win.connect("destroy", Gtk.main_quit)
        webview = WebKit2.WebView()
        webview.load_uri(f"http://localhost:{PORT}")
        win.add(webview)
        win.show_all()
        Gtk.main()
    except:
        import time
        while True: time.sleep(100)
