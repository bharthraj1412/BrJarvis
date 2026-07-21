# B.R. JARVIS MK37 — UI & UX Design Specification (v6.0)

> **Next-Gen AI OS Control Center — Colorful Glossy Glassmorphic Interface**  
> *Architectural Specification for User Interface (UI), User Experience (UX), Design System Tokens, and Micro-Interaction Workflows.*

---

## 📄 Executive Summary

**B.R. JARVIS MK37 v6.0** introduces a state-of-the-art **Colorful Glossy Glassmorphic UI & UX Framework**. Designed for real-time human-AI collaboration, the interface balances high-density system telemetry, multi-modal voice feedback, multi-agent status tracking, and 12 quick-access native integration tiles with zero-friction ergonomics.

The design relies on standard Python `tkinter` and PIL (Pillow) graphics rendering engines, paired with Windows DWM Dark Mode APIs for native frosted-glass aesthetics.

---

## 🎨 Design Philosophy & Principles

### 1. Cyberpunk Frosted Glassmorphism
- **Depth & Translucency**: UI panels utilize translucent dark frosted glass (`#111722`) layered above a deep space canvas background (`#06090e`).
- **Glossy Neon Glow Borders**: Hover states and active focus indicators trigger vibrant neon borders (`#00e5ff`, `#bf5af2`, `#30d158`) with subtle radial elevation.
- **Visual Contrast**: Dark background matrices ensure high contrast (WCAG AA compliant) with neon accents and crisp text typography.

### 2. Low-Cognitive Load & Ambient Intelligence
- **Floating Voice & Core Orb**: A central animated AI Orb provides immediate status recognition (Listening, Thinking, Speaking, Muted).
- **56-Band Equalizer Visualizer**: Real-time smooth dynamic audio waveforms mirror voice input/output activity.
- **Multi-Color Background Particle Field**: 35 floating glass particles animate silently in 2D space to create continuous depth without cluttering UI focus.

### 3. Multi-Modal Accessibility & Ergonomics
- **Quad-Input Support**: Seamless interaction via Voice Commands, Keyboard Shortcuts, Text Command Bar, and Direct Touch/Mouse Tile Clicks.
- **Context-Aware Display Modes**: Switch between **FULL Dashboard**, **COMPACT View**, **SLEEP Orb**, and **MAX Control Panel**.

---

## 📐 Design System & Color Tokens

### 1. Color Palette Matrix (`C`)

| Token | Hex Value | Purpose / Usage |
| :--- | :--- | :--- |
| `bg` | `#06090e` | Deep dark space canvas background |
| `bg_trans` | `#0b1018` | Translucent glass backdrop overlay |
| `surface` | `#111722` | Right panel & navigation bar surface |
| `card` | `#17202f` | Tile card default surface |
| `card_h` | `#202b3f` | Card hover state background |
| `card_glow` | `#2d3d59` | Frosted elevation shadow & border glow |
| `border` | `#263449` | Standard structural panel border |
| `border_glow`| `#00e5ff` | Focused input border & active neon glow |
| `accent` | `#0088ff` | Primary action button / Electric Blue |
| `accent_l` | `#40a9ff` | Light blue text highlight & status |
| `cyan` | `#00f2fe` | AI speaking state, prompt icon, cyan highlight |
| `purple` | `#bf5af2` | AI thinking state, telemetry header |
| `pink` | `#ff2d55` | Core notification, neural log accent |
| `green` | `#30d158` | AI listening state, success badges |
| `amber` | `#ff9f0a` | System warnings & alerts |
| `magenta` | `#ff007f` | Music integration & active media badge |

### 2. State-Based Status Colors

```
🟢 LISTENING  -> #30d158 (Neon Green)
🟣 THINKING   -> #bf5af2 (Neon Purple)
🔵 SPEAKING   -> #00f2fe (Neon Cyan)
🔴 MUTED      -> #ff453a (Neon Red)
🟡 PROCESSING -> #ff9f0a (Neon Amber)
```

### 3. Typography Scale (`F`)

| Style Name | Font Family | Size | Weight | Usage |
| :--- | :--- | :--- | :--- | :--- |
| `ui` | `Segoe UI` | `9pt` | Regular | Standard UI text & button labels |
| `ui_b` | `Segoe UI` | `9pt` | Bold | Primary buttons & modal headings |
| `ui_sm` | `Segoe UI` | `8pt` | Regular | Subtitle & metadata text |
| `ui_xs` | `Segoe UI` | `7pt` | Regular | Section headers & badge labels |
| `ui_title` | `Segoe UI` | `18pt` | Bold | Integration grid title |
| `mono` | `Cascadia Code` | `9pt` | Regular | Command bar entry field |
| `mono_sm` | `Cascadia Code` | `8pt` | Regular | Neural log entries |
| `mono_xs` | `Cascadia Code` | `7pt` | Regular | System timestamps |
| `clock` | `Cascadia Code` | `16pt` | Bold | System header clock |

---

## 🖥️ UI Layout Architecture

The application layout split is structured as follows:

```
+-------------------------------------------------------------------+------------------------+
|                                                                   |                        |
|                     MAIN CANVAS AREA (68% Width)                  |  RIGHT PANEL (32% W)   |
|                                                                   |                        |
|   +-----------------------------------------------------------+   | +--------------------+ |
|   |  DUAL-TONE RADIAL AURORA & PARTICLE FIELD ENGINE          |   | | MODEL ROUTER       | |
|   |                                                           |   | +--------------------+ |
|   |              [ FLOATING CORE VOICE ORB ]                  |   | | SYSTEM TELEMETRY   | |
|   |              ( Pulsing Ring & Audio Wave )                |   | +--------------------+ |
|   |                                                           |   | | AGENT MATRIX       | |
|   +-----------------------------------------------------------+   | +--------------------+ |
|   |                                                           |   | | NEURAL LOG         | |
|   |          12 MULTI-COLOR INTEGRATION TILES GRID            |   | | (Scrollable Feed)  | |
|   |            (Calendar, Timer, Mail, Weather...)            |   | |                    | |
|   +-----------------------------------------------------------+   | +--------------------+ |
+-------------------------------------------------------------------+------------------------+
|  BOTTOM COMMAND BAR: [Modes]  [ ❯ Command Input... ] [Send →] [🎙️]| (52px Fixed Height)    |
+--------------------------------------------------------------------------------------------+
```

---

## 🎛️ Detailed Component Specifications

### 1. Main Background Canvas & Animation Engine
- **Particles Engine**: 35 instances of `GlassParticle` floating continuously across the canvas with semi-randomized velocities ($v_x, v_y \in [0.04, 0.18]$) and phase-shifting color highlights (`cyan`, `purple`, `pink`, `green`, `amber`).
- **Aurora Engine**: Dual radial gradient background glows centered around the Core Orb, providing atmospheric depth.

### 2. Floating AI Core Voice Orb & Waveform Visualizer
- **Voice Orb Engine**: Positioned at $30\%$ Canvas Width, $44\%$ Canvas Height. Supports scaling pulses during voice output and dynamic breathing cycles during standby.
- **Orbiting Halo Ring**: Outer ring rotating at variable angles (`ring_angles`) with status-coded colors.
- **56-Band Equalizer**: Dynamic bar graph positioned below the Core Orb, rendering dynamic sinusoidal height modulation ($0.0 \rightarrow 1.0$) during speech output and mic input.

---

### 3. 12 Multi-Color Glossy Integration Grid (`INTEGRATION_TILES`)

Configured in a **$4 \times 3$ layout** with glossy glass surfaces, icon accents, and direct actions:

| Tile Index | Icon | Label | Target Action / Trigger | Base Glass BG | Accent Glow |
| :---: | :---: | :--- | :--- | :--- | :--- |
| `01` | 📅 | **Open Calendar** | `https://calendar.google.com` | `#0a2240` | `#00b2ff` |
| `02` | ⏱️ | **Set Timer** | `set timer for 10 minutes` | `#3d2200` | `#ffc04d` |
| `03` | ✉️ | **Check Email** | `https://mail.google.com` | `#2c123b` | `#d988ff` |
| `04` | 🗺️ | **Quick Map** | `https://maps.google.com` | `#0c3316` | `#62e083` |
| `05` | 📋 | **Task List** | `show task list and planner` | `#3d0c18` | `#ff6b87` |
| `06` | 🎙️ | **Voice Memos** | `start voice memo recording` | `#052e3d` | `#64f7ff` |
| `07` | 🎵 | **Play Music** | `https://open.spotify.com` | `#3d0522` | `#ff59b2` |
| `08` | 🌤️ | **Check Weather**| `what is the weather today` | `#3d3000` | `#ffe066` |
| `09` | 🔍 | **Search Web** | `search google for latest AI news` | `#071a42` | `#4382f7` |
| `10` | 🌐 | **Open Browser** | `https://google.com` | `#191740` | `#8e8cf7` |
| `11` | 🖥️ | **System Stats** | `SHOW_TELEMETRY` | `#0a2b3d` | `#9de5ff` |
| `12` | ⚙️ | **Quick Settings**| `SHOW_SETTINGS` | `#3d1515` | `#ffa3a3` |

---

### 4. Right Control Panel

#### A. Model Router Header
- Displays current active model (e.g. `⚡ BR NEURAL CORE v6.0`).
- Provides direct access button to the **⚙ Settings Modal**.

#### B. System Telemetry Gauges
- **Live Monitoring Metrics**: CPU Utilisation %, RAM Utilisation %, Disk %, Core Temp, Network IO.
- Rendered via real-time progress bars with dynamic color transitions (Green $\rightarrow$ Amber $\rightarrow$ Red).

#### C. Multi-Agent Orchestrator Matrix
- Real-time indicator badges tracking subagent execution state (`IDLE`, `RUNNING`, `FINISHED`).

#### D. Neural Event Log
- High-performance scrollable event feed (`deque` capped at 300 entries).
- **Color Tagging Scheme**:
  - `you`: White (`#ffffff`), bold prompt string.
  - `ai`: Cyan (`#00f2fe`), assistant output text.
  - `sys`: Muted Grey (`#94a3b8`), background system status.
  - `err`: Neon Red (`#ff453a`), system error notice.
  - `tool`: Neon Green (`#30d158`), subagent / tool execution.

---

### 5. Bottom Command Bar & Action Dock

- **Display Mode Switchers**:
  - `🖥️ Dashboard`: Full dashboard view.
  - `📱 Compact`: Scaled-down floating mini bar.
  - `🌙 Sleep Orb`: Minimizes panel to floating orb.
  - `🎛️ Max Control`: Expands full-screen telemetry console.
- **Command Input Box**:
  - `❯` Neon Cyan prompt icon.
  - Command History Buffer (up to 50 previous entries accessed via `<Up>` / `<Down>` arrows).
  - Live character count counter.
  - `<Tab>` Autocomplete trigger.
- **Quick Action Mic Button**: Toggle microphone state (`🎙️`) with instant status update.

---

## ⌨️ Hotkeys & Fast Ergonomics

| Key Combination | Function |
| :--- | :--- |
| `<F4>` | Toggle Voice Microphone Mute |
| `<F5>` | Set AI State to `LISTENING` |
| `<F11>` | Toggle Sleep Mode Orb |
| `<Escape>` | Focus Command Input Field |
| `<Control-l>` | Clear Neural Event Log |
| `<Control-k>` | Focus Command Input Field |
| `<Up>` / `<Down>` | Navigate Command Input History |
| `<Tab>` | Autocomplete Command String |

---

## 🛠️ Code Structure & Implementation Files

- UI Code Entry Point: [ui.py](file:///d:/BRJARVIS/Br-Jarvis/ui.py)
- Application Startup: [start.py](file:///d:/BRJARVIS/Br-Jarvis/start.py)
- Main Event Orchestrator: [main_mk37.py](file:///d:/BRJARVIS/Br-Jarvis/main_mk37.py)
- Architecture Documentation: [br_archetecture](file:///d:/BRJARVIS/Br-Jarvis/br_archetecture)

---

> *UI & UX Design Specification maintained by the B.R. JARVIS Engineering Team.*
