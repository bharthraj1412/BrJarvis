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
            except Exception as e:
                pass

        # 3. Match Excel Codebase Analysis Intent (Fuzzy/Typo resilient)
        has_excel = any(w in clean for w in ["excel", "sheet", "workbook", "spreadsheet", "xls"])
        has_analysis = any(w in clean for w in ["analy", "anali", "project", "poject", "report", "codebase", "summary", "audit"])
        if has_excel and has_analysis:
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

        # 4. Match Product Analysis / Word / PDF Document Generation Intent
        has_doc_type = any(w in clean for w in ["word", "pdf", "docx", "document", "open it"])
        has_doc_topic = any(w in clean for w in ["product", "analis", "analys", "analise", "b.r.jarvis", "jarvis"])
        if (has_doc_type and has_doc_topic) or clean in ("create pdf open it", "open pdf", "product analysis", "create pdf"):
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
        if any(phrase in clean for phrase in ["system diagnostics", "top processes", "cpu usage", "ram usage"]):
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

        # 6. Match System Control Intent (e.g., "mute volume", "take screenshot")
        if clean in ("mute", "mute audio", "mute volume", "unmute"):
            try:
                import pyautogui
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
