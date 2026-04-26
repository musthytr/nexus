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
    # WebKit2 sürüm uyumluluğu için farklı sürümleri dene
    try:
        gi.require_version('WebKit2', '4.1')
    except (ValueError, AttributeError, ImportError):
        try:
            gi.require_version('WebKit2', '4.0')
        except (ValueError, AttributeError, ImportError):
            print("Uyarı: WebKit2 4.0 veya 4.1 bulunamadı.")
            
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
    # Wrap command so terminal stays open after completion
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
    <title>Nexus</title>
    <script src="https://unpkg.com/@phosphor-icons/web"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap');
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
        .btn-primary:hover { opacity: 0.9; transform: translateY(-1px); }
        .btn-outline { background: transparent; border: 1px solid var(--border-color); color: var(--text-primary); }
        .btn-outline:hover { background: rgba(255,255,255,0.05); }
        
        .input-field { width: 100%; padding: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); background: rgba(0,0,0,0.2); color: white; font-size: 14px; outline: none; margin-bottom: 16px; }
        .select-field { width: 100%; padding: 12px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); background: rgba(0,0,0,0.2); color: white; font-size: 14px; outline: none; margin-bottom: 16px; appearance: none; }
        .select-field option { background: var(--bg-color); color: white; }
 
        .gpu-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 24px; }
        .gpu-card { text-align: center; cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 16px; }
        .gpu-card:hover { transform: translateY(-4px); background: rgba(255,255,255,0.1); }
        .gpu-icon { font-size: 48px; }
        
        .apps-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; margin-top: 24px; }
        .app-card { display: flex; flex-direction: column; gap: 16px; }
        .app-header { display: flex; gap: 16px; align-items: center; }
        .app-icon { width: 48px; height: 48px; border-radius: 12px; background: rgba(255,255,255,0.1); display: flex; align-items: center; justify-content: center; font-size: 24px; }
        .app-icon img { width: 100%; height: 100%; object-fit: contain; }
        .app-footer { margin-top: auto; }
        
        .checkbox-group { display: flex; gap: 20px; margin-bottom: 24px; }
        .checkbox-label { display: flex; align-items: center; gap: 8px; cursor: pointer; color: var(--text-secondary); }
        input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--accent-primary); }
 
        .chat-container { flex: 1; display: flex; flex-direction: column; background: rgba(0,0,0,0.2); border-radius: var(--radius-md); border: 1px solid var(--border-color); overflow: hidden; margin-top: 20px; }
        .chat-messages { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 16px; }
        .message { padding: 16px; border-radius: var(--radius-md); max-width: 80%; line-height: 1.5; font-size: 14px; }
        .message.user { background: rgba(59, 130, 246, 0.2); align-self: flex-end; border-bottom-right-radius: 4px; }
        .message.ai { background: rgba(255, 255, 255, 0.05); align-self: flex-start; border-bottom-left-radius: 4px; }
        .chat-input-area { display: flex; gap: 12px; padding: 16px; background: rgba(0,0,0,0.3); border-top: 1px solid var(--border-color); }
        
        .maintenance-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 24px; }
        .m-card { display: flex; flex-direction: column; gap: 12px; justify-content: center; align-items: center; text-align: center; cursor: pointer; }
        .m-card:hover { background: rgba(255,255,255,0.1); transform: translateY(-2px); }
        .m-icon { font-size: 40px; }
        
 
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
        let isArch = false;
        let chatHistory = [];
 
        const views = {
            bridge: `
                <h1 style="margin-bottom: 12px; font-size: 32px;">Sürücü <span style="color: var(--accent-primary)">Kurulumu</span></h1>
                <p style="color: var(--text-secondary); margin-bottom: 32px;">Sisteminizdeki ekran kartını seçin ve en iyi sürücüleri tek tuşla kurun.</p>
                <div class="gpu-grid">
                    <div class="glass-card gpu-card" onclick="installDrivers('nvidia')">
                        <i class="ph ph-graphics-card gpu-icon" style="color: #76b900;"></i>
                        <h3>NVIDIA</h3>
                        <p style="font-size: 14px; color: var(--text-muted)">Özel (Proprietary) sürücüler</p>
                    </div>
                    <div class="glass-card gpu-card" onclick="installDrivers('amd')">
                        <i class="ph ph-cpu gpu-icon" style="color: #ed1c24;"></i>
                        <h3>AMD Radeon</h3>
                        <p style="font-size: 14px; color: var(--text-muted)">Açık kaynak Mesa & Vulkan</p>
                    </div>
                    <div class="glass-card gpu-card" onclick="installDrivers('intel')">
                        <i class="ph ph-microchip gpu-icon" style="color: #0071c5;"></i>
                        <h3>Intel Graphics</h3>
                        <p style="font-size: 14px; color: var(--text-muted)">Açık kaynak Mesa sürücüleri</p>
                    </div>
                </div>
            `,
            hub: `
                <h1 style="margin-bottom: 12px; font-size: 32px;">Uygulama <span style="color: var(--accent-primary)">Merkezi</span></h1>
                <p style="color: var(--text-secondary); margin-bottom: 24px;">Aradığınız tüm uygulamalar tek bir yerde. Güvenle yükleyin.</p>
                
                <div id="arch-filters" class="checkbox-group" style="display: none;">
                    <label class="checkbox-label"><input type="checkbox" id="chk-flatpak" checked> Flatpak (Flathub)</label>
                    <label class="checkbox-label"><input type="checkbox" id="chk-aur" checked> AUR (Arch User Repos)</label>
                </div>
 
                <div style="display:flex; gap:12px; margin-bottom: 32px;">
                    <input type="text" id="search-input" placeholder="Uygulama ara (ör. firefox, gimp)..." class="input-field" style="margin-bottom:0; flex:1;">
                    <button class="btn btn-primary" onclick="searchApps()"><i class="ph ph-magnifying-glass"></i> Ara</button>
                </div>
                
                <div id="loading" style="display:none; text-align:center; padding:40px; color:var(--text-muted);">
                    <i class="ph ph-spinner ph-spin" style="font-size:32px;"></i><p style="margin-top:12px">Sonuçlar getiriliyor...</p>
                </div>
                <div id="results" class="apps-grid"></div>
            `,
 
            assistant: `
                <h1 style="margin-bottom: 12px; font-size: 32px;">Yapay Zeka <span style="color: var(--accent-secondary)">Asistanı</span></h1>
                <p style="color: var(--text-secondary); margin-bottom: 20px;">Bir API anahtarı girin ve doğrudan sisteminizden AI modellerine sorular sorun.</p>
                
                <div style="display: flex; gap: 16px;">
                    <div style="flex:1;">
                        <label style="font-size:12px; color:var(--text-muted); margin-bottom:4px; display:block">Sağlayıcı</label>
                        <select id="ai-provider" class="select-field" onchange="updateModels()">
                            <option value="openai">OpenAI (ChatGPT)</option>
                            <option value="gemini">Google (Gemini)</option>
                        </select>
                    </div>
                    <div style="flex:1;">
                        <label style="font-size:12px; color:var(--text-muted); margin-bottom:4px; display:block">Model</label>
                        <select id="ai-model" class="select-field">
                            <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                            <option value="gpt-4o">GPT-4o</option>
                        </select>
                    </div>
                    <div style="flex:2;">
                        <label style="font-size:12px; color:var(--text-muted); margin-bottom:4px; display:block">API Key (Gizli Tutulur)</label>
                        <input type="password" id="ai-key" class="input-field" placeholder="sk-..." onchange="saveKey()">
                    </div>
                </div>
 
                <div class="chat-container">
                    <div class="chat-messages" id="chat-messages">
                        <div class="message ai">Merhaba! Ben Nexus Asistanı. Ayarlardan API anahtarını girdikten sonra bana istediğinizi sorabilirsiniz. Linux komutlarında, sorun çözmede veya herhangi bir konuda yardımcı olabilirim.</div>
                    </div>
                    <div class="chat-input-area">
                        <input type="text" id="chat-input" class="input-field" style="margin-bottom:0;" placeholder="Mesajınızı yazın...">
                        <button class="btn btn-primary" onclick="sendChat()"><i class="ph ph-paper-plane-right"></i> Gönder</button>
                    </div>
                </div>
            `,
            maintenance: `
                <h1 style="margin-bottom: 12px; font-size: 32px;">Sistem <span style="color: var(--accent-success)">Bakımı</span></h1>
                <p style="color: var(--text-secondary); margin-bottom: 20px;">Sisteminizi güncelleyin ve gereksiz dosyalardan temizleyerek hızlandırın.</p>
                
                <div class="maintenance-grid">
                    <div class="glass-card m-card" onclick="runMaintenance('update')">
                        <i class="ph ph-arrows-clockwise m-icon" style="color: var(--accent-primary)"></i>
                        <h3>Sistemi Güncelle</h3>
                        <p style="font-size:13px; color:var(--text-muted)">Tüm uygulama ve paketleri son sürüme yükseltir.</p>
                    </div>
                    <div class="glass-card m-card" onclick="runMaintenance('clean')">
                        <i class="ph ph-broom m-icon" style="color: var(--accent-warning)"></i>
                        <h3>Çöpleri Temizle</h3>
                        <p style="font-size:13px; color:var(--text-muted)">Kullanılmayan paketleri ve eski önbellek dosyalarını siler.</p>
                    </div>
                    <div class="glass-card m-card" onclick="runMaintenance('info')">
                        <i class="ph ph-info m-icon" style="color: var(--accent-secondary)"></i>
                        <h3>Sistem Bilgisi Göster</h3>
                        <p style="font-size:13px; color:var(--text-muted)">Detaylı donanım ve yazılım bilgilerinizi konsola yazar.</p>
                    </div>
                    <div class="glass-card m-card" onclick="runMaintenance('logs')">
                        <i class="ph ph-scroll m-icon" style="color: var(--accent-danger)"></i>
                        <h3>Hata Kayıtları (Logs)</h3>
                        <p style="font-size:13px; color:var(--text-muted)">Sistem hatalarını (journalctl) konsol üzerinden inceler.</p>
                    </div>
                </div>
            `
        };
 
        function loadView(name) {
            document.getElementById('content').innerHTML = views[name];
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.querySelector(`.nav-item[data-view="${name}"]`).classList.add('active');
            
            if(name === 'hub') {
                if(isArch) document.getElementById('arch-filters').style.display = 'flex';
                const inp = document.getElementById('search-input');
                if(inp) {
                    inp.addEventListener('keypress', e => { if(e.key === 'Enter') searchApps(); });
                    inp.focus();
                }
            } else if(name === 'assistant') {
                const c = document.getElementById('chat-messages');
                if(chatHistory.length > 0) {
                    c.innerHTML = '';
                    chatHistory.forEach(m => {
                        c.innerHTML += `<div class="message ${m.role === 'user' ? 'user' : 'ai'}">${m.text.replace(/\\n/g, '<br>')}</div>`;
                    });
                    c.scrollTop = c.scrollHeight;
                }
                const inp = document.getElementById('chat-input');
                if(inp) inp.addEventListener('keypress', e => { if(e.key === 'Enter') sendChat(); });
                const savedKey = localStorage.getItem('nexus_ai_key');
                if(savedKey) document.getElementById('ai-key').value = savedKey;
            }
        }
 
        fetch('http://localhost:8080/api/system').then(r => r.json()).then(data => {
            if(data.distro === 'arch' || data.distro === 'manjaro' || data.id_like.includes('arch') || data.distro === 'cachyos') {
                isArch = true;
            }
            loadView('bridge');
        });
 
        window.installDrivers = function(gpu) {
            fetch('http://localhost:8080/api/install_driver', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({gpu: gpu})
            });
        };
 
        window.runMaintenance = function(action) {
            fetch('http://localhost:8080/api/maintenance', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({action})
            });
        };
 
        window.searchApps = async function() {
            const query = document.getElementById('search-input').value.trim();
            if(!query) return;
            let useFlatpak = true, useAur = false;
            if (isArch) {
                useFlatpak = document.getElementById('chk-flatpak').checked;
                useAur = document.getElementById('chk-aur').checked;
            }
            document.getElementById('results').innerHTML = '';
            document.getElementById('loading').style.display = 'block';
            
            try {
                const res = await fetch(`http://localhost:8080/api/search?q=${encodeURIComponent(query)}&flatpak=${useFlatpak}&aur=${useAur}`);
                const data = await res.json();
                let html = '';
                data.results.forEach(app => {
                    const isAur = app.source === 'aur';
                    const srcClass = isAur ? 'var(--accent-warning)' : 'var(--accent-primary)';
                    const srcBg = isAur ? 'rgba(245, 158, 11, 0.1)' : 'rgba(59, 130, 246, 0.1)';
                    const iconHtml = isAur ? 
                        `<div class="app-icon" style="color:var(--accent-warning)"><i class="ph ph-package"></i></div>` : 
                        `<div class="app-icon"><img src="${app.icon}" onerror="this.src='https://flathub.org/assets/flathub-logo.svg'"></div>`;
 
                    html += `
                    <div class="glass-card app-card">
                        <div class="app-header">
                            ${iconHtml}
                            <div style="overflow:hidden">
                                <h3 style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${app.name}">${app.name}</h3>
                                <span style="color:${srcClass};font-size:11px;padding:2px 6px;background:${srcBg};border-radius:4px">${isAur ? 'AUR' : 'Flathub'}</span>
                            </div>
                        </div>
                        <p style="font-size:13px;color:var(--text-secondary);flex:1;overflow:hidden;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical">${app.summary}</p>
                        <div class="app-footer">
                            <button class="btn btn-primary" style="width:100%;background:${isAur ? 'var(--accent-warning)' : ''}" onclick="installApp('${app.source}', '${app.id}')">
                                <i class="ph ph-download-simple"></i> Yükle
                            </button>
                        </div>
                    </div>`;
                });
                
                document.getElementById('loading').style.display = 'none';
                document.getElementById('results').innerHTML = html || '<p style="grid-column:1/-1;text-align:center;color:var(--text-muted)">Sonuç bulunamadı.</p>';
            } catch(e) {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('results').innerHTML = `<p style="grid-column:1/-1;text-align:center;color:#ef4444">Hata: ${e.message}</p>`;
            }
        };
 
        window.installApp = function(type, id) {
            fetch('http://localhost:8080/api/install', {
                method: 'POST',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({type, pkg: id})
            });
        };
 
        window.updateModels = function() {
            const provider = document.getElementById('ai-provider').value;
            const modelSelect = document.getElementById('ai-model');
            if(provider === 'openai') {
                modelSelect.innerHTML = `<option value="gpt-3.5-turbo">GPT-3.5 Turbo</option><option value="gpt-4o">GPT-4o</option>`;
            } else if(provider === 'gemini') {
                modelSelect.innerHTML = `<option value="gemini-3-flash-preview">Gemini 3 Flash Preview</option><option value="gemini-3.0-pro">Gemini 3.0 Pro</option>`;
            }
        };
 
        window.saveKey = function() {
            localStorage.setItem('nexus_ai_key', document.getElementById('ai-key').value);
        };
 
        window.sendChat = async function() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if(!text) return;
            
            const key = document.getElementById('ai-key').value;
            if(!key) {
                alert("Lütfen önce API anahtarınızı girin.");
                return;
            }
 
            const provider = document.getElementById('ai-provider').value;
            const model = document.getElementById('ai-model').value;
            const messagesDiv = document.getElementById('chat-messages');
            
            chatHistory.push({role: 'user', text: text});
            messagesDiv.innerHTML += `<div class="message user">${text}</div>`;
            input.value = '';
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
 
            const loadingId = 'msg-' + Date.now();
            messagesDiv.innerHTML += `<div class="message ai" id="${loadingId}"><i class="ph ph-spinner ph-spin"></i> Düşünüyor...</div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
 
            try {
                const res = await fetch('http://localhost:8080/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({ provider, model, key, message: text })
                });
                const data = await res.json();
                
                document.getElementById(loadingId).remove();
                
                if(data.error) {
                    messagesDiv.innerHTML += `<div class="message ai" style="color:var(--accent-danger)">Hata: ${data.error}</div>`;
                } else {
                    chatHistory.push({role: 'ai', text: data.reply});
                    messagesDiv.innerHTML += `<div class="message ai">${data.reply.replace(/\\n/g, '<br>')}</div>`;
                }
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            } catch(e) {
                document.getElementById(loadingId).remove();
                messagesDiv.innerHTML += `<div class="message ai" style="color:var(--accent-danger)">Bağlantı Hatası: ${e.message}</div>`;
            }
        };
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
            return
        elif parsed.path == '/api/system':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_system_info()).encode('utf-8'))
            return
 
        elif parsed.path == '/api/search':
            qs = parse_qs(parsed.query)
            query = qs.get('q', [''])[0]
            use_flatpak = qs.get('flatpak', ['true'])[0] == 'true'
            use_aur = qs.get('aur', ['false'])[0] == 'true'
            
            results = []
            
            if use_flatpak:
                try:
                    url = "https://flathub.org/api/v2/search"
                    payload = json.dumps({"query": query}).encode('utf-8')
                    req = urllib.request.Request(url, data=payload, headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}, method='POST')
                    with urllib.request.urlopen(req) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        for hit in data.get('hits', [])[:10]:
                            results.append({
                                'source': 'flathub',
                                'id': hit.get('app_id', ''),
                                'name': hit.get('name', ''),
                                'summary': hit.get('summary', ''),
                                'icon': hit.get('iconDesktopUrl') or 'https://flathub.org/assets/flathub-logo.svg'
                            })
                except Exception as e: print("Flathub err:", e)
                
            if use_aur:
                try:
                    url = f"https://aur.archlinux.org/rpc/?v=5&type=search&arg={urllib.parse.quote(query)}"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        for hit in data.get('results', [])[:10]:
                            results.append({
                                'source': 'aur',
                                'id': hit.get('Name', ''),
                                'name': hit.get('Name', ''),
                                'summary': hit.get('Description', ''),
                                'icon': ''
                            })
                except Exception as e: print("AUR err:", e)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"results": results}).encode('utf-8'))
            return
            
        self.send_response(404)
        self.end_headers()
 
    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        if parsed.path == '/api/install':
            data = json.loads(post_data.decode('utf-8'))
            pkg_type = data.get('type')
            pkg_name = data.get('pkg')
            if pkg_type in ['flatpak', 'flathub']:
                cmd = f"flatpak install -y flathub {pkg_name}"
            elif pkg_type == 'aur':
                cmd = f"yay --sudoflags '-S' -S --noconfirm {pkg_name}"
            launch_external_terminal(cmd)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"success":true}')
            return
            
        elif parsed.path == '/api/install_driver':
            data = json.loads(post_data.decode('utf-8'))
            gpu = data.get('gpu')
            sys_info = get_system_info()
            is_arch = sys_info['distro'] in ['arch', 'manjaro', 'cachyos'] or 'arch' in sys_info['id_like']
            is_fedora = sys_info['distro'] == 'fedora' or 'fedora' in sys_info['id_like']
            is_debian = sys_info['distro'] in ['debian', 'ubuntu', 'linuxmint', 'pop'] or 'debian' in sys_info['id_like']
            
            cmd = "echo 'OS not supported for auto driver install'"
            if is_arch:
                if gpu == 'nvidia': cmd = "sudo pacman -S --noconfirm nvidia nvidia-utils"
                elif gpu == 'amd': cmd = "sudo pacman -S --noconfirm mesa vulkan-radeon xf86-video-amdgpu"
                elif gpu == 'intel': cmd = "sudo pacman -S --noconfirm mesa vulkan-intel"
            elif is_fedora:
                if gpu == 'nvidia': cmd = "sudo dnf install -y akmod-nvidia xorg-x11-drv-nvidia-cuda"
                elif gpu == 'amd': cmd = "sudo dnf install -y mesa-dri-drivers mesa-vulkan-drivers xorg-x11-drv-amdgpu"
                elif gpu == 'intel': cmd = "sudo dnf install -y mesa-dri-drivers mesa-vulkan-drivers"
            elif is_debian:
                if gpu == 'nvidia': cmd = "sudo ubuntu-drivers autoinstall || sudo apt install -y nvidia-driver"
                elif gpu == 'amd': cmd = "sudo apt install -y mesa-vulkan-drivers xserver-xorg-video-amdgpu"
                elif gpu == 'intel': cmd = "sudo apt install -y mesa-vulkan-drivers"
                
            launch_external_terminal(cmd)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"success":true}')
            return
 
        elif parsed.path == '/api/chat':
            data = json.loads(post_data.decode('utf-8'))
            provider = data.get('provider')
            model = data.get('model')
            key = data.get('key')
            message = data.get('message')
            
            reply = ""
            error = ""
            
            try:
                if provider == 'openai':
                    url = "https://api.openai.com/v1/chat/completions"
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {key}"
                    }
                    payload = {
                        "model": model,
                        "messages": [{"role": "user", "content": message}]
                    }
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                    with urllib.request.urlopen(req) as res:
                        resp_data = json.loads(res.read().decode('utf-8'))
                        reply = resp_data['choices'][0]['message']['content']
                        
                elif provider == 'gemini':
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                    headers = {"Content-Type": "application/json"}
                    payload = {
                        "contents": [{"parts": [{"text": message}]}]
                    }
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
                    with urllib.request.urlopen(req) as res:
                        resp_data = json.loads(res.read().decode('utf-8'))
                        reply = resp_data['candidates'][0]['content']['parts'][0]['text']
            except urllib.error.HTTPError as e:
                error = f"API Error: {e.code} - {e.reason}"
            except Exception as e:
                error = str(e)
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            if error:
                self.wfile.write(json.dumps({"error": error}).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({"reply": reply}).encode('utf-8'))
            return
 
        elif parsed.path == '/api/maintenance':
            data = json.loads(post_data.decode('utf-8'))
            action = data.get('action')
            sys_info = get_system_info()
            is_arch = sys_info['distro'] in ['arch', 'manjaro', 'cachyos'] or 'arch' in sys_info['id_like']
            is_fedora = sys_info['distro'] == 'fedora' or 'fedora' in sys_info['id_like']
            is_debian = sys_info['distro'] in ['debian', 'ubuntu', 'linuxmint', 'pop'] or 'debian' in sys_info['id_like']
            
            cmd = ""
            if action == 'update':
                if is_arch:
                    cmd = "sudo pacman -Syu && sudo flatpak update -y"
                elif is_fedora:
                    cmd = "sudo dnf upgrade -y && sudo flatpak update -y"
                elif is_debian:
                    cmd = "sudo apt update && sudo apt upgrade -y && sudo flatpak update -y"
            elif action == 'clean':
                if is_arch:
                    cmd = "sudo pacman -Scc --noconfirm && sudo paccache -r && flatpak uninstall --unused -y"
                elif is_fedora:
                    cmd = "sudo dnf clean all && flatpak uninstall --unused -y"
                elif is_debian:
                    cmd = "sudo apt autoremove -y && sudo apt clean && flatpak uninstall --unused -y"
            elif action == 'info':
                cmd = "if command -v neofetch &> /dev/null; then neofetch; elif command -v fastfetch &> /dev/null; then fastfetch; else uname -a && lscpu | grep 'Model name' && free -h; fi"
            elif action == 'logs':
                cmd = "journalctl -p 3 -xb"
                
            if cmd:
                launch_external_terminal(cmd)
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"success":true}')
            return
            
        self.send_response(404)
        self.end_headers()
 
def start_server():
    with socketserver.TCPServer(("", PORT), NexusHandler) as httpd:
        httpd.serve_forever()
 
if __name__ == '__main__':
    # Start background server
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    
    # Start GTK Window
    try:
        win = Gtk.Window(title="Nexus Masaüstü")
        win.set_default_size(1024, 768)
        win.connect("destroy", Gtk.main_quit)
        
        webview = WebKit2.WebView()
        webview.load_uri(f"http://localhost:{PORT}")
        
        win.add(webview)
        win.show_all()
        Gtk.main()
    except Exception as e:
        print("GUI could not be started:", e)
        # Keep server running if GUI fails
        import time
        while True: time.sleep(100)
