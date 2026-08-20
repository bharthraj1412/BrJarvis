from __future__ import annotations

import threading

from brjarvis.desktop.floating_runtime import FloatingRuntimeAdapter


class _Orchestrator:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.called = threading.Event()

    def chat(self, prompt):
        self.called.set()
        if self.error:
            raise self.error
        return self.response


def test_state_updates_are_serializable_and_subscriber_driven():
    adapter = FloatingRuntimeAdapter()
    seen = []
    unsubscribe = adapter.subscribe(seen.append)

    adapter.set_runtime("embedded_online")
    adapter.set_assistant_state("THINKING", message="Planning")
    adapter.set_connector_health("ready", [{"name": "GitHub", "configured": True}])

    snapshot = adapter.snapshot()
    assert snapshot.runtime == "embedded_online"
    assert snapshot.assistant == "processing"
    assert snapshot.connectors == "ready"
    assert snapshot.connectors_data[0]["name"] == "GitHub"
    assert seen[-1].as_dict()["connectors_data"][0]["configured"] is True

    unsubscribe()
    count = len(seen)
    adapter.set_runtime("offline")
    assert len(seen) == count


def test_submit_command_uses_orchestrator_and_recovers_to_listening():
    orchestrator = _Orchestrator({"response": "Completed response"})
    adapter = FloatingRuntimeAdapter(orchestrator=orchestrator)

    adapter.submit_command("status")
    assert orchestrator.called.wait(timeout=2)

    snapshot = adapter.snapshot()
    assert snapshot.message == "Completed response"
    assert snapshot.assistant == "listening"
    assert snapshot.task == "completed"
    assert snapshot.input == "idle"


def test_submit_command_surfaces_safe_error_state():
    orchestrator = _Orchestrator(error=RuntimeError("backend unavailable"))
    adapter = FloatingRuntimeAdapter(orchestrator=orchestrator)

    adapter.submit_command("status")
    assert orchestrator.called.wait(timeout=2)
    for _ in range(100):
        if adapter.snapshot().input == "error":
            break
        import time

        time.sleep(0.01)

    snapshot = adapter.snapshot()
    assert snapshot.assistant == "error"
    assert snapshot.task == "failed"
    assert snapshot.input == "error"
    assert snapshot.error == "backend unavailable"


def test_voice_capability_can_be_reported_unavailable():
    adapter = FloatingRuntimeAdapter()
    adapter.update(capabilities={"voice": False, "voice_to_text": False})
    adapter.trigger_voice()

    snapshot = adapter.snapshot()
    assert snapshot.audio == "unavailable"
    assert snapshot.assistant == "error"
    assert "unavailable" in snapshot.error.lower()


class _Response:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.response


def test_http_chat_uses_centralized_auth_and_maps_response(tmp_path, monkeypatch):
    monkeypatch.delenv("SERVER_API_KEY", raising=False)
    monkeypatch.delenv("JARVIS_SERVER_API_KEY", raising=False)
    api_file = tmp_path / "api_keys.json"
    api_file.write_text('{"server_api_key":"secret-test-key"}', encoding="utf-8")
    session = _Session(_Response({"response": "HTTP response"}))
    adapter = FloatingRuntimeAdapter(request_session=session, config_root=tmp_path)

    assert adapter._post_chat("hello") == {"response": "HTTP response"}
    method, url, kwargs = session.calls[0]
    assert method == "POST"
    assert url.endswith("/api/chat")
    assert kwargs["headers"]["X-API-Key"] == "secret-test-key"
    assert kwargs["headers"]["Authorization"] == "Bearer secret-test-key"
    assert kwargs["json"] == {"message": "hello"}


def test_connector_refresh_projects_ready_health():
    session = _Session(_Response({"connectors": [{"name": "GitHub", "configured": True}]}))
    adapter = FloatingRuntimeAdapter(request_session=session)
    adapter.refresh_connectors()

    for _ in range(100):
        if adapter.snapshot().connectors == "ready":
            break
        import time

        time.sleep(0.01)

    snapshot = adapter.snapshot()
    assert snapshot.connectors == "ready"
    assert snapshot.connectors_data[0]["name"] == "GitHub"
    assert session.calls[0][1].endswith("/api/connector/status")


def test_voice_callback_is_invoked_only_when_available():
    called = threading.Event()
    adapter = FloatingRuntimeAdapter(voice_trigger=called.set)

    adapter.trigger_voice()

    assert called.wait(timeout=1)
    assert adapter.snapshot().assistant == "listening"
    assert adapter.snapshot().audio == "recording"



def test_backend_pool_errors_are_converted_to_friendly_user_message():
    error = FloatingRuntimeAdapter._safe_error(RuntimeError("HTTPConnectionPool(host='127.0.0.1', port=8000): Max retries exceeded"))
    assert error == "BR JARVIS backend is not reachable. Start the backend or retry."


def test_timeout_errors_are_converted_to_listening_recovery_message():
    error = FloatingRuntimeAdapter._safe_error(RuntimeError("WaitTimeoutError: listening timed out"))
    assert error == "Listening timed out. Click MIC to try again."



def test_recent_tasks_and_continue_task_load_original_goal():
    class _TaskSession:
        def __init__(self):
            self.calls = []

        def request(self, method, url, **kwargs):
            self.calls.append(url)
            if url.endswith("/api/agent/tasks?limit=6"):
                return _Response({"tasks": [{"task_id": "task_123", "goal": "Review study notes", "status": "WAITING_FOR_USER"}]})
            return _Response({"task_id": "task_123", "goal": "Review study notes", "status": "WAITING_FOR_USER"})

    session = _TaskSession()
    adapter = FloatingRuntimeAdapter(request_session=session)
    adapter.refresh_recent_tasks()
    import time

    for _ in range(100):
        if adapter.snapshot().recent_tasks:
            break
        time.sleep(0.01)
    assert adapter.snapshot().recent_tasks[0]["task_id"] == "task_123"

    adapter.continue_task("task_123")
    for _ in range(100):
        if adapter.snapshot().transcript == "Review study notes":
            break
        time.sleep(0.01)
    assert adapter.snapshot().transcript == "Review study notes"
    assert "press Send" in adapter.snapshot().message



def test_new_command_supersedes_stale_command_response():
    class _SlowOrchestrator:
        def __init__(self):
            self.started = {}
            self.release_first = threading.Event()

        def chat(self, prompt):
            self.started[prompt] = True
            if prompt == "first":
                self.release_first.wait(timeout=1)
            return {"response": prompt}

    orchestrator = _SlowOrchestrator()
    adapter = FloatingRuntimeAdapter(orchestrator=orchestrator)
    adapter.submit_command("first")
    for _ in range(100):
        if "first" in orchestrator.started:
            break
        import time

        time.sleep(0.01)
    adapter.submit_command("second")
    for _ in range(100):
        if adapter.snapshot().latest_response == "second":
            break
        import time

        time.sleep(0.01)
    orchestrator.release_first.set()
    import time

    time.sleep(0.05)
    assert adapter.snapshot().latest_response == "second"


def test_submitting_command_stops_active_voice_capture():
    class _Voice:
        recording = True

        def stop(self):
            self.recording = False

    voice = _Voice()
    adapter = FloatingRuntimeAdapter(orchestrator=_Orchestrator({"response": "ok"}), voice_controller=voice)
    adapter.submit_command("stop listening first")
    assert voice.recording is False



def test_voice_transcript_is_refined_before_project_submission():
    class _Voice:
        available = True
        recording = False

        def start(self, **kwargs):
            kwargs["on_transcript"]("make a study plan tomorrow")

        def stop(self):
            return False

    orchestrator = _Orchestrator({"response": "project task accepted"})
    refined = []
    adapter = FloatingRuntimeAdapter(
        orchestrator=orchestrator,
        voice_controller=_Voice(),
        refiner=lambda draft: refined.append(draft) or "Create a study plan for tomorrow with three focused sessions.",
    )
    adapter.trigger_voice()
    assert orchestrator.called.wait(timeout=2)
    for _ in range(100):
        if adapter.snapshot().latest_response == "project task accepted":
            break
        import time

        time.sleep(0.01)
    assert refined == ["make a study plan tomorrow"]
    assert adapter.snapshot().latest_response == "project task accepted"


def test_workspace_starts_backend_before_handoff():
    started = []
    probe_results = iter([False, True])

    class _WorkspaceResponse(_Response):
        def __init__(self):
            super().__init__({"url": "http://127.0.0.1:8000/web/?handoff=token"}, status_code=200)

    class _WorkspaceSession:
        def request(self, method, url, **kwargs):
            return _WorkspaceResponse()

    ready = threading.Event()
    adapter = FloatingRuntimeAdapter(
        request_session=_WorkspaceSession(),
        backend_probe=lambda: next(probe_results, True),
        backend_starter=lambda: started.append(True),
    )
    adapter.request_workspace_handoff(on_ready=lambda url: ready.set())
    assert ready.wait(timeout=2)
    assert started == [True]
    assert adapter.snapshot().workspace == "ready"
