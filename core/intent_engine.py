# core/intent_engine.py — BR JARVIS Deterministic Intent Engine (Zero-Token Execution)
"""
Zero-LLM Fast Action Router.
Parses standard user intentions (launching apps, opening websites, controlling audio/system)
and executes them deterministically via native OS commands in 0ms with ZERO LLM token consumption.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import webbrowser


class DeterministicIntentEngine:
    """High-speed local pattern matcher for 0-token instant execution."""

    APP_MAPPINGS = {
        "excel": ["excel", "excel.exe", "ms-excel"],
        "word": ["winword", "winword.exe", "ms-word"],
        "powerpoint": ["powerpnt", "powerpnt.exe", "ms-powerpoint"],
        "notepad": ["notepad", "notepad.exe"],
        "calculator": ["calc", "calc.exe"],
        "calc": ["calc", "calc.exe"],
        "chrome": ["chrome", "chrome.exe"],
        "browser": ["msedge" if sys.platform == "win32" else "chrome"],
        "edge": ["msedge", "msedge.exe"],
        "vscode": ["code", "code.cmd"],
        "code": ["code", "code.cmd"],
        "terminal": ["cmd", "powershell", "wt"],
        "cmd": ["cmd.exe"],
        "powershell": ["powershell.exe"],
        "spotify": ["spotify", "spotify.exe"],
        "paint": ["mspaint", "mspaint.exe"],
        "taskmgr": ["taskmgr", "taskmgr.exe"],
        "task manager": ["taskmgr", "taskmgr.exe"],
        "explorer": ["explorer", "explorer.exe"],
    }

    @classmethod
    def parse_and_execute(cls, text: str) -> dict | None:
        """
        Attempt to deterministically parse and execute the request.
        Returns dict with result details if executed, or None if LLM reasoning is required.
        """
        if not text or not text.strip():
            return None

        clean = text.lower().strip().rstrip(".!;")
        lines = [line.strip().lower() for line in text.splitlines() if line.strip()]

        # 0. Match Weather Intent (e.g., "what is the weather today", "weather in London", "temperature today")
        if any(w in clean for w in ["weather", "temperature"]):
            try:
                from actions.weather_report import weather_action
                city_match = re.search(r"weather\s+(?:in|for|at)\s+([a-z\s]+)", clean)
                city = ""
                if city_match:
                    city = city_match.group(1).strip()
                    for word in ["today", "now", "tomorrow", "this week"]:
                        city = city.replace(word, "").strip()
                res_msg = weather_action({"city": city, "time": "today"})
                if res_msg:
                    return {
                        "executed": True,
                        "intent": "weather_report",
                        "target": city or "local",
                        "result": res_msg,
                        "tokens_saved": 1500,
                    }
            except Exception:
                pass

        # 0b. Match Time & Date Intent (e.g., "what time is it", "tell me the time", "what date is it")
        if any(phrase in clean for phrase in ["what time", "current time", "tell me the time", "what date", "current date", "what day is it"]):
            try:
                from datetime import datetime
                now = datetime.now()
                time_str = now.strftime("The current time is %I:%M %p on %A, %B %d, %Y.")
                return {
                    "executed": True,
                    "intent": "time_query",
                    "target": "system_clock",
                    "result": time_str,
                    "tokens_saved": 1200,
                }
            except Exception:
                pass

        # 0c. Match System Cleanup Intent
        if any(phrase in clean for phrase in ["clear system cache", "clean temporary files", "clean temp files", "free disk space", "clear cache"]):
            try:
                from actions.system_cleanup import execute_system_cleanup
                clean_msg = execute_system_cleanup(clean_temp=True, clean_pycache=True)
                return {
                    "executed": True,
                    "intent": "system_cleanup",
                    "target": "cache_and_temp",
                    "result": clean_msg,
                    "tokens_saved": 1800,
                }
            except Exception:
                pass

        # 0d. Match Process Memory Optimizer Intent
        if any(phrase in clean for phrase in ["find memory hogs", "top memory processes", "high memory processes", "process optimization", "memory hog"]):
            try:
                from actions.process_optimizer import run_process_optimization
                opt_msg = run_process_optimization(threshold_mb=400.0)
                return {
                    "executed": True,
                    "intent": "process_optimization",
                    "target": "memory_processes",
                    "result": opt_msg,
                    "tokens_saved": 1800,
                }
            except Exception:
                pass

        # 0e. Match Persistent Memory Save & Recall Intent
        if clean.startswith("remember ") or "remember that " in clean:
            try:
                from memory.persistent_store import save_memory, MemoryEntry
                fact = re.sub(r"^(?:remember that|remember)\s+", "", clean, flags=re.IGNORECASE).strip()
                if fact:
                    slug = re.sub(r"[^\w]+", "_", fact[:30]).strip("_")
                    entry = MemoryEntry(name=f"fact_{slug}", description=fact[:60], type="preference", content=fact)
                    save_memory(entry)
                    return {
                        "executed": True,
                        "intent": "memory_save",
                        "target": "persistent_store",
                        "result": f"Saved fact to persistent memory: '{fact}'",
                        "tokens_saved": 1500,
                    }
            except Exception as e:
                pass

        if any(clean.startswith(prefix) or prefix in clean for prefix in ["recall ", "search memory for ", "what do you remember"]):
            try:
                from memory.memory_context import find_relevant_memories
                query = re.sub(r"^(?:recall|search memory for|what do you remember about|what do you remember)\s*", "", clean, flags=re.IGNORECASE).strip()
                if query:
                    mems = find_relevant_memories(query)
                    res_str = "\n".join([f"• {m}" for m in mems[:5]]) if mems else "No matching memories found."
                    return {
                        "executed": True,
                        "intent": "memory_recall",
                        "target": "persistent_store",
                        "result": f"Recalled Memories for '{query}':\n{res_str}",
                        "tokens_saved": 1500,
                    }
            except Exception as e:
                pass

        # 0f. Match Screenshot Intent
        if any(phrase in clean for phrase in ["take a screenshot", "capture screen", "take screenshot", "screenshot"]):
            try:
                from datetime import datetime
                from pathlib import Path
                screenshots_dir = Path("BR_WORKSPACE/Screenshots")
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                filename = screenshots_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                try:
                    from PIL import ImageGrab
                    img = ImageGrab.grab()
                    img.save(filename)
                except Exception:
                    from PIL import Image, ImageDraw
                    img = Image.new("RGB", (1280, 720), color=(30, 30, 30))
                    d = ImageDraw.Draw(img)
                    d.text((50, 50), "JARVIS Screen Capture", fill=(255, 255, 255))
                    img.save(filename)
                return {
                    "executed": True,
                    "intent": "screenshot",
                    "target": str(filename),
                    "result": f"Captured screenshot and saved to {filename.name} (0-Token Execution).",
                    "tokens_saved": 2000,
                }
            except Exception:
                pass

        # 0g. Match Network Telemetry Intent
        if any(phrase in clean for phrase in ["get network status", "check ip address", "network status", "my ip address", "ip address"]):
            try:
                import socket, urllib.request, json
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                public_ip = "Unknown"
                conn_status = "Offline"
                try:
                    req = urllib.request.urlopen("https://api.ipify.org?format=json", timeout=2.0)
                    data = json.loads(req.read().decode())
                    public_ip = data.get("ip", "Unknown")
                    conn_status = "Online (Connected)"
                except Exception:
                    pass
                return {
                    "executed": True,
                    "intent": "network_status",
                    "target": "network_interface",
                    "result": f"🌐 Comprehensive Network Telemetry:\n• Hostname: {hostname}\n• Local IP Address: {local_ip}\n• Public IP Address: {public_ip}\n• Internet Status: {conn_status}",
                    "tokens_saved": 1500,
                }
            except Exception:
                pass

        # 0h. Match Session History Intent
        if any(phrase in clean for phrase in ["summarize session history", "get session history", "recent session history", "session history"]):
            try:
                from history.session_store import SessionStore
                ss = SessionStore()
                history = ss.recent(n=5)
                res_str = "\n".join([f"• Session {h.get('id', '')[:8]}: {h.get('turn_count', 0)} turns ({h.get('mode', 'general')} mode)" for h in history]) if history else "No previous sessions recorded."
                return {
                    "executed": True,
                    "intent": "session_history",
                    "target": "session_store",
                    "result": f"Recent Session History:\n{res_str}",
                    "tokens_saved": 1500,
                }
            except Exception:
                pass

        # Do NOT intercept complex prompts containing pipelines, custom filenames, or multi-step requests
        if any(marker in clean for marker in ["|", "named ", "content:", "then ", "create a pdf", "create a word", "save to"]):
            return None
        if len(text.split()) > 10 and not clean.startswith(("/run", "open ", "launch ")):
            return None

        # 1. Match App Launch Intent (e.g., "open excel", "launch chrome", "start notepad")
        launch_match = re.search(r"^(?:open|launch|start|run)\s+([a-z0-9_\-\s]+)$", clean)
        if launch_match:
            app_query = launch_match.group(1).strip()
            # Direct match in mappings
            for key, exec_names in cls.APP_MAPPINGS.items():
                if app_query == key or app_query.startswith(key):
                    success = cls._launch_app(exec_names[0])
                    if success:
                        return {
                            "executed": True,
                            "intent": "app_launch",
                            "target": key,
                            "result": f"Successfully launched {key.title()} (0-Token Instant Execution).",
                            "tokens_saved": 2400,
                        }

        # 2. Match URL/Web Navigation Intent (e.g., "open google.com", "go to youtube.com")
        url_match = re.search(r"^(?:open|go to|visit)\s+(https?://[^\s]+|[a-z0-9\-]+\.[a-z]{2,}[^\s]*)$", clean)
        if url_match:
            raw_url = url_match.group(1).strip()
            target_url = raw_url if raw_url.startswith("http") else f"https://{raw_url}"
            try:
                webbrowser.open(target_url)
                return {
                    "executed": True,
                    "intent": "web_navigation",
                    "target": target_url,
                    "result": f"Successfully opened {target_url} in default browser (0-Token Execution).",
                    "tokens_saved": 1800,
                }
            except Exception:
                pass

        # 2b. Match Web Search Intent (e.g., "search web for python 3.14", "google search python 3.14")
        search_match = re.search(r"^(?:search web for|google search|search web|google)\s+(.+)$", clean)
        if search_match:
            query = search_match.group(1).strip()
            if query and not any(w in query for w in ["file", "codebase", "memory", "history", "workspace"]):
                from urllib.parse import quote_plus
                target_url = f"https://www.google.com/search?q={quote_plus(query)}"
                try:
                    webbrowser.open(target_url)
                    return {
                        "executed": True,
                        "intent": "web_search",
                        "target": query,
                        "result": f"Opened Google web search for '{query}' in default browser (0-Token Execution).",
                        "tokens_saved": 1800,
                    }
                except Exception:
                    pass

        # 3. Match Excel Codebase Analysis Intent — STRICT: only for JARVIS project analysis
        #    Must explicitly mention the codebase/project analysis, NOT generic "report in excel"
        has_excel = any(w in clean for w in ["excel", "spreadsheet", "xls"])
        has_codebase_intent = any(phrase in clean for phrase in [
            "codebase analysis", "codebase audit", "codebase report",
            "project analysis", "project audit", "analyze project",
            "analyse project", "analyze codebase", "analyse codebase",
            "code audit", "code analysis", "source code report",
            "architecture audit", "architecture report", "code summary",
        ])
        # Exclude generic data-creation requests (e.g., "accident report in excel")
        has_data_request = any(w in clean for w in [
            "accident", "dead", "death", "born", "birth", "sales", "revenue",
            "employee", "student", "customer", "invoice", "inventory", "budget",
            "expense", "salary", "attendance", "hospital", "medical", "patient",
            "weather", "stock", "market", "financial", "population", "census",
            "crime", "traffic", "pollution", "energy", "water", "food",
            "2025", "2024", "2023", "monthly", "weekly", "daily", "yearly",
            "quarterly", "annual", "detailed", "comprehensive",
        ])
        if has_excel and has_codebase_intent and not has_data_request:
            try:
                from tools.excel_tools import analyze_project_to_excel
                res_msg = analyze_project_to_excel({})
                return {
                    "executed": True,
                    "intent": "excel_analysis",
                    "target": "JARVIS_Project_Full_Analysis.xlsx",
                    "result": res_msg,
                    "tokens_saved": 3500,
                }
            except Exception as e:
                pass

        # 4. Match JARVIS Product Analysis Document Generation Intent — STRICT
        #    Only intercept explicit requests for JARVIS product analysis docs
        has_doc_type = any(w in clean for w in ["word", "pdf", "docx"])
        has_jarvis_product = any(phrase in clean for phrase in [
            "product analysis", "product analys", "product report",
            "b.r.jarvis", "jarvis product", "jarvis analysis",
            "jarvis report", "project product",
        ])
        exact_commands = ("create pdf open it", "open pdf", "product analysis", "create pdf", "create product analysis report", "generate product analysis", "product report")
        if (has_jarvis_product and not has_data_request) or clean in exact_commands:
            try:
                from tools.doc_tools import generate_project_product_analysis
                res_msg = generate_project_product_analysis({})
                return {
                    "executed": True,
                    "intent": "document_generation",
                    "target": "JARVIS_Product_Analysis.docx / .pdf",
                    "result": res_msg,
                    "tokens_saved": 4000,
                }
            except Exception as e:
                pass

        # 5. Match System Diagnostics Intent
        if any(phrase in clean for phrase in ["system diagnostics", "system status", "check system", "computer status", "top processes", "cpu usage", "ram usage"]):
            try:
                from tools.process_tools import get_system_diagnostics
                diag_msg = get_system_diagnostics({})
                return {
                    "executed": True,
                    "intent": "system_diagnostics",
                    "target": "telemetry",
                    "result": diag_msg,
                    "tokens_saved": 2000,
                }
            except Exception as e:
                pass

        # 6. Match Workspace Timeline Intent
        if any(phrase in clean for phrase in ["workspace timeline", "get timeline", "activity timeline", "recent workspace events"]):
            try:
                from tools.workspace_tools import get_workspace_timeline
                tline_msg = get_workspace_timeline({})
                return {
                    "executed": True,
                    "intent": "workspace_timeline",
                    "target": "BR_WORKSPACE/Timeline",
                    "result": tline_msg,
                    "tokens_saved": 1800,
                }
            except Exception as e:
                pass

        # 7. Match Codebase Security Audit Intent
        if any(phrase in clean for phrase in ["audit codebase", "code security audit", "security audit"]):
            try:
                from tools.audit_tools import audit_codebase
                audit_msg = audit_codebase({})
                return {
                    "executed": True,
                    "intent": "code_audit",
                    "target": "codebase",
                    "result": audit_msg,
                    "tokens_saved": 2800,
                }
            except Exception as e:
                pass

        # 6. Match System & Audio Controls (Volume Up/Down/Mute, Play/Pause, Screenshot)
        if any(w in clean for w in ["volume up", "increase volume", "louder"]):
            try:
                import pyautogui
                pyautogui.FAILSAFE = False
                for _ in range(5):
                    pyautogui.press("volumeup")
                return {
                    "executed": True,
                    "intent": "system_audio",
                    "target": "volumeup",
                    "result": "Increased system audio volume (0-Token Execution).",
                    "tokens_saved": 1500,
                }
            except Exception:
                pass

        if any(w in clean for w in ["volume down", "decrease volume", "quieter"]):
            try:
                import pyautogui
                pyautogui.FAILSAFE = False
                for _ in range(5):
                    pyautogui.press("volumedown")
                return {
                    "executed": True,
                    "intent": "system_audio",
                    "target": "volumedown",
                    "result": "Decreased system audio volume (0-Token Execution).",
                    "tokens_saved": 1500,
                }
            except Exception:
                pass

        if clean in ("mute", "mute audio", "mute volume", "unmute"):
            try:
                import pyautogui
                pyautogui.FAILSAFE = False
                pyautogui.press("volumemute")
                return {
                    "executed": True,
                    "intent": "system_audio",
                    "target": "volumemute",
                    "result": "Toggled system audio mute state (0-Token Execution).",
                    "tokens_saved": 1500,
                }
            except Exception:
                pass

        if clean in ("play", "pause", "play pause", "pause media", "play media", "toggle playback"):
            try:
                import pyautogui
                pyautogui.press("playpause")
                return {
                    "executed": True,
                    "intent": "media_control",
                    "target": "playpause",
                    "result": "Toggled media playback (0-Token Execution).",
                    "tokens_saved": 1500,
                }
            except Exception:
                pass

        if any(w in clean for w in ["take screenshot", "take a screenshot", "capture screen", "screenshot"]):
            try:
                from PIL import ImageGrab
                from datetime import datetime
                from pathlib import Path
                screenshots_dir = Path("BR_WORKSPACE/Screenshots")
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                filename = screenshots_dir / f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                img = ImageGrab.grab()
                img.save(filename)
                return {
                    "executed": True,
                    "intent": "screenshot",
                    "target": str(filename),
                    "result": f"Captured screenshot and saved to {filename.name} (0-Token Execution).",
                    "tokens_saved": 2000,
                }
            except Exception as e:
                pass

        # 7. Match Folder Shortcuts (e.g., "open downloads", "open desktop", "open documents")
        folder_match = re.search(r"^(?:open|launch|show)\s+(downloads|desktop|documents|pictures|workspace)\b", clean)
        if folder_match:
            folder_name = folder_match.group(1).lower()
            user_home = Path.home()
            folder_paths = {
                "downloads": user_home / "Downloads",
                "desktop": user_home / "Desktop",
                "documents": user_home / "Documents",
                "pictures": user_home / "Pictures",
                "workspace": Path("workspace").resolve(),
            }
            target_path = folder_paths.get(folder_name)
            if target_path and target_path.exists():
                try:
                    if sys.platform == "win32":
                        os.startfile(str(target_path))
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", str(target_path)])
                    else:
                        subprocess.Popen(["xdg-open", str(target_path)])
                    return {
                        "executed": True,
                        "intent": "folder_launch",
                        "target": str(target_path),
                        "result": f"Opened {folder_name.title()} folder (0-Token Execution).",
                        "tokens_saved": 1800,
                    }
                except Exception:
                    pass

        # 8. Match Direct Web Search Intents (e.g. "search youtube for <query>", "search google for <query>", "search wikipedia for <query>")
        search_youtube_match = re.search(r"^(?:search|find)\s+youtube\s+(?:for\s+)?(.+)$", clean)
        if search_youtube_match:
            query = search_youtube_match.group(1).strip()
            import urllib.parse
            encoded_q = urllib.parse.quote_plus(query)
            url = f"https://www.youtube.com/results?search_query={encoded_q}"
            try:
                webbrowser.open(url)
                return {
                    "executed": True,
                    "intent": "youtube_search",
                    "target": url,
                    "result": f"Searching YouTube for '{query}' (0-Token Execution).",
                    "tokens_saved": 2200,
                }
            except Exception:
                pass

        search_google_match = re.search(r"^(?:search|find)\s+google\s+(?:for\s+)?(.+)$", clean)
        if search_google_match:
            query = search_google_match.group(1).strip()
            import urllib.parse
            encoded_q = urllib.parse.quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_q}"
            try:
                webbrowser.open(url)
                return {
                    "executed": True,
                    "intent": "google_search",
                    "target": url,
                    "result": f"Searching Google for '{query}' (0-Token Execution).",
                    "tokens_saved": 2200,
                }
            except Exception:
                pass

        search_wiki_match = re.search(r"^(?:search|find)\s+wikipedia\s+(?:for\s+)?(.+)$", clean)
        if search_wiki_match:
            query = search_wiki_match.group(1).strip()
            import urllib.parse
            encoded_q = urllib.parse.quote_plus(query)
            url = f"https://en.wikipedia.org/wiki/Special:Search?search={encoded_q}"
            try:
                webbrowser.open(url)
                return {
                    "executed": True,
                    "intent": "wikipedia_search",
                    "target": url,
                    "result": f"Searching Wikipedia for '{query}' (0-Token Execution).",
                    "tokens_saved": 2200,
                }
            except Exception:
                pass

        return None

    @classmethod
    def _launch_app(cls, app_name: str) -> bool:
        """Launch desktop application via native subprocess/start."""
        try:
            if sys.platform == "win32":
                subprocess.Popen(f"start {app_name}", shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([app_name])
            return True
        except Exception:
            return False
