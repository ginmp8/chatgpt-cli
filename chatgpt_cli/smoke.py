"""Read-only, opt-in real-model smoke test of Codex app-server JSON-RPC.

Does not inspect local credentials. A real Codex sign-in must already exist.
Tests that substitute an app-server executable exercise transport only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from queue import Empty, Queue
import subprocess
import threading
import time
from typing import Any


class SmokeError(RuntimeError):
    """A bounded verification gate failed; never misreport this as success."""


def verify_turn(backend: str, model: str, prompt: str, cwd: str, timeout: float = 90.0) -> dict[str, Any]:
    """Run exactly one read-only turn over an official Codex app-server child."""
    if not model or model == "default" or len(model) > 200 or any(ord(ch) < 32 for ch in model):
        raise SmokeError("Choose an explicit model ID from the actual CLI catalog")
    if not prompt.strip() or len(prompt) > 4000:
        raise SmokeError("Choose a prompt with 1-4000 characters")
    if timeout < 2 or timeout > 300:
        raise SmokeError("Timeout must be between 2 and 300 seconds")
    work = Path(cwd).expanduser().resolve(strict=True)
    if not work.is_dir():
        raise SmokeError("Project path is not a directory")

    child = subprocess.Popen(
        [backend, "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1, cwd=str(work),
    )
    assert child.stdin is not None and child.stdout is not None
    messages: Queue[str | None] = Queue(maxsize=256)
    overflow = threading.Event()

    def reader() -> None:
        try:
            while not overflow.is_set():
                line = child.stdout.readline(256 * 1024 + 1)
                if not line:
                    break
                if len(line) > 256 * 1024:
                    overflow.set()
                    break
                messages.put(line)
        finally:
            messages.put(None)

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    deadline = time.monotonic() + timeout
    total = 0

    def send(message: dict[str, Any]) -> None:
        child.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        child.stdin.flush()

    def receive() -> dict[str, Any]:
        nonlocal total
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SmokeError("Codex app-server response timed out")
        try:
            item = messages.get(timeout=remaining)
        except Empty as exc:
            raise SmokeError("Codex app-server response timed out") from exc
        if overflow.is_set():
            raise SmokeError("Codex app-server frame exceeded 256 KiB")
        if item is None:
            raise SmokeError("Codex app-server exited before completing the turn")
        total += len(item)
        if total > 4 * 1024 * 1024:
            raise SmokeError("Codex app-server output exceeded 4 MiB")
        try:
            value = json.loads(item)
        except json.JSONDecodeError as exc:
            raise SmokeError("Invalid Codex JSON-RPC frame") from exc
        if not isinstance(value, dict):
            raise SmokeError("Invalid Codex JSON-RPC message")
        return value

    def require_response(request_id: int) -> dict[str, Any]:
        while True:
            message = receive()
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise SmokeError(f"Codex request {request_id} was rejected")
            result = message.get("result")
            if not isinstance(result, dict):
                raise SmokeError(f"Codex request {request_id} returned no result")
            return result

    try:
        send({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "chatgpt_cli", "title": "PandaCode CLI Smoke", "version": "0.1.0"},
        }})
        require_response(1)
        send({"method": "initialized", "params": {}})
        send({"id": 2, "method": "model/list", "params": {"limit": 100, "includeHidden": False}})
        catalog = require_response(2)
        models = catalog.get("data")
        if not isinstance(models, list) or not any(
            isinstance(entry, dict)
            and (entry.get("model") or entry.get("id")) == model
            and not entry.get("hidden", False) for entry in models
        ):
            raise SmokeError("Selected model was not returned by the CLI catalog")
        send({"id": 3, "method": "thread/start", "params": {
            "model": model, "cwd": str(work), "approvalPolicy": "never", "sandbox": "read-only",
        }})
        thread_result = require_response(3)
        remote_thread = thread_result.get("thread")
        thread_id = remote_thread.get("id") if isinstance(remote_thread, dict) else None
        if not isinstance(thread_id, str) or not thread_id:
            raise SmokeError("Codex did not provide a thread ID")
        send({"id": 4, "method": "turn/start", "params": {
            "threadId": thread_id,
            "input": [{"type": "text", "text": prompt, "text_elements": []}],
            "approvalPolicy": "never",
            "sandboxPolicy": {"type": "readOnly", "networkAccess": False},
        }})
        reply_parts: list[str] = []
        completed = False
        turn_id: str | None = None
        while not completed:
            event = receive()
            if event.get("id") == 4 and "error" in event:
                raise SmokeError("Codex rejected turn/start")
            if event.get("id") is not None and event.get("method") in {
                "item/commandExecution/requestApproval", "item/fileChange/requestApproval",
                "item/permissions/requestApproval",
            }:
                raise SmokeError("Smoke requested a tool approval; no auto-approval permitted")
            params = event.get("params", {})
            if not isinstance(params, dict):
                continue
            method = event.get("method")
            if method == "item/agentMessage/delta" and isinstance(params.get("delta"), str):
                reply_parts.append(params["delta"])
            if method == "item/completed" and not reply_parts:
                item = params.get("item", {})
                if isinstance(item, dict) and item.get("type") == "agentMessage" and isinstance(item.get("text"), str):
                    reply_parts.append(item["text"])
            if method == "turn/completed":
                turn = params.get("turn", {})
                if not isinstance(turn, dict) or turn.get("status") != "completed":
                    raise SmokeError("Codex turn did not complete successfully")
                turn_id = turn.get("id")
                completed = True
        reply = "".join(reply_parts).strip()
        if not reply:
            raise SmokeError("Codex completed with an empty assistant message")
        return {"backend": backend, "model": model, "thread_id": thread_id,
                "turn_id": turn_id, "turn_status": "completed", "reply": reply}
    except (OSError, BrokenPipeError) as exc:
        raise SmokeError("Codex app-server transport failed") from exc
    finally:
        if child.poll() is None:
            child.terminate()
        try:
            child.communicate(timeout=2)
        except (subprocess.TimeoutExpired, ValueError):
            child.kill()
            child.wait(timeout=2)
