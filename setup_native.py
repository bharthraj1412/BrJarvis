# setup_native.py — JARVIS MK37 Native C Compiler Script
"""
Compiles native/jarvis_native.c into shared library (libjarvis_native.so / .dll / .dylib).
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR   = Path(__file__).resolve().parent
NATIVE_DIR = BASE_DIR / "native"
C_SRC      = NATIVE_DIR / "jarvis_native.c"

system = platform.system()
if system == "Windows":
    LIB_NAME = "jarvis_native.dll"
elif system == "Darwin":
    LIB_NAME = "libjarvis_native.dylib"
else:
    LIB_NAME = "libjarvis_native.so"

LIB_PATH = NATIVE_DIR / LIB_NAME


def compile_native() -> bool:
    """Attempt to compile native C library using gcc or clang."""
    if not C_SRC.exists():
        print(f"[NativeBuild] ⚠️ C source file not found: {C_SRC}")
        return False

    compiler = shutil.which("gcc") or shutil.which("clang")
    if not compiler:
        if system == "Windows":
            compiler = shutil.which("cl")
        if not compiler:
            print("[NativeBuild] ℹ️ No C compiler (gcc/clang) found. Native features will use pure-Python fallbacks.")
            return False

    NATIVE_DIR.mkdir(parents=True, exist_ok=True)

    if system == "Windows" and "cl" in compiler:
        cmd = [compiler, "/LD", str(C_SRC), f"/Fe{LIB_PATH}", "/O2"]
    else:
        flags = ["-O3", "-shared", "-fPIC"]
        if system == "Darwin":
            flags = ["-O3", "-dynamiclib"]
        cmd = [compiler] + flags + ["-o", str(LIB_PATH), str(C_SRC), "-lm"]

    print(f"[NativeBuild] 🛠️ Compiling native library: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and LIB_PATH.exists():
            print(f"[NativeBuild] ✅ Native library successfully compiled: {LIB_PATH}")
            return True
        else:
            print(f"[NativeBuild] ⚠️ Compilation failed: {res.stderr}")
            return False
    except Exception as e:
        print(f"[NativeBuild] ⚠️ Compilation exception: {e}")
        return False


if __name__ == "__main__":
    success = compile_native()
    sys.exit(0 if success else 1)
