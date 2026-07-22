// web/app.js — BR JARVIS AI Desktop Operating System Client

document.addEventListener('DOMContentLoaded', () => {
    const host = window.location.host;
    const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const API_BASE = `${protocol}://${host}`;
    const WS_URL = `${wsProtocol}://${host}/ws`;

    // DOM Elements
    const networkLatencyEl = document.getElementById('network-latency');
    const backendSelector = document.getElementById('backendSelector');
    const roleSelector = document.getElementById('roleSelector');
    const systemTimeEl = document.getElementById('system-time');

    const navItems = document.querySelectorAll('.nav-item');
    const viewContainers = document.querySelectorAll('.view-container');

    const chatWindow = document.getElementById('chatWindow');
    const chatInput = document.getElementById('chatInput');
    const sendChatBtn = document.getElementById('sendChatBtn');
    const inputRoleChip = document.getElementById('inputRoleChip');
    const activeRoleBadge = document.getElementById('activeRoleBadge');

    const consoleLog = document.getElementById('consoleLog');
    const clearConsoleBtn = document.getElementById('clearConsoleBtn');

    // Gauges
    const cpuRing = document.getElementById('cpu-ring');
    const ramRing = document.getElementById('ram-ring');
    const diskRing = document.getElementById('disk-ring');
    const cpuValue = document.getElementById('cpu-value');
    const ramValue = document.getElementById('ram-value');
    const diskValue = document.getElementById('disk-value');

    // Command Palette
    const cmdPaletteTrigger = document.getElementById('cmdPaletteTrigger');
    const cmdPaletteModal = document.getElementById('cmdPaletteModal');
    const cmdPaletteInput = document.getElementById('cmdPaletteInput');
    const cmdPaletteResults = document.getElementById('cmdPaletteResults');

    // Modals
    const screenCastModal = document.getElementById('screenCastModal');
    const addMemoryModal = document.getElementById('addMemoryModal');

    let socket = null;
    let isVoiceActive = false;

    // ── SYSTEM TIME ──
    function updateSystemTime() {
        if (systemTimeEl) {
            systemTimeEl.textContent = new Date().toLocaleTimeString();
        }
    }
    setInterval(updateSystemTime, 1000);
    updateSystemTime();

    // ── GAUGE UPDATES ──
    function setGauge(ring, textEl, value) {
        if (!ring || !textEl) return;
        const val = Math.min(100, Math.max(0, parseFloat(value) || 0));
        const offset = 251.2 - (251.2 * val) / 100;
        ring.style.strokeDashoffset = offset;
        textEl.textContent = `${Math.round(val)}%`;
    }

    // ── VIEW SWITCHER ──
    window.switchView = function(viewId) {
        navItems.forEach(item => {
            if (item.dataset.view === viewId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        viewContainers.forEach(container => {
            if (container.id === viewId) {
                container.classList.add('active');
            } else {
                container.classList.remove('active');
            }
        });
    };

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const viewId = item.dataset.view;
            if (viewId) switchView(viewId);
        });
    });

    // ── ROLE PERSONA SWITCHER ──
    if (roleSelector) {
        roleSelector.addEventListener('change', (e) => {
            const role = e.target.value.toUpperCase();
            if (activeRoleBadge) activeRoleBadge.textContent = `ROLE: ${role}`;
            if (inputRoleChip) inputRoleChip.textContent = `ROLE: ${role}`;
            appendLog(`[ROLE] Persona switched to ${role}`, 'sys');
        });
    }

    // ── COMMAND PALETTE (Ctrl + K) ──
    window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            toggleCmdPalette();
        }
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });

    if (cmdPaletteTrigger) {
        cmdPaletteTrigger.addEventListener('click', toggleCmdPalette);
    }

    function toggleCmdPalette() {
        if (cmdPaletteModal) {
            cmdPaletteModal.classList.toggle('active');
            if (cmdPaletteModal.classList.contains('active') && cmdPaletteInput) {
                cmdPaletteInput.focus();
                cmdPaletteInput.value = '';
            }
        }
    }

    function closeAllModals() {
        document.querySelectorAll('.modal').forEach(m => m.classList.remove('active'));
    }

    window.executePaletteCommand = function(cmd) {
        closeAllModals();
        if (cmd.startsWith('view:')) {
            switchView(cmd.split(':')[1]);
        } else if (cmd.startsWith('cmd:')) {
            executeQuickCommand(cmd.split(':')[1]);
        } else if (cmd.startsWith('model:')) {
            if (backendSelector) {
                backendSelector.value = cmd.split(':')[1];
                backendSelector.dispatchEvent(new Event('change'));
            }
        } else if (cmd.startsWith('role:')) {
            if (roleSelector) roleSelector.value = cmd.split(':')[1];
        }
    };

    // ── QUICK COMMAND EXECUTION ──
    window.executeQuickCommand = function(text) {
        switchView('chatView');
        if (chatInput) {
            chatInput.value = text;
            transmitChat();
        }
    };

    // ── SCREEN SHARE MODAL ──
    window.openScreenShareModal = function() {
        if (screenCastModal) screenCastModal.classList.add('active');
    };

    window.closeScreenShareModal = function() {
        if (screenCastModal) screenCastModal.classList.remove('active');
    };

    window.confirmScreenCast = function() {
        closeScreenShareModal();
        appendLog('[SCREEN_CAST] Sharing active window / entire screen with Live Vision Engine...', 'sys');
        switchView('voiceView');
    };

    // ── WEBSOCKET CONNECTION ──
    function initWebSocket() {
        try {
            socket = new WebSocket(WS_URL);

            socket.onopen = () => {
                appendLog('[SYSTEM] WebSocket Neural Link Connected', 'sys');
                fetchTelemetry();
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleServerMessage(data);
                } catch (e) {
                    appendLog(event.data, 'log');
                }
            };

            socket.onclose = () => {
                appendLog('[SYSTEM] WebSocket Connection Lost — Reconnecting...', 'err');
                setTimeout(initWebSocket, 3000);
            };
        } catch (e) {
            console.error('WebSocket Init Error:', e);
        }
    }

    function handleServerMessage(data) {
        if (data.type === 'telemetry') {
            if (data.cpu !== undefined) setGauge(cpuRing, cpuValue, data.cpu);
            if (data.ram !== undefined) setGauge(ramRing, ramValue, data.ram);
            if (data.disk !== undefined) setGauge(diskRing, diskValue, data.disk);
        } else if (data.type === 'stream_chunk') {
            appendChatStreamChunk(data.text);
        } else if (data.type === 'chat_response') {
            appendChatMessage('JARVIS', data.response, 'system');
        } else if (data.type === 'log') {
            appendLog(data.message, 'log');
        }
    }

    // ── CHAT TRANSMISSION ──
    function transmitChat() {
        if (!chatInput) return;
        const text = chatInput.value.strip ? chatInput.value.strip() : chatInput.value.trim();
        if (!text) return;

        appendChatMessage('User', text, 'user');
        chatInput.value = '';

        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'chat_prompt',
                prompt: text,
                backend: backendSelector ? backendSelector.value : 'gemini',
                role: roleSelector ? roleSelector.value : 'general'
            }));
        } else {
            // REST Fallback
            fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt: text })
            })
            .then(res => res.json())
            .then(data => {
                appendChatMessage('JARVIS', data.response || data.result, 'system');
            })
            .catch(err => {
                appendChatMessage('JARVIS', `Error: ${err}`, 'system');
            });
        }
    }

    if (sendChatBtn) {
        sendChatBtn.addEventListener('click', transmitChat);
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') transmitChat();
        });
    }

    function appendChatMessage(author, text, type) {
        if (!chatWindow) return;
        const bubble = document.createElement('div');
        bubble.className = `msg-bubble ${type}`;
        bubble.innerHTML = `
            <div class="msg-author">${author}</div>
            <div class="msg-body">${formatMarkdown(text)}</div>
        `;
        chatWindow.appendChild(bubble);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        // Format code blocks
        escaped = escaped.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        // Format inline code
        escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Format bold
        escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        return escaped.replace(/\n/g, '<br>');
    }

    function appendLog(msg, type = 'sys') {
        if (!consoleLog) return;
        const line = document.createElement('div');
        line.className = `log-line ${type}`;
        line.textContent = msg;
        consoleLog.appendChild(line);
        consoleLog.scrollTop = consoleLog.scrollHeight;
    }

    if (clearConsoleBtn) {
        clearConsoleBtn.addEventListener('click', () => {
            if (consoleLog) consoleLog.innerHTML = '';
        });
    }

    // ── TELEMETRY FETCHING ──
    function fetchTelemetry() {
        fetch(`${API_BASE}/health`)
        .then(res => res.json())
        .then(data => {
            if (data.cpu_percent !== undefined) setGauge(cpuRing, cpuValue, data.cpu_percent);
            if (data.memory_percent !== undefined) setGauge(ramRing, ramValue, data.memory_percent);
            if (data.disk_percent !== undefined) setGauge(diskRing, diskValue, data.disk_percent);
        })
        .catch(() => {});
    }

    // ── HTML5 DYNAMIC PARTICLE ENGINE ──
    function initParticleCanvas() {
        const cvs = document.getElementById('particleCanvas');
        if (!cvs) return;
        const ctx = cvs.getContext('2d');
        let width = cvs.width = window.innerWidth;
        let height = cvs.height = window.innerHeight;

        window.addEventListener('resize', () => {
            width = cvs.width = window.innerWidth;
            height = cvs.height = window.innerHeight;
        });

        const particles = [];
        const particleCount = Math.min(45, Math.floor(width / 30));

        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                radius: Math.random() * 2 + 1,
                color: Math.random() > 0.5 ? 'rgba(0, 242, 254, ' : 'rgba(121, 40, 202, '
            });
        }

        function render() {
            ctx.clearRect(0, 0, width, height);

            for (let i = 0; i < particles.length; i++) {
                const p = particles[i];
                p.x += p.vx;
                p.y += p.vy;

                if (p.x < 0 || p.x > width) p.vx *= -1;
                if (p.y < 0 || p.y > height) p.vy *= -1;

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
                ctx.fillStyle = p.color + '0.6)';
                ctx.fill();

                // Draw connecting laser lines between nearby particles
                for (let j = i + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    const dx = p.x - p2.x;
                    const dy = p.y - p2.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    if (dist < 130) {
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.strokeStyle = p.color + (1 - dist / 130) * 0.15 + ')';
                        ctx.lineWidth = 0.8;
                        ctx.stroke();
                    }
                }
            }

            requestAnimationFrame(render);
        }

        requestAnimationFrame(render);
    }

    // ── CONNECTORS & SKILLS DYNAMIC LOADERS ──
    function fetchConnectors() {
        fetch(`${API_BASE}/api/connectors`)
            .then(res => res.json())
            .then(data => {
                const grid = document.getElementById('connectorsGrid');
                if (!grid || !data.connectors) return;
                grid.innerHTML = data.connectors.map(c => `
                    <div class="connector-card">
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                            <span style="font-size: 24px;">${c.icon}</span>
                            <span class="status-badge connected">${c.status}</span>
                        </div>
                        <h4 style="margin: 4px 0; font-family: var(--font-heading); color: #fff;">${c.name}</h4>
                        <p style="font-size: 12px; color: var(--text-muted); margin-bottom: 10px;">${c.desc}</p>
                        <div style="font-size: 11px; color: var(--accent-cyan); font-family: monospace;">
                            ${c.tools.join(', ')}
                        </div>
                    </div>
                `).join('');
            })
            .catch(() => {});
    }

    function fetchSkills() {
        fetch(`${API_BASE}/api/skills`)
            .then(res => res.json())
            .then(skills => {
                const grid = document.getElementById('skillsGrid');
                if (!grid || !Array.isArray(skills)) return;
                grid.innerHTML = skills.map(s => `
                    <div class="skill-card">
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <h4 style="margin: 0; color: var(--accent-purple); font-family: var(--font-heading);">${s.name}</h4>
                            <span class="status-badge" style="background: rgba(121, 40, 202, 0.2); color: #00f2fe;">Built-in</span>
                        </div>
                        <p style="font-size: 12px; color: var(--text-muted); margin: 8px 0;">${s.description}</p>
                        <div style="font-size: 11px; color: var(--text-main); font-family: monospace;">
                            Triggers: ${s.triggers.join(', ')}
                        </div>
                    </div>
                `).join('');
            })
            .catch(() => {});
    }

    // ── DYNAMIC BACKEND MODEL SELECTOR & SYNCHRONIZER ──
    function initBackendModelSelector() {
        if (!backendSelector) return;

        function syncModels() {
            fetch(`${API_BASE}/api/models`)
                .then(res => res.json())
                .then(models => {
                    const options = [];
                    let defaultVal = 'gemini';
                    
                    for (const [key, details] of Object.entries(models)) {
                        const opt = document.createElement('option');
                        opt.value = key;
                        opt.textContent = `${details.name} (${details.model})`;
                        if (details.is_default) {
                            opt.selected = true;
                            defaultVal = key;
                        }
                        options.push(opt);
                    }
                    
                    if (options.length > 0) {
                        backendSelector.innerHTML = '';
                        options.forEach(opt => backendSelector.appendChild(opt));
                        backendSelector.value = defaultVal;
                    }
                    appendLog('[SYSTEM] Loaded active AI model backends from server', 'sys');
                })
                .catch(err => {
                    console.warn('Failed to load dynamic model list, using fallback options', err);
                });
        }

        // Load initially
        syncModels();

        // Listen for user change and switch backend on the server
        backendSelector.addEventListener('change', (e) => {
            const selectedBackend = e.target.value;
            appendLog(`[SYSTEM] Switching backend to ${selectedBackend.toUpperCase()}...`, 'sys');
            
            fetch(`${API_BASE}/api/backend/switch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ backend: selectedBackend })
            })
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                appendLog(`[SYSTEM] ${data.message || 'Successfully switched default backend.'}`, 'sys');
            })
            .catch(err => {
                appendLog(`[SYSTEM] Failed to switch backend: ${err.message}`, 'err');
                syncModels();
            });
        });
    }

    initBackendModelSelector();
    fetchConnectors();
    fetchSkills();

    initParticleCanvas();
    setInterval(fetchTelemetry, 5000);
    initWebSocket();

    // Register PWA Service Worker for multi-platform support
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/web/sw.js')
                .then((reg) => console.log('[PWA] ServiceWorker registered with scope:', reg.scope))
                .catch((err) => console.warn('[PWA] ServiceWorker registration failed:', err));
        });
    }
});
