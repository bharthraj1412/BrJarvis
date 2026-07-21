# voice/assistant.py — JARVIS MK37 Voice Control Coordinator
"""
Main hands-free voice control coordinator for JARVIS MK37.
Integrates Speech Recognition, Wake Word Detection, and ReAct loop execution.
"""
from __future__ import annotations

import asyncio
import queue
import re
import os
import sys
import time
import threading
import traceback
from typing import Callable
from router import AgentProfile

_HAS_SR = False
try:
    import speech_recognition as sr
    _HAS_SR = True
except ImportError:
    pass

_HAS_WINSOUND = False
try:
    import winsound
    _HAS_WINSOUND = True
except ImportError:
    pass

from ui import JarvisUI
from core.bootstrap import build_assistant_runtime
from agent.task_queue import get_queue, TaskPriority
from voice.tts import NeuralTTS
from voice.stt import SounddeviceMicrophone


class BRVoiceAssistant:
    """Hands-free Voice Assistant coordinator for JARVIS MK37."""

    def __init__(self, ui: JarvisUI):
        self.ui = ui
        self.orchestrator = None
        self._loop = None
        
        # Load configurable settings
        self.name = os.environ.get("JARVIS_ASSISTANT_NAME", "BR").strip()
        self.wake_word = os.environ.get("JARVIS_WAKE_WORD", "hey jarvis").strip().lower()
        self._wake_listen_timeout = 1.2
        self._wake_phrase_limit = 2.0
        self._command_timeout = 3.0
        self._command_phrase_limit = 8.0
        self._ambient_calibration = 1.0

        # Initialize Neural TTS Engine
        self.tts = NeuralTTS(voice_key="default", rate="+18%", pitch="+0Hz")
        
        # Bind manual text command submission from UI
        self.ui.on_text_command = self._on_text_command

        # Start Global Hotkeys System
        try:
            from actions.hotkeys import HotkeyManager
            self.hotkey_manager = HotkeyManager(self)
            self.hotkey_manager.start()
        except Exception as e:
            print(f"[Voice] Hotkeys failed to initialize: {e}")

    def _on_text_command(self, text: str):
        if self._loop:
            asyncio.run_coroutine_threadsafe(self.process_command(text), self._loop)

    def speak(self, text: str):
        """Speak text using the neural TTS engine with UI state sync."""
        print(f"[JARVIS] 🗣 Speak: {text}")

        def on_start():
            self.ui.speaking = True
            self.ui.set_state("SPEAKING")

        def on_finish():
            self.ui.speaking = False
            if not self.ui.muted:
                self.ui.set_state("LISTENING")

        self.tts.speak_async(text, on_start=on_start, on_finish=on_finish)

    def _tune_recognizer(self, recognizer):
        """Apply low-latency settings for wake-word and command capture."""
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.22
        recognizer.non_speaking_duration = 0.08
        recognizer.phrase_threshold = 0.08
        recognizer.energy_threshold = max(getattr(recognizer, "energy_threshold", 300), 180)
        try:
            recognizer.dynamic_energy_adjustment_damping = 0.05
            recognizer.dynamic_energy_ratio = 1.25
        except Exception:
            pass

    def _is_wake_phrase(self, text: str) -> bool:
        """Return True when transcript contains 'hey jarvis', the wake word, 'jarvis', or assistant name."""
        normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()
        if not normalized:
            return False
        
        words = normalized.split()
        wake_word = self.wake_word.lower()
        name = self.name.lower()
        
        # True if 'hey jarvis' or configured wake word is in transcript
        if "hey jarvis" in normalized or wake_word in normalized:
            return True
        if wake_word in words or name in words or name in normalized:
            return True
        if "jarvis" in words or "jarvis" in normalized:
            return True
        # Also support sound-alike variations for "jarvis"
        for w in words:
            if w in ("jarves", "jarv", "javis", "garvis", "jarvises"):
                return True
        return False

    async def _transcribe_audio(self, audio: sr.AudioData) -> str:
        """Transcribe audio using local Whisper, default backend, or Google STT fallback."""
        text = ""

        # 1. Try local Whisper first (offline STT)
        if os.environ.get("JARVIS_OFFLINE_STT", "false").lower() == "true":
            try:
                from voice.whisper_local import transcribe as whisper_transcribe, is_available as whisper_available
                from voice.multilingual import get_whisper_code
                if whisper_available():
                    lang_code = get_whisper_code()
                    text = await self._loop.run_in_executor(
                        None, lambda: whisper_transcribe(audio.get_wav_data(), language=lang_code)
                    )
            except Exception as e:
                print(f"[Voice] Local Whisper transcription failed: {e}")

        # 2. Try configured default backend (if it has transcribe method)
        if not text:
            try:
                from config.models import get_model_config
                default_name = get_model_config().get("default_backend", "gemini").lower()
                
                default_profile = AgentProfile.GEMINI
                if default_name == "gpt":
                    default_profile = AgentProfile.GPT
                elif default_name == "claude":
                    default_profile = AgentProfile.CLAUDE

                primary = self.backends.get(default_profile)
                if primary and hasattr(primary, "transcribe"):
                    text = await self._loop.run_in_executor(
                        None, lambda: primary.transcribe(audio.get_wav_data())
                    )

                if not text and default_profile != AgentProfile.GEMINI:
                    gemini = self.backends.get(AgentProfile.GEMINI)
                    if gemini and hasattr(gemini, "transcribe"):
                        text = await self._loop.run_in_executor(
                            None, lambda: gemini.transcribe(audio.get_wav_data())
                        )
            except Exception as e:
                print(f"[Voice] Primary transcription chain failed: {e}")

        # 3. Fallback to Google STT with multilingual support
        if not text:
            try:
                if hasattr(self, "r") and self.r:
                    from voice.multilingual import get_google_stt_code
                    stt_lang = get_google_stt_code()
                    text = await self._loop.run_in_executor(
                        None, lambda: self.r.recognize_google(audio, language=stt_lang).lower()
                    )
            except Exception:
                text = ""

        return text

    async def process_command(self, text: str):
        text_clean = text.strip()
        if not text_clean:
            return

        # Apply custom vocabulary corrections
        try:
            from pathlib import Path
            import json
            vocab_path = Path("config/vocabulary.json")
            if vocab_path.exists():
                vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
                corrections = vocab.get("corrections", {})
                for misheard, correct in corrections.items():
                    pattern = re.compile(r'\b' + re.escape(misheard) + r'\b', re.IGNORECASE)
                    text_clean = pattern.sub(correct, text_clean)
        except Exception as e:
            print(f"[Voice] Vocabulary correction error: {e}")

        # Match custom commands
        try:
            from actions.custom_commands import custom_command_engine
            match_res = custom_command_engine.match(text_clean)
            if match_res:
                cmd_dict, variables = match_res
                self.ui.set_state("THINKING")
                self.ui.write_log(f"Custom Command Matched: {cmd_dict['trigger']}")
                result_str = await self._loop.run_in_executor(
                    None,
                    lambda: custom_command_engine.execute(cmd_dict, variables, speak_callback=self.speak)
                )
                self.ui.write_log(f"SYS: {result_str}")
                self.ui.set_state("LISTENING")
                return
        except Exception as e:
            print(f"[Voice] Custom command execution error: {e}")

        self.ui.set_state("THINKING")
        self.ui.write_log(f"You: {text_clean}")

        low = text_clean.lower()
        if any(w in low for w in ["goodbye", "exit", "close", "stop br", "shutdown br", "stop jarvis", "shutdown jarvis"]):
            self.ui.write_log("SYS: Shutting down.")
            self.speak("Goodbye, sir.")
            await asyncio.sleep(2.5)
            os._exit(0)

        # Detect multiple parallel goals
        parallel_keywords = ["while also", "at the same time", "simultaneously", "and also"]
        is_parallel = "|" in text_clean or any(kw in low for kw in parallel_keywords)

        if is_parallel:
            goals = []
            if "|" in text_clean:
                goals = [g.strip() for g in text_clean.split("|") if g.strip()]
            else:
                split_word = next((kw for kw in parallel_keywords if kw in low), "and also")
                pattern = re.compile(re.escape(split_word), re.IGNORECASE)
                goals = [g.strip() for g in pattern.split(text_clean) if g.strip()]

            if len(goals) > 1:
                self.ui.write_log(f"SYS: Running {len(goals)} tasks in parallel...")
                self.speak("Executing multiple tasks in parallel.")

                q = get_queue()
                task_ids = q.submit_many(goals, priority=TaskPriority.NORMAL, speak=self.speak)

                for idx, tid in enumerate(task_ids):
                    self.ui.update_agent_task(tid, goals[idx][:20], "running")

                async def monitor_tasks():
                    while True:
                        all_done = True
                        for tid in task_ids:
                            status = q.get_status(tid)
                            if status and status["status"] not in ("completed", "failed", "cancelled"):
                                all_done = False
                            elif status and status["status"] == "completed":
                                self.ui.update_agent_task(tid, goals[task_ids.index(tid)][:20], "completed")
                            elif status and status["status"] == "failed":
                                self.ui.update_agent_task(tid, goals[task_ids.index(tid)][:20], "failed")
                        if all_done:
                            break
                        await asyncio.sleep(0.5)
                    self.speak("All parallel tasks completed.")
                    self.ui.set_state("LISTENING")

                asyncio.create_task(monitor_tasks())
                return

        # Single goal execution using ReAct Orchestrator loop
        try:
            response = await asyncio.to_thread(self.orchestrator.chat, text_clean)
            self.ui.write_log(f"JARVIS: {response}")
            self.speak(response)
        except Exception as e:
            err_msg = f"Error processing request: {e}"
            self.ui.write_log(f"ERR: {err_msg}")
            self.speak("Sorry, I encountered an error processing that request.")
            traceback.print_exc()

        self.ui.set_state("LISTENING")

    async def run(self):
        self._loop = asyncio.get_event_loop()

        # Initialize AI core backends
        self.ui.set_state("THINKING")
        self.ui.write_log("SYS: Initializing AI backends...")
        runtime = build_assistant_runtime()
        self.orchestrator = runtime.orchestrator
        self.backends = runtime.backends
        self.ui.write_log("SYS: JARVIS Cognitive Core online.")

        # Setup Speech Recognition
        mic_available = False
        self.r = None
        mic = None

        if _HAS_SR:
            try:
                self.r = sr.Recognizer()
                mic = SounddeviceMicrophone()
                self._tune_recognizer(self.r)
                mic_available = True
            except Exception as e:
                self.ui.write_log(f"WRN: Hands-free mic offline: {e}")
        else:
            self.ui.write_log("WRN: speech_recognition not installed. Text-only mode.")

        # Background thread: sync TTS speaking state with UI animation
        def animation_sync_loop():
            while True:
                try:
                    is_speaking = self.tts.is_speaking
                    self.ui.speaking = is_speaking
                    if is_speaking:
                        if self.ui._state != "SPEAKING":
                            self.ui.set_state("SPEAKING")
                    elif self.ui._state == "SPEAKING":
                        self.ui.set_state("LISTENING")
                except Exception:
                    pass
                time.sleep(0.05)

        threading.Thread(target=animation_sync_loop, daemon=True).start()

        self.ui.set_state("LISTENING")
        self.speak(f"{self.name} online. Neural core active. Awaiting your command.")

        # Execute custom startup commands
        try:
            from actions.custom_commands import custom_command_engine
            if custom_command_engine.startup_commands:
                self.ui.write_log("SYS: Executing startup commands...")
                for startup_cmd in custom_command_engine.startup_commands:
                    # Run startup command asynchronously
                    self._loop.call_soon_threadsafe(
                        lambda c=startup_cmd: custom_command_engine.execute({"actions": [c]}, {}, speak_callback=self.speak)
                    )
        except Exception as e:
            print(f"[Voice] Startup commands error: {e}")

        if not mic_available or not self.r or not mic:
            self.ui.write_log("SYS: Keyboard text control operational.")
            while True:
                await asyncio.sleep(1.0)

        # Open and start microphone stream globally (one-time setup)
        try:
            with mic as source:
                self.ui.write_log("SYS: Calibrating microphone noise threshold...")
                try:
                    self.r.adjust_for_ambient_noise(source, duration=self._ambient_calibration)
                    self.ui.write_log("SYS: Microphone ready. Hands-free mode active.")
                except Exception as e:
                    self.ui.write_log(f"ERR: Microphone calibration failed: {e}")

                # Wake-word passive listening loop
                while True:
                    try:
                        # Clear audio queue to ensure fresh inputs
                        while not mic.q.empty():
                            try:
                                mic.q.get_nowait()
                            except queue.Empty:
                                break

                        # Passive listening checks: only run if not speaking/muted
                        if self.ui.speaking or getattr(self.ui, "muted", False):
                            await asyncio.sleep(0.1)
                            continue

                        audio = await self._loop.run_in_executor(
                            None, lambda: self.r.listen(
                                source,
                                timeout=5.0,  # Longer timeout to reduce loop restart overhead
                                phrase_time_limit=self._wake_phrase_limit,
                            )
                        )

                        # Transcribe using configured default backend with fallbacks
                        text = await self._transcribe_audio(audio)

                        if self._is_wake_phrase(text):
                            if _HAS_WINSOUND:
                                winsound.Beep(988, 80)
                                winsound.Beep(1318, 100)

                            self.ui.set_state("LISTENING")
                            self.ui.write_log("SYS: Wake word detected. Listening...")

                            # Clear audio queue before listening to command
                            while not mic.q.empty():
                                try:
                                    mic.q.get_nowait()
                                except queue.Empty:
                                    break

                            audio_cmd = await self._loop.run_in_executor(
                                None, lambda: self.r.listen(
                                    source,
                                    timeout=self._command_timeout,
                                    phrase_time_limit=self._command_phrase_limit
                                )
                            )

                            cmd_text = await self._transcribe_audio(audio_cmd)

                            if cmd_text.strip():
                                await self.process_command(cmd_text)
                            else:
                                self.ui.set_state("LISTENING")

                    except sr.WaitTimeoutError:
                        # Expected timeout when silence, continue loop
                        pass
                    except Exception as e:
                        print(f"[Voice Loop Error]: {e}")
                        await asyncio.sleep(0.5)

        except Exception as e:
            self.ui.write_log(f"ERR: Failed to start microphone stream: {e}")
            self.ui.write_log("SYS: Keyboard text control operational.")
            while True:
                await asyncio.sleep(1.0)
