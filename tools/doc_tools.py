# tools/doc_tools.py — BR JARVIS Word & PDF Document Generator Suite
"""
Automated Microsoft Word (.docx) and PDF (.pdf) Document Generator & Auto-Launcher.
"""
from __future__ import annotations

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Any

from tools.registry import register_tool

try:
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False

try:
    from fpdf import FPDF
    _FPDF_AVAILABLE = True
except ImportError:
    _FPDF_AVAILABLE = False


def _get_workspace_dir() -> Path:
    return Path(__file__).resolve().parent.parent


@register_tool(
    name="create_word_document",
    description="Create a formatted Microsoft Word (.docx) document with headers, styled paragraphs, tables, and auto-launch in Word.",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Document title"},
            "content": {"type": "string", "description": "Main document text content or markdown"},
            "filename": {"type": "string", "description": "Output filename ending in .docx"},
            "auto_open": {"type": "boolean", "description": "Whether to auto-launch Word"}
        },
        "required": ["title", "content"]
    }
)
def create_word_document(args: dict) -> str:
    """Create a Microsoft Word document (.docx)."""
    if not _DOCX_AVAILABLE:
        return "Error: 'python-docx' library is missing."

    title = args.get("title", "Document")
    content = args.get("content", "")
    filename = args.get("filename", "JARVIS_Document.docx")
    auto_open = args.get("auto_open", True)

    if not filename.endswith(".docx"):
        filename += ".docx"

    out_path = _get_workspace_dir() / filename

    doc = docx.Document()

    # Title
    h1 = doc.add_heading(title, level=0)
    h1.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Add content lines
    for line in content.splitlines():
        line_s = line.strip()
        if not line_s:
            continue
        if line_s.startswith("# "):
            doc.add_heading(line_s[2:], level=1)
        elif line_s.startswith("## "):
            doc.add_heading(line_s[3:], level=2)
        elif line_s.startswith("### "):
            doc.add_heading(line_s[4:], level=3)
        elif line_s.startswith("- ") or line_s.startswith("* "):
            doc.add_paragraph(line_s[2:], style="List Bullet")
        else:
            doc.add_paragraph(line_s)

    try:
        doc.save(out_path)
    except PermissionError:
        import time
        ts = time.strftime("%H%M%S")
        out_path = _get_workspace_dir() / f"JARVIS_Document_{ts}.docx"
        doc.save(out_path)

    if auto_open and sys.platform == "win32":
        try:
            subprocess.Popen(f'start "" "{out_path}"', shell=True)
        except Exception:
            pass

    return f"⚡ Created Microsoft Word document: '{out_path}' and launched Word."


@register_tool(
    name="create_pdf_document",
    description="Create a formatted PDF (.pdf) document and auto-launch in default PDF viewer.",
    parameters={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Document title"},
            "content": {"type": "string", "description": "Main text content or markdown"},
            "filename": {"type": "string", "description": "Output filename ending in .pdf"},
            "auto_open": {"type": "boolean", "description": "Whether to auto-launch PDF viewer"}
        },
        "required": ["title", "content"]
    }
)
def create_pdf_document(args: dict) -> str:
    """Create a PDF document (.pdf)."""
    if not _FPDF_AVAILABLE:
        return "Error: 'fpdf' library is missing."

    title = args.get("title", "Document")
    content = args.get("content", "")
    filename = args.get("filename", "JARVIS_Document.pdf")
    auto_open = args.get("auto_open", True)

    if not filename.endswith(".pdf"):
        filename += ".pdf"

    out_path = _get_workspace_dir() / filename

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=16, style="B")
    pdf.cell(200, 10, txt=title.encode("latin-1", "replace").decode("latin-1"), ln=True, align="L")
    pdf.ln(5)

    pdf.set_font("Helvetica", size=11)

    for line in content.splitlines():
        line_clean = line.encode("latin-1", "replace").decode("latin-1")
        if not line_clean.strip():
            pdf.ln(3)
            continue
        if line_clean.startswith("#"):
            pdf.set_font("Helvetica", size=13, style="B")
            pdf.cell(0, 8, txt=line_clean.lstrip("#").strip(), ln=True)
            pdf.set_font("Helvetica", size=11)
        else:
            pdf.multi_cell(0, 6, txt=line_clean)

    try:
        pdf.output(str(out_path))
    except PermissionError:
        import time
        ts = time.strftime("%H%M%S")
        out_path = _get_workspace_dir() / f"JARVIS_Document_{ts}.pdf"
        pdf.output(str(out_path))

    if auto_open and sys.platform == "win32":
        try:
            subprocess.Popen(f'start "" "{out_path}"', shell=True)
        except Exception:
            pass

    return f"⚡ Created PDF document: '{out_path}' and launched PDF reader."


@register_tool(
    name="generate_project_product_analysis",
    description="Generate a complete Product Analysis Report for B.R. JARVIS as Word (.docx) and PDF (.pdf) documents and auto-open them.",
    parameters={"type": "object", "properties": {}}
)
def generate_project_product_analysis(args: dict) -> str:
    """Generate complete Product Analysis report for B.R. JARVIS in Word & PDF formats."""
    doc_title = "Product Analysis Document: B.R. JARVIS"
    doc_text = """
# Product Analysis Document: B.R. JARVIS

## 1. Executive Summary
- **Product Name:** B.R. JARVIS (Advanced Agentic AI Operating System)
- **Identity:** Ultra-fast autonomous AI assistant designed for decisive multi-step reasoning, pair programming, and live desktop visual control.
- **Mission:** To eliminate conversational filler and deliver instant, high-precision software engineering actions.

## 2. Product Vision & Value Proposition
B.R. JARVIS shifts the paradigm from static autocomplete AI to an autonomous senior developer:
- **Zero-Filler Directive:** Delivers immediate, high-signal task resolution with minimal output tokens.
- **Local Gateway Integration:** Operates with unlimited request quotas via local gateway http://localhost:8045/v1.

## 3. Core Features & Capabilities
- **0-Token Intent Engine:** Executes common app launches, browser navigation, and diagnostics in 0ms with zero token cost.
- **Live OS Visual Controller:** Performs real-time desktop visual grounded automation (2160x1440 screen resolution).
- **Multi-Tab Excel & Document Generator:** Automatically creates formatted .xlsx, .docx, and .pdf analytical reports.

## 4. Architecture & Subsystems Inventory
- **Core Kernel:** Native C FNV-1a bridge, EventBus runtime, dependency injection container.
- **Action Suite:** Live OS Control, Computer Control, RAG Library, Desktop Automation.
- **Tool Registry:** 98+ registered tools across web, code, files, excel, process management, and audits.
- **UI HUD:** Tkinter glassmorphism display with Mission Control HUD and Max Control Center.

## 5. Security & Execution Safety
- Local-first workspace execution with absolute path validation.
- AST compilation checks and security vulnerability scanning.
"""
    res_word = create_word_document({"title": doc_title, "content": doc_text, "filename": "JARVIS_Product_Analysis.docx", "auto_open": True})
    res_pdf = create_pdf_document({"title": doc_title, "content": doc_text, "filename": "JARVIS_Product_Analysis.pdf", "auto_open": True})

    return f"{res_word}\n{res_pdf}"
