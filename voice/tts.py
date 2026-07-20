# voice/tts.py — JARVIS MK37 Neural Text-To-Speech Engine
"""
High-quality text-to-speech using Microsoft Edge neural voices.
Fallback support to Linux native audio utilities, pyttsx3/espeak, or Windows SAPI5.
"""
from __future__ import annotations

import asyncio
import os
import platform
import re
import shutil
import subprocess
import tempfile
import threading
import uuid
import time
import traceback
from pathlib import Path

_OS = platform.system()

_HAS_EDGE_TTS = False
try:
    import edge_tts
    _HAS_EDGE_TTS = True
except ImportError:
    pass

_HAS_PYTHONCOM = False
try:
    import pythoncom
    _HAS_PYTHONCOM = True
except ImportError:
    pass


class MCIPlayer:
    """Play MP3/WAV files using Windows MCI or Linux/macOS audio utilities."""
    _winmm = None
    _lock = threading.Lock()
    _active_processes: dict[str, subprocess.Popen] = {}

    @classmethod
    def _init_winmm(cls):
        if cls._winmm is None and _OS == "Windows":
            import ctypes
            cls._winmm = ctypes.windll.winmm

    @classmethod
    def _send(cls, command: str) -> str:
        if _OS != "Windows":
            return ""
        import ctypes
        cls._init_winmm()
        buf = ctypes.create_unicode_buffer(256)
        err = cls._winmm.mciSendStringW(command, buf, 255, 0)
        if err:
            err_buf = ctypes.create_unicode_buffer(256)
            cls._winmm.mciGetErrorStringW(err, err_buf, 255)
            raise RuntimeError(f"MCI error: {err_buf.value}")
        return buf.value

    @classmethod
    def play_file(cls, filepath: str, alias: str = None) -> str:
        """Play an audio file. Returns the alias used."""
        with cls._lock:
            alias = alias or f"tts_{uuid.uuid4().hex[:8]}"
            if _OS == "Windows":
                fp = filepath.replace("/", "\\")
                try:
                    cls._send(f'close {alias}')
                except RuntimeError:
                    pass
                cls._send(f'open "{fp}" type mpegvideo alias {alias}')
                cls._send(f'play {alias}')
                return alias
            else:
                # Linux / macOS playback engine
                players = ["pw-play", "paplay", "ffplay", "mpv", "aplay", "canberra-gtk-play", "vlc"]
                chosen = None
                for p in players:
                    if shutil.which(p):
                        chosen = p
                        break
                
                if chosen:
                    cmd = [chosen]
                    if chosen == "ffplay":
                        cmd.extend(["-nodisp", "-autoexit", "-loglevel", "quiet"])
                    elif chosen == "mpv":
                        cmd.extend(["--no-terminal", "--no-video"])
                    cmd.append(filepath)
                    
                    try:
                        proc = subprocess.Popen(
                            cmd,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        cls._active_processes[alias] = proc
                    except Exception as e:
                        print(f"[JARVIS] Audio player execution error ({chosen}): {e}")
                else:
                    print(f"[JARVIS] No command-line audio player found for {filepath}")
                return alias

    @classmethod
    def is_playing(cls, alias: str) -> bool:
        """Check if the given alias is currently playing."""
        if _OS == "Windows":
            try:
                status = cls._send(f'status {alias} mode')
                return status.strip().lower() == "playing"
            except RuntimeError:
                return False
        else:
            with cls._lock:
                proc = cls._active_processes.get(alias)
                if proc is not None:
                    poll = proc.poll()
                    if poll is None:
                        return True
                    else:
                        cls._active_processes.pop(alias, None)
                        return False
                return False

    @classmethod
    def play_file_blocking(cls, filepath: str):
        """Play a file and block until playback completes."""
        alias = cls.play_file(filepath)
        while cls.is_playing(alias):
            time.sleep(0.05)
        cls.stop(alias)

    @classmethod
    def stop(cls, alias: str):
        """Stop and close the given alias."""
        if _OS == "Windows":
            try:
                cls._send(f'stop {alias}')
                cls._send(f'close {alias}')
            except RuntimeError:
                pass
        else:
            with cls._lock:
                proc = cls._active_processes.pop(alias, None)
                if proc and proc.poll() is None:
                    try:
                        proc.terminate()
                    except Exception:
                        pass


class NeuralTTS:
    """High-quality text-to-speech using Microsoft Edge neural voices.
    Falls back to Linux espeak/spd-say or Windows SAPI5.
    """

    VOICES = {
        "default":   "en-GB-SoniaNeural",      # British female — elegant, JARVIS-like
        "male_gb":   "en-GB-RyanNeural",        # British male
        "female_us": "en-US-JennyNeural",      # American female
        "male_us":   "en-US-GuyNeural",         # American male
    }

    def __init__(self, voice_key: str = "default", rate: str = "+18%", pitch: str = "+0Hz"):
        self.voice = self.VOICES.get(voice_key, self.VOICES["default"])
        self.rate = rate
        self.pitch = pitch
        self._temp_dir = Path(tempfile.gettempdir()) / "br_tts_cache"
        self._temp_dir.mkdir(exist_ok=True)
        self._current_alias = None
        self._is_speaking = False
        self._speak_lock = threading.Lock()

        # Fallback speaker
        self._sapi_speaker = None
        if not _HAS_EDGE_TTS:
            if _OS == "Windows":
                self._init_sapi5()
            else:
                self._init_linux_tts()

    def _init_sapi5(self):
        """Initialize SAPI5 as fallback (Windows)."""
        try:
            if _HAS_PYTHONCOM:
                pythoncom.CoInitialize()
            import win32com.client
            self._sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")
            voices = self._sapi_speaker.GetVoices()
            for i in range(voices.Count):
                desc = voices.Item(i).GetDescription()
                if "Zira" in desc or "Hazel" in desc:
                    self._sapi_speaker.Voice = voices.Item(i)
                    break
            self._sapi_speaker.Rate = -1
            print("[JARVIS] SAPI5 fallback voice initialized.")
        except Exception as e:
            print(f"[JARVIS] Warning: SAPI5 fallback failed: {e}")
            self._sapi_speaker = None

    def _init_linux_tts(self):
        """Initialize Linux speech dispatcher or espeak fallback."""
        if shutil.which("spd-say") or shutil.which("espeak") or shutil.which("espeak-ng"):
            print("[JARVIS] Linux native CLI TTS engine ready.")

    @property
    def is_speaking(self) -> bool:
        return self._is_speaking

    def speak_async(self, text: str, on_start=None, on_finish=None):
        """Speak text in a background thread."""
        thread = threading.Thread(
            target=self._speak_worker,
            args=(text, on_start, on_finish),
            daemon=True
        )
        thread.start()

    def _speak_worker(self, text: str, on_start=None, on_finish=None):
        """Worker that generates + plays TTS audio."""
        with self._speak_lock:
            self._is_speaking = True
            if on_start:
                on_start()

            try:
                if _HAS_EDGE_TTS:
                    self._speak_edge_tts(text)
                elif _OS == "Windows" and self._sapi_speaker:
                    self._speak_sapi5(text)
                else:
                    self._speak_linux_fallback(text)
            except Exception as e:
                print(f"[JARVIS] TTS error: {e}")
                traceback.print_exc()
            finally:
                self._is_speaking = False
                self._current_alias = None
                if on_finish:
                    on_finish()

    def _speak_edge_tts(self, text: str):
        """Generate speech using edge-tts and play via cross-platform audio player."""
        clean_text = re.sub(r'[*_~`#\[\](){}|<>]', '', text)
        clean_text = clean_text.strip()
        if not clean_text:
            return

        cache_key = uuid.uuid5(uuid.NAMESPACE_URL, f"{self.voice}|{self.rate}|{self.pitch}|{clean_text}").hex
        mp3_path = self._temp_dir / f"tts_{cache_key}.mp3"
        if mp3_path.exists() and mp3_path.stat().st_size >= 100:
            try:
                alias = MCIPlayer.play_file(str(mp3_path))
                self._current_alias = alias
                while MCIPlayer.is_playing(alias):
                    time.sleep(0.03)
                MCIPlayer.stop(alias)
                return
            except Exception:
                pass

        # Generate MP3 file
        loop = asyncio.new_event_loop()
        try:
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=self.voice,
                rate=self.rate,
                pitch=self.pitch,
            )
            loop.run_until_complete(communicate.save(str(mp3_path)))
        finally:
            loop.close()

        if not mp3_path.exists() or mp3_path.stat().st_size < 100:
            print("[JARVIS] edge-tts generated empty audio, skipping playback.")
            return

        try:
            alias = MCIPlayer.play_file(str(mp3_path))
            self._current_alias = alias
            while MCIPlayer.is_playing(alias):
                time.sleep(0.03)
            MCIPlayer.stop(alias)
        finally:
            pass

    def _speak_sapi5(self, text: str):
        """Speak using SAPI5 (Windows blocking)."""
        if not self._sapi_speaker:
            return
        try:
            if _HAS_PYTHONCOM:
                pythoncom.CoInitialize()
            self._sapi_speaker.Speak(text, 0)
        except Exception as e:
            print(f"[JARVIS] SAPI5 speak error: {e}")

    def _speak_linux_fallback(self, text: str):
        """Speak using Linux spd-say or espeak fallback."""
        clean = re.sub(r'[*_~`#\[\](){}|<>]', '', text).strip()
        if not clean:
            return
        
        if shutil.which("spd-say"):
            subprocess.run(["spd-say", "-w", clean], capture_output=True)
        elif shutil.which("espeak-ng"):
            subprocess.run(["espeak-ng", clean], capture_output=True)
        elif shutil.which("espeak"):
            subprocess.run(["espeak", clean], capture_output=True)
        else:
            print(f"[JARVIS] (Console TTS Fallback): {text}")

    def stop(self):
        """Stop any current speech playback."""
        if self._current_alias:
            MCIPlayer.stop(self._current_alias)
            self._current_alias = None
        self._is_speaking = False
