"""
JARVIS MK37 — Neural Holographic Interface (v2.0)
Complete UI redesign: holographic HUD with real-time monitors,
neural network visualization, voice waveform, command history,
agent status panel, and full-system integration.
"""
from __future__ import annotations

import os, json, time, math, random, threading, platform, subprocess, colorsys
import tkinter as tk
from tkinter import ttk
from collections import deque
from pathlib import Path
import sys

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageEnhance
    _PIL = True
except ImportError:
    _PIL = False

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

# ── Base paths ────────────────────────────────────────────────────────────────
def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

BASE_DIR   = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
API_FILE   = CONFIG_DIR / "api_keys.json"

# ── Identity ──────────────────────────────────────────────────────────────────
SYSTEM_NAME = "B.R"
MODEL_BADGE = "BR NEURAL CORE v4.0 — edge-tts Neural Voice"

# ── Holographic Color Palette ─────────────────────────────────────────────────
C = {
    "bg":       "#000508",
    "bg2":      "#00080f",
    "panel":    "#010c14",
    "border":   "#0a3d5c",
    "pri":      "#00e5ff",
    "pri2":     "#00b8d9",
    "mid":      "#006680",
    "dim":      "#002a3a",
    "dimmer":   "#001520",
    "acc":      "#ff6d00",
    "acc2":     "#ffd600",
    "acc3":     "#76ff03",
    "text":     "#b2ebf2",
    "text2":    "#4dd0e1",
    "muted":    "#ff1744",
    "success":  "#00e676",
    "warn":     "#ff9100",
    "error":    "#ff1744",
    "neural":   "#1a237e",
    "think":    "#aa00ff",
    "speak":    "#00e5ff",
    "listen":   "#00e676",
}


class NeuralNode:
    """A node in the background neural network visualization."""
    __slots__ = ["x", "y", "vx", "vy", "r", "pulse", "phase"]
    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.1, 0.4)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.r  = random.uniform(1.5, 3.5)
        self.pulse = random.uniform(0, 2 * math.pi)
        self.phase = random.uniform(0, 2 * math.pi)

    def update(self, w, h):
        self.x = (self.x + self.vx) % w
        self.y = (self.y + self.vy) % h
        self.pulse += 0.03


class HexGrid:
    """Pre-computed hex grid coordinates for the background."""
    def __init__(self, w, h, size=32):
        self.cells = []
        s = size
        col_w = s * 1.732
        row_h = s * 1.5
        for row in range(int(h / row_h) + 2):
            for col in range(int(w / col_w) + 2):
                cx = col * col_w + (s * 0.866 if row % 2 else 0)
                cy = row * row_h
                self.cells.append((cx, cy))

    def poly(self, cx, cy, size):
        pts = []
        for i in range(6):
            a = math.radians(60 * i - 30)
            pts.extend([cx + size * math.cos(a), cy + size * math.sin(a)])
        return pts


class JarvisUI:
    def __init__(self, face_path, size=None):
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S — MARK XXXVII  Neural Core")
        self.root.resizable(True, True)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        W  = min(sw, 1280)
        H  = min(sh,  880)
        self.root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.root.configure(bg=C["bg"])
        self.root.minsize(900, 680)

        self.W = W
        self.H = H

        # ── State ─────────────────────────────────────────────────────────
        self.speaking      = False
        self.muted         = False
        self.scale         = 1.0
        self.target_scale  = 1.0
        self.halo_alpha    = 60.0
        self.target_halo   = 60.0
        self.last_t        = time.time()
        self.tick          = 0
        self.scan_a1       = 0.0
        self.scan_a2       = 180.0
        self.rings_spin    = [0.0, 120.0, 240.0]
        self.pulse_rings   = []
        self.status_text   = "INITIALISING"
        self.status_blink  = True
        self._state        = "INITIALISING"
        self._prev_state   = ""

        # Voice waveform
        self._wave_data    = [0.0] * 80
        self._wave_smooth  = [0.0] * 80

        # Neural nodes
        self._nodes        = [NeuralNode(W, H) for _ in range(55)]
        self._hex_grid     = HexGrid(W, H, 28)

        # System metrics
        self._cpu          = 0.0
        self._ram          = 0.0
        self._net_s        = 0
        self._net_r        = 0
        self._gpu_temp     = None
        self._sys_tick     = 0
        self._agent_tasks  = {}

        # Command history
        self._cmd_history  = deque(maxlen=50)
        self._hist_idx     = -1
        self._log_entries  = deque(maxlen=200)

        # Callbacks
        self.on_text_command = None

        # Face
        self._face_pil         = None
        self._face_cache       = None
        self._has_face         = False
        self.FACE_SZ           = min(int(H * 0.42), 320)
        self.FCX               = int(W * 0.38)
        self.FCY               = int(H * 0.42)
        self._load_face(face_path)

        # ── Layout ────────────────────────────────────────────────────────
        self._build_layout()
        self._build_input_bar()
        self._build_hotkey_bar()

        # ── Timers ────────────────────────────────────────────────────────
        self.root.bind("<Configure>", self._on_resize)
        self.root.bind("<F4>", lambda e: self._toggle_mute())
        self.root.bind("<F5>", lambda e: self.set_state("LISTENING"))
        self.root.bind("<Escape>", lambda e: self._input_entry.focus_set())

        self._api_key_ready = self._api_keys_exist()
        if not self._api_key_ready:
            self.root.after(200, self._show_setup_ui)

        self._start_sys_monitor()
        self._animate()
        self.root.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))

    # ── Layout builders ────────────────────────────────────────────────────

    def _build_layout(self):
        W, H = self.W, self.H

        # Main canvas (background + face area)
        self.bg = tk.Canvas(self.root, width=W, height=H,
                            bg=C["bg"], highlightthickness=0)
        self.bg.place(x=0, y=0)

        # Right panel (monitors + log)
        self._build_right_panel()

    def _build_right_panel(self):
        W, H = self.W, self.H
        PW = int(W * 0.34)          # panel width
        PX = W - PW - 8
        PY = 72

        # Panel frame
        self.panel_frame = tk.Frame(
            self.root, bg=C["panel"],
            highlightbackground=C["border"],
            highlightthickness=1
        )
        self.panel_frame.place(x=PX, y=PY, width=PW, height=H - PY - 90)

        # System metrics sub-canvas
        self.metrics_canvas = tk.Canvas(
            self.panel_frame, bg=C["panel"],
            highlightthickness=0, height=110
        )
        self.metrics_canvas.pack(fill="x", padx=0, pady=0)

        # Separator
        tk.Frame(self.panel_frame, bg=C["border"], height=1).pack(fill="x")

        # Agent status
        self.agent_canvas = tk.Canvas(
            self.panel_frame, bg=C["panel"],
            highlightthickness=0, height=64
        )
        self.agent_canvas.pack(fill="x")
        tk.Frame(self.panel_frame, bg=C["border"], height=1).pack(fill="x")

        # Log area label
        log_header = tk.Frame(self.panel_frame, bg=C["panel"])
        log_header.pack(fill="x", padx=8, pady=(4, 0))
        tk.Label(log_header, text="◈ NEURAL LOG", fg=C["mid"], bg=C["panel"],
                 font=("Consolas", 8, "bold")).pack(side="left")
        self._log_count_var = tk.StringVar(value="0 entries")
        tk.Label(log_header, textvariable=self._log_count_var,
                 fg=C["dim"], bg=C["panel"],
                 font=("Consolas", 7)).pack(side="right")

        # Log text
        log_cont = tk.Frame(self.panel_frame, bg=C["panel"])
        log_cont.pack(fill="both", expand=True, padx=2, pady=(2, 4))
        scroll = tk.Scrollbar(log_cont, orient="vertical",
                               bg=C["bg2"], troughcolor=C["bg"],
                               activebackground=C["mid"])
        self.log_text = tk.Text(
            log_cont,
            fg=C["text"], bg=C["panel"],
            insertbackground=C["pri"],
            borderwidth=0, wrap="word",
            font=("Consolas", 9), padx=6, pady=4,
            yscrollcommand=scroll.set,
            state="disabled", cursor="arrow"
        )
        scroll.config(command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.pack(side="left", fill="both", expand=True)

        self.log_text.tag_config("you",  foreground="#e0e0e0", font=("Consolas", 9, "bold"))
        self.log_text.tag_config("ai",   foreground=C["pri"],  font=("Consolas", 9))
        self.log_text.tag_config("sys",  foreground=C["acc2"], font=("Consolas", 8))
        self.log_text.tag_config("err",  foreground=C["error"],font=("Consolas", 9, "bold"))
        self.log_text.tag_config("tool", foreground=C["acc3"], font=("Consolas", 8))
        self.log_text.tag_config("time", foreground=C["dim"],  font=("Consolas", 7))

    def _build_input_bar(self):
        W, H = self.W, self.H
        PW   = int(W * 0.34)
        bar_y = H - 86
        bar_x = 8
        bar_w = W - PW - 32

        # Input container
        inp_frame = tk.Frame(self.root, bg=C["bg2"],
                             highlightbackground=C["border"],
                             highlightthickness=1)
        inp_frame.place(x=bar_x, y=bar_y, width=bar_w, height=38)

        # Prompt label
        tk.Label(inp_frame, text="▸", fg=C["pri"], bg=C["bg2"],
                 font=("Consolas", 12, "bold")).pack(side="left", padx=(10, 2))

        self._input_var = tk.StringVar()
        self._input_entry = tk.Entry(
            inp_frame,
            textvariable=self._input_var,
            fg=C["text"], bg=C["bg2"],
            insertbackground=C["pri"],
            borderwidth=0, font=("Consolas", 10),
            highlightthickness=0,
        )
        self._input_entry.pack(side="left", fill="both", expand=True, padx=6)
        self._input_entry.bind("<Return>",   self._on_input_submit)
        self._input_entry.bind("<KP_Enter>", self._on_input_submit)
        self._input_entry.bind("<Up>",       self._hist_prev)
        self._input_entry.bind("<Down>",     self._hist_next)
        self._input_entry.bind("<Tab>",      self._autocomplete)

        # Highlight container border on focus
        def on_focus_in(e):
            inp_frame.config(highlightbackground=C["pri"])
        def on_focus_out(e):
            inp_frame.config(highlightbackground=C["border"])
        self._input_entry.bind("<FocusIn>", on_focus_in)
        self._input_entry.bind("<FocusOut>", on_focus_out)

        # Char counter
        self._charcount_var = tk.StringVar(value="0")
        tk.Label(inp_frame, textvariable=self._charcount_var,
                 fg=C["dim"], bg=C["bg2"], font=("Consolas", 8), width=4
                 ).pack(side="right", padx=6)
        self._input_var.trace_add("write", self._update_charcount)

        # Send button
        send_btn = tk.Button(
            self.root, text="SEND ▸", command=self._on_input_submit,
            fg=C["bg"], bg=C["pri"],
            activeforeground=C["bg"], activebackground=C["pri2"],
            font=("Consolas", 10, "bold"), borderwidth=0, cursor="hand2",
            relief="flat"
        )
        send_btn.place(x=bar_x + bar_w + 4, y=bar_y, width=72, height=38)

        # Hover effects for Send button
        def on_btn_enter(e):
            send_btn.config(bg=C["pri2"])
        def on_btn_leave(e):
            send_btn.config(bg=C["pri"])
        send_btn.bind("<Enter>", on_btn_enter)
        send_btn.bind("<Leave>", on_btn_leave)

    def _build_hotkey_bar(self):
        W, H = self.W, self.H
        keys = [
            ("[F4] MUTE", C["muted"]),
            ("[F5] RESET", C["mid"]),
            ("[ESC] FOCUS", C["dim"]),
            ("[↑↓] HISTORY", C["dim"]),
        ]
        hbar = tk.Frame(self.root, bg=C["bg"])
        hbar.place(x=8, y=H - 42, width=W - 16, height=20)
        for label, color in keys:
            tk.Label(hbar, text=label, fg=color, bg=C["bg"],
                     font=("Consolas", 8)).pack(side="left", padx=6)

    # ── System monitoring ──────────────────────────────────────────────────

    def _start_sys_monitor(self):
        def _monitor_loop():
            while True:
                try:
                    if _PSUTIL:
                        self._cpu = psutil.cpu_percent(interval=0.5)
                        self._ram = psutil.virtual_memory().percent
                        net = psutil.net_io_counters()
                        self._net_s = net.bytes_sent
                        self._net_r = net.bytes_recv
                except Exception:
                    pass
                time.sleep(1.5)
        threading.Thread(target=_monitor_loop, daemon=True).start()

    # ── Animation loop ─────────────────────────────────────────────────────

    def _animate(self):
        self.tick += 1
        t   = self.tick
        now = time.time()

        # Target updates
        interval = 0.12 if self.speaking else 0.52
        if now - self.last_t > interval:
            if self.speaking:
                self.target_scale = random.uniform(1.06, 1.12)
                self.target_halo  = random.uniform(150, 200)
            elif self.muted:
                self.target_scale = random.uniform(0.997, 1.002)
                self.target_halo  = random.uniform(15, 30)
            elif self._state == "THINKING":
                self.target_scale = random.uniform(1.002, 1.008)
                self.target_halo  = random.uniform(40, 80)
            else:
                self.target_scale = random.uniform(1.001, 1.006)
                self.target_halo  = random.uniform(55, 75)
            self.last_t = now

        sp = 0.38 if self.speaking else 0.18
        self.scale     += (self.target_scale - self.scale)     * sp
        self.halo_alpha += (self.target_halo   - self.halo_alpha) * sp

        # Ring spins
        spin_speeds = [1.4, -0.9, 2.1] if self.speaking else [0.6, -0.35, 0.9]
        for i, spd in enumerate(spin_speeds):
            self.rings_spin[i] = (self.rings_spin[i] + spd) % 360

        # Scan lines
        s1_spd = 3.2 if self.speaking else 1.4
        s2_spd = -2.1 if self.speaking else -0.75
        self.scan_a1 = (self.scan_a1 + s1_spd) % 360
        self.scan_a2 = (self.scan_a2 + s2_spd) % 360

        # Pulse rings
        pspd  = 4.5 if self.speaking else 2.2
        limit = self.FACE_SZ * 0.76
        self.pulse_rings = [r + pspd for r in self.pulse_rings if r + pspd < limit]
        if len(self.pulse_rings) < 4 and random.random() < (0.07 if self.speaking else 0.025):
            self.pulse_rings.append(0.0)

        # Neural nodes
        for node in self._nodes:
            node.update(self.W, self.H)

        # Voice waveform
        self._update_waveform()

        # Blink
        if t % 36 == 0:
            self.status_blink = not self.status_blink

        # Redraw
        self._draw_frame()

        # Metrics every 3 frames
        if t % 3 == 0:
            self._draw_metrics()
        if t % 5 == 0:
            self._draw_agent_status()

        self.root.after(16, self._animate)

    def _update_waveform(self):
        if self.speaking:
            for i in range(len(self._wave_data)):
                self._wave_data[i] = random.gauss(0, 0.55)
        elif self._state == "THINKING":
            t = self.tick * 0.08
            for i in range(len(self._wave_data)):
                self._wave_data[i] = 0.25 * math.sin(t + i * 0.25) * math.sin(t * 0.3)
        else:
            for i in range(len(self._wave_data)):
                self._wave_data[i] *= 0.85
        for i in range(len(self._wave_smooth)):
            self._wave_smooth[i] += (self._wave_data[i] - self._wave_smooth[i]) * 0.35

    # ── Draw helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _hex_color(r, g, b, a=255):
        f = max(0, min(255, a)) / 255.0
        return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

    @staticmethod
    def _alpha_blend(hex_col, alpha):
        """Apply alpha to a #rrggbb string."""
        h = hex_col.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        f = max(0, min(1.0, alpha / 255.0))
        return f"#{int(r*f):02x}{int(g*f):02x}{int(b*f):02x}"

    def _draw_frame(self):
        c = self.bg
        W, H = self.W, self.H
        c.delete("all")

        # 1. Hex grid background
        self._draw_hex_bg(c)

        # 2. Neural network edges
        self._draw_neural_edges(c)

        # 3. Neural nodes
        self._draw_neural_nodes(c)

        # 4. Face halo + rings
        self._draw_face_halo(c)

        # 5. Face image
        self._draw_face(c)

        # 6. Scan lines
        self._draw_scan_lines(c)

        # 7. Corner brackets (HUD frame)
        self._draw_hud_frame(c, W, H)

        # 8. Header bar
        self._draw_header(c, W)

        # 9. Status area
        self._draw_status_area(c, W, H)

        # 10. Voice waveform
        self._draw_waveform(c, W, H)

        # 11. Sidebar vertical divider
        PW = int(W * 0.34)
        PX = W - PW - 8
        c.create_line(PX - 1, 72, PX - 1, H - 88,
                      fill=C["border"], width=1, dash=(4, 6))

    def _draw_hex_bg(self, c):
        W, H = self.W, self.H
        t = self.tick * 0.003
        for cx, cy in self._hex_grid.cells:
            d = math.hypot(cx - self.FCX, cy - self.FCY)
            pulse = 0.5 + 0.5 * math.sin(t * 0.8 - d * 0.018)
            alpha = max(0, min(255, int(8 * pulse)))
            if alpha < 2:
                continue
            size = 26
            pts  = []
            for i in range(6):
                a = math.radians(60 * i - 30)
                pts.extend([cx + size * math.cos(a), cy + size * math.sin(a)])
            col = self._hex_color(0, int(18 * pulse), int(35 * pulse), alpha)
            c.create_polygon(pts, outline=col, fill="", width=1)

    def _draw_neural_edges(self, c):
        nodes = self._nodes
        conn_dist = 120
        for i, n1 in enumerate(nodes):
            for n2 in nodes[i+1:]:
                dx = n1.x - n2.x
                dy = n1.y - n2.y
                d  = math.sqrt(dx*dx + dy*dy)
                if d < conn_dist:
                    alpha = int(45 * (1.0 - d / conn_dist))
                    if alpha < 3:
                        continue
                    if self.speaking:
                        col = self._hex_color(0, 200, 255, alpha)
                    elif self._state == "THINKING":
                        col = self._hex_color(140, 0, 255, alpha)
                    else:
                        col = self._hex_color(0, 80, 130, alpha)
                    c.create_line(n1.x, n1.y, n2.x, n2.y,
                                  fill=col, width=1)

    def _draw_neural_nodes(self, c):
        for node in self._nodes:
            p = 0.5 + 0.5 * math.sin(node.pulse)
            r = node.r * (1.0 + 0.4 * p)
            a = int(80 + 120 * p)
            if self.speaking:
                col = self._hex_color(0, 220, 255, a)
            elif self._state == "THINKING":
                col = self._hex_color(160, 0, 255, a)
            else:
                col = self._hex_color(0, 100, 160, a)
            c.create_oval(node.x - r, node.y - r,
                          node.x + r, node.y + r,
                          fill=col, outline="")

    def _draw_face_halo(self, c):
        FCX, FCY = self.FCX, self.FCY
        FW = self.FACE_SZ
        ha = self.halo_alpha

        # Outer glow rings
        for i, r in enumerate(range(int(FW * 0.56), int(FW * 0.30), -20)):
            frac = 1.0 - (r - FW * 0.30) / (FW * 0.26)
            ga   = max(0, min(255, int(ha * 0.10 * frac)))
            if self.muted:
                col = self._hex_color(255, 20, 80, ga)
            elif self._state == "THINKING":
                col = self._hex_color(160, 0, 255, ga)
            else:
                col = self._hex_color(0, 200, 255, ga)
            c.create_oval(FCX-r, FCY-r, FCX+r, FCY+r,
                          outline=col, width=2, fill="")

        # Pulse rings
        for pr in self.pulse_rings:
            pa  = max(0, int(200 * (1.0 - pr / (FW * 0.76))))
            ri  = int(pr)
            if self.muted:
                col = self._hex_color(255, 30, 80, pa // 3)
            else:
                col = self._hex_color(0, 220, 255, pa)
            c.create_oval(FCX-ri, FCY-ri, FCX+ri, FCY+ri,
                          outline=col, width=2, fill="")

        # Spinning arc rings
        ring_specs = [(0.48, 3, 115, 70), (0.40, 2, 80, 52), (0.33, 1, 58, 40)]
        for idx, (r_frac, w_ring, arc_l, gap) in enumerate(ring_specs):
            ring_r = int(FW * r_frac)
            base_a = self.rings_spin[idx]
            a_val  = max(0, min(255, int(ha * (1.0 - idx * 0.2))))
            if self.muted:
                col = self._hex_color(255, 30, 80, a_val)
            elif self._state == "THINKING":
                col = self._hex_color(160, 0, 255, a_val)
            else:
                col = self._hex_color(0, 220, 255, a_val)
                
            glow_col = self._alpha_blend(col, int(a_val * 0.35))
            for s in range(360 // (arc_l + gap)):
                start = (base_a + s * (arc_l + gap)) % 360
                # Glow ring
                c.create_arc(FCX-ring_r, FCY-ring_r, FCX+ring_r, FCY+ring_r,
                             start=start, extent=arc_l,
                             outline=glow_col, width=w_ring + 3, style="arc")
                # Core ring
                c.create_arc(FCX-ring_r, FCY-ring_r, FCX+ring_r, FCY+ring_r,
                             start=start, extent=arc_l,
                             outline=col, width=w_ring, style="arc")

        # Tick marks
        t_out = int(FW * 0.50)
        t_in  = int(FW * 0.478)
        mk_a  = max(0, min(255, int(ha * 1.2)))
        mk_c  = self._hex_color(0, 220, 255, mk_a)
        for deg in range(0, 360, 10):
            rad = math.radians(deg)
            inn = t_in if deg % 30 == 0 else t_in + 6
            c.create_line(
                FCX + t_out * math.cos(rad), FCY - t_out * math.sin(rad),
                FCX + inn  * math.cos(rad), FCY - inn  * math.sin(rad),
                fill=mk_c, width=(2 if deg % 90 == 0 else 1)
            )

        # Crosshairs
        ch_r = int(FW * 0.51)
        gap  = int(FW * 0.14)
        ch_a = self._hex_color(0, 200, 255, int(ha * 0.55))
        for x1, y1, x2, y2 in [
                (FCX - ch_r, FCY, FCX - gap, FCY),
                (FCX + gap,  FCY, FCX + ch_r, FCY),
                (FCX, FCY - ch_r, FCX, FCY - gap),
                (FCX, FCY + gap,  FCX, FCY + ch_r)]:
            c.create_line(x1, y1, x2, y2, fill=ch_a, width=1)

    def _draw_scan_lines(self, c):
        FCX, FCY = self.FCX, self.FCY
        FW  = self.FACE_SZ
        sr  = int(FW * 0.50)
        a   = min(255, int(self.halo_alpha * 1.5))
        ext = 75 if self.speaking else 44
        col1 = self._hex_color(0, 220, 255, a)
        col2 = self._hex_color(255, 120, 0, a // 2)
        c.create_arc(FCX-sr, FCY-sr, FCX+sr, FCY+sr,
                     start=self.scan_a1, extent=ext,
                     outline=col1, width=3, style="arc")
        c.create_arc(FCX-sr, FCY-sr, FCX+sr, FCY+sr,
                     start=self.scan_a2, extent=ext,
                     outline=col2, width=2, style="arc")

    def _draw_face(self, c):
        FCX, FCY = self.FCX, self.FCY
        FW = self.FACE_SZ
        fw = int(FW * self.scale)

        if self._has_face and _PIL:
            if (self._face_cache is None or
                    abs(self._face_cache[0] - self.scale) > 0.005):
                scaled = self._face_pil.resize((fw, fw), Image.BILINEAR)
                if self.muted:
                    r, g, b, a = scaled.split()
                    g = g.point(lambda px: int(px * 0.4))
                    b = b.point(lambda px: int(px * 0.4))
                    r = r.point(lambda px: min(255, int(px * 1.1 + 20)))
                    scaled = Image.merge("RGBA", (r, g, b, a))
                tk_img = ImageTk.PhotoImage(scaled)
                self._face_cache = (self.scale, tk_img)
            c.create_image(FCX, FCY, image=self._face_cache[1])
        else:
            # Fallback orb
            orb_r = int(FW * 0.28 * self.scale)
            for i in range(8, 0, -1):
                frac = i / 8
                r2   = int(orb_r * frac)
                a    = int(self.halo_alpha * 1.2 * frac)
                if self.muted:
                    col = self._hex_color(220, 0, 60, a)
                else:
                    col = self._hex_color(0, int(80 * frac), int(160 * frac), a)
                c.create_oval(FCX-r2, FCY-r2, FCX+r2, FCY+r2, fill=col, outline="")
            c.create_text(FCX, FCY, text=SYSTEM_NAME,
                          fill=C["pri"], font=("Consolas", 12, "bold"))

    def _draw_hud_frame(self, c, W, H):
        blen = 28
        bc   = C["pri"]
        bw   = 2
        # Adjusted to avoid panel area
        fx0, fx1 = 8,  int(W * 0.62) - 8
        fy0, fy1 = 68, H - 90

        corners = [(fx0, fy0, 1, 1), (fx1, fy0, -1, 1),
                   (fx0, fy1, 1, -1), (fx1, fy1, -1, -1)]
        for bx, by, sdx, sdy in corners:
            c.create_line(bx, by, bx + sdx * blen, by,  fill=bc, width=bw)
            c.create_line(bx, by, bx, by + sdy * blen,  fill=bc, width=bw)

        # Thin inner frame lines
        dim_c = C["border"]
        c.create_rectangle(fx0, fy0, fx1, fy1, outline=dim_c, width=1, dash=(2, 8))

        # Coordinates HUD text
        FCX, FCY = self.FCX, self.FCY
        coord_txt = f"X:{FCX:4d}  Y:{FCY:4d}  SCALE:{self.scale:.3f}"
        c.create_text(fx0 + 10, fy1 - 8, text=coord_txt,
                      fill=C["dim"], font=("Consolas", 7), anchor="w")

    def _draw_header(self, c, W):
        H = 66
        c.create_rectangle(0, 0, W, H, fill="#000a12", outline="")
        c.create_line(0, H, W, H, fill=C["border"], width=1)

        # Logo
        c.create_text(20, 22, text=SYSTEM_NAME, fill=C["pri"],
                      font=("Consolas", 18, "bold"), anchor="w")
        c.create_text(20, 45, text=MODEL_BADGE, fill=C["mid"],
                      font=("Consolas", 8), anchor="w")

        # Clock + date
        c.create_text(W - 14, 20, text=time.strftime("%H:%M:%S"),
                      fill=C["pri"], font=("Consolas", 16, "bold"), anchor="e")
        c.create_text(W - 14, 42, text=time.strftime("%a %Y-%m-%d"),
                      fill=C["mid"], font=("Consolas", 8), anchor="e")

        # Center: mode/backend indicator
        state_colors = {
            "LISTENING": C["listen"], "SPEAKING": C["speak"],
            "THINKING": C["think"],  "MUTED": C["muted"],
            "PROCESSING": C["warn"],
        }
        sc  = state_colors.get(self._state, C["mid"])
        sym = "●" if self.status_blink else "○"
        c.create_text(W // 2, 34, text=f"{sym}  {self._state}",
                      fill=sc, font=("Consolas", 11, "bold"))

    def _draw_status_area(self, c, W, H):
        FCX, FCY = self.FCX, self.FCY
        FW = self.FACE_SZ
        sy = FCY + FW // 2 + 32
        if sy > H - 110:
            return

        # Status label below face
        state_colors = {
            "LISTENING": C["listen"], "SPEAKING": C["speak"],
            "THINKING": C["think"],  "MUTED": C["muted"],
            "PROCESSING": C["warn"],
        }
        sc = state_colors.get(self._state, C["mid"])
        if self.muted:
            s_text = "⊘  MICROPHONE MUTED"
        elif self.speaking:
            s_text = f"▶  SPEAKING  ·  {time.strftime('%H:%M:%S')}"
        elif self._state == "THINKING":
            dots = "." * ((self.tick // 8 % 4) + 1)
            s_text = f"◈  PROCESSING{dots}"
        elif self._state == "LISTENING":
            s_text = "◎  AWAITING INPUT"
        else:
            s_text = f"◌  {self._state}"
        c.create_text(FCX, sy, text=s_text,
                      fill=sc, font=("Consolas", 10, "bold"))

        # Session uptime
        uptime = int(time.time()) % 86400
        h = uptime // 3600
        m = (uptime % 3600) // 60
        s = uptime % 60
        c.create_text(FCX, sy + 18,
                      text=f"SESSION  {h:02d}:{m:02d}:{s:02d}",
                      fill=C["dim"], font=("Consolas", 8))

    def _draw_waveform(self, c, W, H):
        """Draw the voice waveform below the status area."""
        FCX, FCY = self.FCX, self.FCY
        FW  = self.FACE_SZ
        wy  = FCY + FW // 2 + 62
        if wy + 22 > H - 95:
            return

        N   = len(self._wave_smooth)
        px0 = FCX - int(W * 0.22)
        bw  = int(W * 0.44) // N
        bw  = max(2, bw)
        BH  = 18

        for i, amp in enumerate(self._wave_smooth):
            h_bar = max(2, int(abs(amp) * BH * 1.8))
            h_bar = min(h_bar, BH)
            bx = px0 + i * bw
            if self.muted:
                col = C["muted"] if h_bar > 3 else C["dim"]
            elif self.speaking:
                col = C["pri"] if h_bar > BH * 0.5 else C["mid"]
            elif self._state == "THINKING":
                col = C["think"] if h_bar > 4 else C["dim"]
            else:
                col = C["dim"]
            top = wy + BH - h_bar
            c.create_rectangle(bx, top, bx + bw - 1, wy + BH,
                                fill=col, outline="")

    def _draw_metrics(self):
        """Draw system metrics in the right panel."""
        c = self.metrics_canvas
        c.delete("all")
        w = c.winfo_width() or 300
        h = 110

        c.create_rectangle(0, 0, w, h, fill=C["panel"], outline="")

        # Title
        c.create_text(10, 8, text="◈ SYSTEM TELEMETRY",
                      fill=C["mid"], font=("Consolas", 8, "bold"), anchor="w")

        metrics = []
        if _PSUTIL:
            metrics = [
                ("CPU", self._cpu, C["pri"],   C["dim"]),
                ("RAM", self._ram, C["acc2"],  C["dim"]),
            ]
        else:
            metrics = [
                ("CPU", 0.0, C["pri"],  C["dim"]),
                ("RAM", 0.0, C["acc2"], C["dim"]),
            ]

        bar_w = w - 80
        for idx, (label, val, col, bg) in enumerate(metrics):
            y0 = 24 + idx * 28
            c.create_text(10, y0 + 7, text=label, fill=C["text2"],
                          font=("Consolas", 8), anchor="w")
            # Background bar
            c.create_rectangle(42, y0 + 2, 42 + bar_w, y0 + 12,
                                fill=C["dimmer"], outline=C["dim"])
            # Segmented blocks
            num_segments = 25
            seg_gap = 2
            total_gap_w = (num_segments - 1) * seg_gap
            seg_w = (bar_w - total_gap_w) / num_segments
            
            filled_segs = int(num_segments * val / 100)
            for i in range(num_segments):
                x0 = 42 + i * (seg_w + seg_gap)
                x1 = x0 + seg_w
                if i < filled_segs:
                    c.create_rectangle(x0, y0 + 2, x1, y0 + 12, fill=col, outline="")
            # Value text
            c.create_text(w - 8, y0 + 7, text=f"{val:.0f}%",
                          fill=col, font=("Consolas", 8), anchor="e")

        # Network
        net_text = "NET  ↑" + self._fmt_bytes(self._net_s) + "  ↓" + self._fmt_bytes(self._net_r)
        c.create_text(10, 90, text=net_text,
                      fill=C["mid"], font=("Consolas", 7), anchor="w")

        # Tick indicator
        tick_x = (self.tick % (w - 20)) + 10
        c.create_line(tick_x, 99, tick_x + 3, 99, fill=C["pri"], width=2)

    def _draw_agent_status(self):
        c = self.agent_canvas
        c.delete("all")
        w = c.winfo_width() or 300

        c.create_rectangle(0, 0, w, 64, fill=C["panel"], outline="")
        c.create_text(10, 8, text="◈ AGENT STATUS",
                      fill=C["mid"], font=("Consolas", 8, "bold"), anchor="w")

        state_col = {
            "LISTENING": C["listen"], "SPEAKING": C["speak"],
            "THINKING": C["think"],  "MUTED": C["muted"],
            "PROCESSING": C["warn"],
        }
        sc  = state_col.get(self._state, C["mid"])
        dot = "●" if self.status_blink else "○"
        c.create_text(10, 28, text=f"{dot} BR  ·  {self._state}",
                      fill=sc, font=("Consolas", 9), anchor="w")

        tasks = list(self._agent_tasks.items())[-2:]
        for i, (tid, info) in enumerate(tasks):
            y = 44 + i * 14
            st = info.get("status", "?")
            st_col = C["listen"] if st == "completed" else C["warn"]
            c.create_text(10, y,
                          text=f"  ↳ {info.get('name','agent')[:12]}  [{st}]",
                          fill=st_col, font=("Consolas", 7), anchor="w")

    @staticmethod
    def _fmt_bytes(n):
        if n > 1_073_741_824:
            return f"{n/1_073_741_824:.1f}G"
        if n > 1_048_576:
            return f"{n/1_048_576:.1f}M"
        if n > 1024:
            return f"{n/1024:.1f}K"
        return f"{n}B"

    # ── Input handling ─────────────────────────────────────────────────────

    def _on_input_submit(self, event=None):
        text = self._input_var.get().strip()
        if not text:
            return
        self._input_var.set("")
        self._hist_idx = -1
        if text and (not self._cmd_history or self._cmd_history[0] != text):
            self._cmd_history.appendleft(text)
        if self.on_text_command:
            threading.Thread(
                target=self.on_text_command,
                args=(text,), daemon=True
            ).start()

    def _hist_prev(self, event=None):
        if not self._cmd_history:
            return
        self._hist_idx = min(self._hist_idx + 1, len(self._cmd_history) - 1)
        self._input_var.set(self._cmd_history[self._hist_idx])
        self._input_entry.icursor(tk.END)

    def _hist_next(self, event=None):
        if self._hist_idx <= 0:
            self._hist_idx = -1
            self._input_var.set("")
            return
        self._hist_idx -= 1
        self._input_var.set(self._cmd_history[self._hist_idx])
        self._input_entry.icursor(tk.END)

    def _autocomplete(self, event=None):
        text = self._input_var.get()
        # Simple command prefix completion
        prefixes = [
            "/commit", "/review", "/research", "/edit", "/scaffold",
            "/docker", "/deploy", "/github-scan", "/monitor",
        ]
        for p in prefixes:
            if p.startswith(text) and text:
                self._input_var.set(p + " ")
                self._input_entry.icursor(tk.END)
                return "break"

    def _update_charcount(self, *_):
        n = len(self._input_var.get())
        self._charcount_var.set(str(n))

    def _toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.set_state("MUTED")
            self.write_log("SYS: Microphone muted.")
        else:
            self.set_state("LISTENING")
            self.write_log("SYS: Microphone active.")

    # ── Public API ─────────────────────────────────────────────────────────

    def set_state(self, state: str):
        self._prev_state = self._state
        self._state      = state
        if state == "MUTED":
            self.speaking = False
        elif state == "SPEAKING":
            self.speaking = True
        elif state == "THINKING":
            self.speaking = False
        elif state == "LISTENING":
            self.speaking = False
        elif state == "PROCESSING":
            self.speaking = False
        else:
            self.speaking = False
        self.status_text = state

    def write_log(self, text: str):
        ts = time.strftime("[%H:%M:%S] ")
        tl = text.lower()

        if tl.startswith("you:"):
            tag  = "you"
            self.set_state("PROCESSING")
        elif tl.startswith("jarvis:") or tl.startswith("ai:") or tl.startswith("br:"):
            tag  = "ai"
            self.set_state("SPEAKING")
        elif "error" in tl or "failed" in tl or "exception" in tl:
            tag  = "err"
        elif tl.startswith("[tool]") or "tool" in tl[:10]:
            tag  = "tool"
        else:
            tag  = "sys"

        self._log_entries.append((ts, text, tag))

        def _insert():
            self.log_text.configure(state="normal")
            self.log_text.insert(tk.END, ts, "time")
            self.log_text.insert(tk.END, text + "\n", tag)
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")
            self._log_count_var.set(f"{len(self._log_entries)} entries")

        self.root.after_idle(_insert)

    def update_agent_task(self, task_id: str, name: str, status: str):
        self._agent_tasks[task_id] = {"name": name, "status": status}

    def start_speaking(self):
        self.set_state("SPEAKING")

    def stop_speaking(self):
        if not self.muted:
            self.set_state("LISTENING")

    # ── Resize handler ─────────────────────────────────────────────────────

    def _on_resize(self, event=None):
        if event and event.widget is self.root:
            self.W = self.root.winfo_width()
            self.H = self.root.winfo_height()
            self.bg.config(width=self.W, height=self.H)
            self.FCX = int(self.W * 0.38)
            self.FCY = int(self.H * 0.42)
            self.FACE_SZ = min(int(self.H * 0.42), 320)
            self._hex_grid = HexGrid(self.W, self.H, 28)

    # ── Face loader ────────────────────────────────────────────────────────

    def _load_face(self, path):
        if not _PIL:
            return
        FW = self.FACE_SZ
        try:
            img  = Image.open(path).convert("RGBA").resize((FW, FW), Image.LANCZOS)
            mask = Image.new("L", (FW, FW), 0)
            ImageDraw.Draw(mask).ellipse((2, 2, FW - 2, FW - 2), fill=255)
            img.putalpha(mask)
            self._face_pil = img
            self._has_face = True
        except Exception:
            self._has_face = False

    # ── API key setup ──────────────────────────────────────────────────────

    def _api_keys_exist(self) -> bool:
        if not API_FILE.exists():
            return False
        try:
            data = json.loads(API_FILE.read_text(encoding="utf-8"))
            return bool(data.get("gemini_api_key")) and bool(data.get("os_system"))
        except Exception:
            return False

    def wait_for_api_key(self):
        while not self._api_key_ready:
            time.sleep(0.1)

    def _show_setup_ui(self):
        detected = self._detect_os()
        self._selected_os = tk.StringVar(value=detected)

        overlay = tk.Frame(self.root, bg="#00080f",
                           highlightbackground=C["pri"],
                           highlightthickness=2)
        overlay.place(relx=0.5, rely=0.5, anchor="center",
                      width=460, height=520)

        # Header
        hdr = tk.Frame(overlay, bg=C["pri"], height=42)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  ◈  BR INITIALISATION REQUIRED",
                 fg=C["bg"], bg=C["pri"],
                 font=("Consolas", 11, "bold")).pack(side="left", pady=10)

        # Body
        body = tk.Frame(overlay, bg="#00080f", padx=24)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="GEMINI API KEY",
                 fg=C["mid"], bg="#00080f",
                 font=("Consolas", 9, "bold")).pack(anchor="w", pady=(20, 4))

        key_frame = tk.Frame(body, bg="#000d14",
                             highlightbackground=C["border"],
                             highlightthickness=1)
        key_frame.pack(fill="x", pady=(0, 4))
        tk.Label(key_frame, text="▸", fg=C["pri"], bg="#000d14",
                 font=("Consolas", 10)).pack(side="left", padx=6, pady=8)
        self._gemini_entry = tk.Entry(
            key_frame, width=38, fg=C["text"], bg="#000d14",
            insertbackground=C["pri"], borderwidth=0,
            font=("Consolas", 10), show="*"
        )
        self._gemini_entry.pack(side="left", fill="x", expand=True, pady=8, padx=4)
        self._show_key_var = tk.IntVar()
        tk.Checkbutton(key_frame, text="Show", variable=self._show_key_var,
                       fg=C["dim"], bg="#000d14", selectcolor="#000d14",
                       activebackground="#000d14",
                       command=lambda: self._gemini_entry.config(
                           show="" if self._show_key_var.get() else "*")
                       ).pack(side="right", padx=6)

        tk.Label(body, text="Visit https://aistudio.google.com for a free key",
                 fg=C["dim"], bg="#00080f",
                 font=("Consolas", 7)).pack(anchor="w", pady=(0, 18))

        # Divider
        tk.Frame(body, bg=C["border"], height=1).pack(fill="x", pady=8)

        tk.Label(body, text="OPERATING SYSTEM",
                 fg=C["mid"], bg="#00080f",
                 font=("Consolas", 9, "bold")).pack(anchor="w", pady=(8, 8))

        os_frame = tk.Frame(body, bg="#00080f")
        os_frame.pack(fill="x", pady=(0, 20))
        self._os_btns = {}
        os_map = [
            ("windows", "⊞  WINDOWS", C["pri"]),
            ("mac",     "  macOS",    C["acc2"]),
            ("linux",   "🐧  LINUX",   C["acc3"]),
        ]
        for os_key, label, col in os_map:
            btn = tk.Button(
                os_frame, text=label, width=12,
                font=("Consolas", 9, "bold"), borderwidth=0,
                cursor="hand2", pady=7, relief="flat",
                command=lambda k=os_key: self._sel_os(k)
            )
            btn.pack(side="left", padx=6)
            self._os_btns[os_key] = btn
        self._sel_os(detected)

        # Submit
        tk.Frame(body, bg=C["border"], height=1).pack(fill="x", pady=(8, 16))
        submit = tk.Button(
            body, text="▸  INITIALISE NEURAL CORE",
            command=self._save_setup,
            bg=C["pri"], fg=C["bg"],
            activebackground=C["pri2"], activeforeground=C["bg"],
            font=("Consolas", 10, "bold"), borderwidth=0,
            pady=10, cursor="hand2", relief="flat"
        )
        submit.pack(fill="x")
        self._setup_overlay = overlay
        self._gemini_entry.focus_set()

    def _sel_os(self, os_key):
        self._selected_os.set(os_key)
        col_map = {"windows": C["pri"], "mac": C["acc2"], "linux": C["acc3"]}
        for k, btn in self._os_btns.items():
            if k == os_key:
                btn.config(fg=C["bg"], bg=col_map[k],
                           activeforeground=C["bg"],
                           activebackground=col_map[k])
            else:
                btn.config(fg=C["dim"], bg=C["dimmer"],
                           activeforeground=C["text"],
                           activebackground=C["bg2"])

    def _save_setup(self):
        key = self._gemini_entry.get().strip()
        if not key:
            self._gemini_entry.config(
                highlightthickness=2, highlightbackground=C["error"],
                highlightcolor=C["error"])
            return
        os_sys = self._selected_os.get()
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(API_FILE, "w", encoding="utf-8") as f:
            json.dump({"gemini_api_key": key, "os_system": os_sys}, f, indent=4)
        self._setup_overlay.destroy()
        self._api_key_ready = True
        self.set_state("LISTENING")
        self.write_log(f"SYS: Neural core initialised. OS → {os_sys.upper()}. BR online.")

    @staticmethod
    def _detect_os() -> str:
        s = platform.system().lower()
        if s == "darwin":  return "mac"
        if s == "windows": return "windows"
        return "linux"
