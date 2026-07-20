// web/app.js

document.addEventListener('DOMContentLoaded', () => {
    // ── CORE WEB CLIENT CONFIGURATION ──
    const host = window.location.host;
    const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const API_BASE = `${protocol}://${host}`;
    const WS_URL = `${wsProtocol}://${host}/ws`;

    // ── HTML DOM ELEMENT BINDINGS ──
    const networkLatencyEl = document.getElementById('network-latency');
    const backendSelector = document.getElementById('backendSelector');
    const connStatusEl = document.getElementById('conn-status');
    const systemTimeEl = document.getElementById('system-time');
    const osLabel = document.getElementById('os-label');
    const chatModeLabel = document.getElementById('chat-mode-label');

    // Gauges
    const cpuRing = document.getElementById('cpu-ring');
    const ramRing = document.getElementById('ram-ring');
    const diskRing = document.getElementById('disk-ring');
    const cpuValue = document.getElementById('cpu-value');
    const ramValue = document.getElementById('ram-value');
    const diskValue = document.getElementById('disk-value');

    // Tabs
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    // Memory Explorer
    const memoryListContainer = document.getElementById('memoryListContainer');
    const memorySearchInput = document.getElementById('memorySearchInput');
    const openAddMemoryModalBtn = document.getElementById('openAddMemoryModalBtn');
    const addMemoryModal = document.getElementById('addMemoryModal');
    const closeMemoryModalBtn = document.getElementById('closeMemoryModalBtn');
    const cancelMemoryModalBtn = document.getElementById('cancelMemoryModalBtn');
    const saveMemoryBtn = document.getElementById('saveMemoryBtn');
    const memNameInput = document.getElementById('memName');
    const memTypeSelect = document.getElementById('memType');
    const memDescInput = document.getElementById('memDesc');
    const memContentTextarea = document.getElementById('memContent');
    const memScopeSelect = document.getElementById('memScope');

    // Skills
    const skillsListContainer = document.getElementById('skillsListContainer');

    // Chat Dialog
    const chatWindow = document.getElementById('chatWindow');
    const chatInput = document.getElementById('chatInput');
    const sendChatBtn = document.getElementById('sendChatBtn');

    // Console logs
    const consoleLog = document.getElementById('consoleLog');
    const clearConsoleBtn = document.getElementById('clearConsoleBtn');

    // Task Queue
    const tasksList = document.getElementById('tasksList');

    let socket = null;
    let localMemories = [];
    let isWaitingForResponse = false;

    // ── GAUGE UTILS ──
    // Dasharray circumference is 2 * PI * r = 2 * 3.14159 * 40 = 251.2
    function setGauge(ring, textEl, value) {
        if (!ring || !textEl) return;
        const val = Math.min(100, Math.max(0, parseFloat(value) || 0));
        const offset = 251.2 - (251.2 * val) / 100;
        ring.style.strokeDashoffset = offset;
        textEl.textContent = `${Math.round(val)}%`;
    }

    // ── SYSTEM TIME ──
    function updateSystemTime() {
        const d = new Date();
        systemTimeEl.textContent = d.toLocaleTimeString();
    }
    setInterval(updateSystemTime, 1000);
    updateSystemTime();

    // ── TAB SWITCHER ──
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });

    // ── MEMORY MODAL ──
    openAddMemoryModalBtn.addEventListener('click', () => {
        addMemoryModal.style.display = 'flex';
        memNameInput.value = '';
        memDescInput.value = '';
        memContentTextarea.value = '';
    });

    const closeModal = () => { addMemoryModal.style.display = 'none'; };
    closeMemoryModalBtn.addEventListener('click', closeModal);
    cancelMemoryModalBtn.addEventListener('click', closeModal);

    // Save Memory
    saveMemoryBtn.addEventListener('click', async () => {
        const name = memNameInput.value.trim();
        const type = memTypeSelect.value;
        const desc = memDescInput.value.trim();
        const content = memContentTextarea.value.trim();
        const scope = memScopeSelect.value;

        if (!name || !content) {
            alert('Please specify both Name and Content for the memory cell.');
            return;
        }

        try {
            const res = await fetch(`${API_BASE}/api/memory`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, type, description: desc, content, scope })
            });
            if (res.ok) {
                appendLog(`[SYSTEM] Memory entry '${name}' saved successfully.`, 'sys');
                closeModal();
                loadMemories();
            } else {
                appendLog('[SYSTEM] Failed to write memory entry to storage cell.', 'err');
            }
        } catch (e) {
            appendLog(`[SYSTEM] Error communicating with memory store: ${e.message}`, 'err');
        }
    });

    // Load Memories
    async function loadMemories() {
        try {
            const res = await fetch(`${API_BASE}/api/memory`);
            if (res.ok) {
                const data = await res.json();
                localMemories = data.memories || [];
                renderMemories(localMemories);
            }
        } catch (e) {
            console.error('Error fetching memories', e);
        }
    }

    function renderMemories(memories) {
        memoryListContainer.innerHTML = '';
        if (memories.length === 0) {
            memoryListContainer.innerHTML = '<div class="no-tasks">No memory cells found in scope.</div>';
            return;
        }
        memories.forEach(m => {
            const div = document.createElement('div');
            div.className = 'memory-item';
            div.innerHTML = `
                <div class="title">
                    <span>${m.name}</span>
                    <span class="type-tag">${m.type}/${m.scope}</span>
                </div>
                <div class="desc">${m.description || m.content.substring(0, 50)}</div>
                <button class="delete-cell" title="Wipe Memory Cell">&times;</button>
            `;
            // Trigger deletion on click
            div.querySelector('.delete-cell').addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm(`Are you sure you want to wipe memory cell '${m.name}'?`)) {
                    deleteMemory(m.name, m.scope);
                }
            });
            // Click to populate chat
            div.addEventListener('click', () => {
                chatInput.value = `Tell me about the memory: ${m.name}`;
                chatInput.focus();
            });
            memoryListContainer.appendChild(div);
        });
    }

    async function deleteMemory(name, scope) {
        try {
            const res = await fetch(`${API_BASE}/api/memory/${encodeURIComponent(name)}?scope=${scope}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                appendLog(`[SYSTEM] Memory cell '${name}' wiped.`, 'sys');
                loadMemories();
            } else {
                appendLog(`[SYSTEM] Failed to wipe memory cell '${name}'.`, 'err');
            }
        } catch (e) {
            appendLog(`[SYSTEM] Delete communication error: ${e.message}`, 'err');
        }
    }

    // Filter Memories
    memorySearchInput.addEventListener('input', () => {
        const q = memorySearchInput.value.toLowerCase().trim();
        if (!q) {
            renderMemories(localMemories);
            return;
        }
        const filtered = localMemories.filter(m => 
            m.name.toLowerCase().includes(q) || 
            (m.description && m.description.toLowerCase().includes(q)) ||
            m.content.toLowerCase().includes(q)
        );
        renderMemories(filtered);
    });

    // ── LOAD SKILLS ──
    async function loadSkills() {
        try {
            const res = await fetch(`${API_BASE}/api/skills`);
            if (res.ok) {
                const skills = await res.json();
                renderSkills(skills);
            }
        } catch (e) {
            console.error('Error fetching skills', e);
        }
    }

    function renderSkills(skills) {
        skillsListContainer.innerHTML = '';
        if (skills.length === 0) {
            skillsListContainer.innerHTML = '<div class="no-tasks">No preloaded skills available.</div>';
            return;
        }
        skills.forEach(s => {
            const div = document.createElement('div');
            div.className = 'skill-item';
            const trigger = s.triggers && s.triggers.length > 0 ? s.triggers[0] : `/skill ${s.name}`;
            div.innerHTML = `
                <div class="name">
                    <span>${s.name}</span>
                    <span class="trigger-tag">${trigger}</span>
                </div>
                <div class="desc">${s.description}</div>
            `;
            div.addEventListener('click', () => {
                chatInput.value = `${trigger} `;
                chatInput.focus();
            });
            skillsListContainer.appendChild(div);
        });
    }

    // ── SYSTEM TELEMETRY ──
    async function fetchTelemetry() {
        const start = performance.now();
        try {
            const res = await fetch(`${API_BASE}/api/status`);
            if (res.ok) {
                const elapsed = Math.round(performance.now() - start);
                networkLatencyEl.textContent = `${elapsed}ms`;
                networkLatencyEl.className = 'val ' + (elapsed < 100 ? 'green' : elapsed < 250 ? 'orange' : 'red');

                const data = await res.json();
                setGauge(cpuRing, cpuValue, data.cpu);
                setGauge(ramRing, ramValue, data.ram);
                setGauge(diskRing, diskValue, data.disk);
                osLabel.textContent = `OS: ${data.os.toUpperCase()}`;
                chatModeLabel.textContent = `MODE: ${data.mode.toUpperCase()}`;
                
                // Keep dropdown selection updated
                if (data.backend && backendSelector.value !== data.backend) {
                    backendSelector.value = data.backend;
                }
            }
        } catch (e) {
            networkLatencyEl.textContent = 'TIMEOUT';
            networkLatencyEl.className = 'val red';
        }
    }
    setInterval(fetchTelemetry, 3000);
    fetchTelemetry();

    // Backend Selector Switching
    backendSelector.addEventListener('change', async () => {
        const selectBe = backendSelector.value;
        appendLog(`[SYSTEM] Initiating core swap to: ${selectBe.toUpperCase()}`, 'sys');
        try {
            const res = await fetch(`${API_BASE}/api/backend/switch`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ backend: selectBe })
            });
            if (res.ok) {
                const data = await res.json();
                appendLog(`[SYSTEM] Core swap successful: ${data.message}`, 'sys');
                fetchTelemetry();
            } else {
                const err = await res.json();
                appendLog(`[SYSTEM] Swap rejected: ${err.detail}`, 'err');
            }
        } catch (e) {
            appendLog(`[SYSTEM] Core swap communication error: ${e.message}`, 'err');
        }
    });

    // ── TASK PIPELINE STATUS ──
    async function fetchTasks() {
        try {
            const res = await fetch(`${API_BASE}/api/tasks`);
            if (res.ok) {
                const data = await res.json();
                renderTasks(data.tasks || []);
            }
        } catch (e) {
            console.error('Error fetching tasks', e);
        }
    }
    setInterval(fetchTasks, 2000);
    fetchTasks();

    function renderTasks(tasks) {
        tasksList.innerHTML = '';
        if (tasks.length === 0) {
            tasksList.innerHTML = '<div class="no-tasks">All concurrent worker pipes are currently idle.</div>';
            return;
        }
        tasks.forEach(t => {
            const card = document.createElement('div');
            card.className = `task-card ${t.status}`;
            card.innerHTML = `
                <div class="task-goal">${t.goal.substring(0, 45)}${t.goal.length > 45 ? '...' : ''}</div>
                <div class="task-meta">
                    <span class="lbl">ID: ${t.task_id.substring(0, 8)}</span>
                    <span class="val ${t.status === 'running' ? 'green' : t.status === 'completed' ? 'cyan' : 'red'}">${t.status.toUpperCase()}</span>
                </div>
            `;
            tasksList.appendChild(card);
        });
    }

    // ── CHAT DIALOG MODULE (STREAMING) ──
    async function handleChatSubmission() {
        const text = chatInput.value.trim();
        if (!text || isWaitingForResponse) return;

        chatInput.value = '';
        appendMessage('user', 'You', text);
        isWaitingForResponse = true;

        // Create initial assistant bubble
        const bubble = appendMessage('assistant', 'JARVIS', 'Connecting pipeline...');
        const textEl = bubble.querySelector('.msg-text');

        try {
            const streamUrl = `${API_BASE}/api/chat/stream?message=${encodeURIComponent(text)}`;
            const eventSource = new EventSource(streamUrl);

            let firstToken = true;

            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.error) {
                        textEl.textContent = `[Error: ${data.error}]`;
                        eventSource.close();
                        isWaitingForResponse = false;
                        return;
                    }
                    if (data.token) {
                        if (firstToken) {
                            textEl.innerHTML = '';
                            firstToken = false;
                        }
                        
                        // Parse tool indicators
                        if (data.token.includes('[JARVIS] 🔧')) {
                            textEl.innerHTML += `<div style="color: var(--color-cyan); font-family: var(--font-mono); font-size:11px; margin: 4px 0;">${data.token}</div>`;
                        } else if (data.token.includes('[Tool Result:')) {
                            textEl.innerHTML += `<div style="color: var(--color-green); font-family: var(--font-mono); font-size:11px; margin: 4px 0;">${data.token}</div>`;
                        } else {
                            // Normal token content - escape html and add
                            const cleanText = data.token
                                .replace(/&/g, "&amp;")
                                .replace(/</g, "&lt;")
                                .replace(/>/g, "&gt;");
                            textEl.innerHTML += cleanText;
                        }
                        chatWindow.scrollTop = chatWindow.scrollHeight;
                    }
                } catch (e) {
                    console.error('Error parsing SSE event data', e);
                }
            };

            eventSource.onerror = (err) => {
                eventSource.close();
                isWaitingForResponse = false;
                loadMemories(); // Refresh memory cells on chat completion
            };

        } catch (e) {
            textEl.textContent = `Error initiating data sync stream: ${e.message}`;
            isWaitingForResponse = false;
        }
    }

    sendChatBtn.addEventListener('click', handleChatSubmission);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleChatSubmission();
    });

    function appendMessage(role, sender, text) {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${role}`;
        
        // Convert backticks codeblock formatting if non-streaming
        let renderedText = text;
        if (role === 'assistant' && text.includes('```')) {
            renderedText = text.replace(/```(.*?)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
        }

        bubble.innerHTML = `
            <div class="sender">${sender.toUpperCase()}</div>
            <div class="msg-text">${renderedText}</div>
        `;
        chatWindow.appendChild(bubble);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        return bubble;
    }

    // ── CONSOLE LOGGER MODULE ──
    function appendLog(line, type = 'log') {
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        entry.textContent = `[${timestamp}] ${line}`;
        
        consoleLog.appendChild(entry);
        consoleLog.scrollTop = consoleLog.scrollHeight;
    }

    clearConsoleBtn.addEventListener('click', () => {
        consoleLog.innerHTML = '<div class="log-entry sys">[SYSTEM] Log interface flushed. Awaiting console broadcasts...</div>';
    });

    // ── WEBSOCKET LIVE SYNC (BROADCAST LOGS) ──
    function connectWS() {
        appendLog('[SYSTEM] Establishing live WebSocket feed...', 'sys');
        socket = new WebSocket(WS_URL);

        socket.onopen = () => {
            connStatusEl.textContent = 'ONLINE';
            connStatusEl.className = 'val green';
            appendLog('[SYSTEM] Live WebSocket feed online.', 'sys');
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'log') {
                    appendLog(data.message, 'log');
                } else if (data.type === 'response') {
                    appendMessage('assistant', 'JARVIS', data.message);
                } else if (data.type === 'error') {
                    appendMessage('assistant', 'JARVIS', `[Error: ${data.message}]`);
                }
            } catch (e) {
                appendLog(`[SYSTEM] Socket parse error: ${e.message}`, 'err');
            }
        };

        socket.onclose = () => {
            connStatusEl.textContent = 'OFFLINE';
            connStatusEl.className = 'val red';
            appendLog('[SYSTEM] WebSocket feed disconnected. Reconnecting in 5s...', 'err');
            setTimeout(connectWS, 5000);
        };

        socket.onerror = (err) => {
            socket.close();
        };
    }

    // Initialize Web App Components
    connectWS();
    loadMemories();
    loadSkills();
});
