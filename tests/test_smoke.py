import textwrap
import pytest
from chatgpt_cli.smoke import verify_turn, SmokeError


FAKE = '''#!/usr/bin/env python3
import json, sys
for line in sys.stdin:
    q = json.loads(line)
    key = q.get("id")
    if key == 1:
        print(json.dumps({"id": 1, "result": {}}), flush=True)
    elif key == 2:
        print(json.dumps({"id": 2, "result": {"data": [{"model": "gpt-test", "displayName": "Test Model"}]}}), flush=True)
    elif key == 3:
        print(json.dumps({"id": 3, "result": {"thread": {"id": "th-1"}, "model": q["params"]["model"]}}), flush=True)
    elif key == 4:
        assert q["params"]["threadId"] == "th-1"
        assert q["params"]["sandboxPolicy"]["type"] == "readOnly"
        print(json.dumps({"id": 4, "result": {"turn": {"id": "turn-1"}}}), flush=True)
        if q["params"]["input"][0]["text"] == "simulate-failed":
            print(json.dumps({"method": "turn/completed", "params": {"turn": {"id": "turn-1", "status": "failed"}}}), flush=True)
        elif q["params"]["input"][0]["text"] == "simulate-empty":
            print(json.dumps({"method": "turn/completed", "params": {"turn": {"id": "turn-1", "status": "completed"}}}), flush=True)
        else:
            print(json.dumps({"method": "item/agentMessage/delta", "params": {"delta": "PANDACODE_REAL_MODEL_OK"}}), flush=True)
            print(json.dumps({"method": "turn/completed", "params": {"turn": {"id": "turn-1", "status": "completed"}}}), flush=True)
'''


def fake(tmp_path):
    path = tmp_path / "fake-codex"
    path.write_text(FAKE)
    path.chmod(0o700)
    return str(path)


def test_stdin_roundtrip_and_model_identity(tmp_path):
    result = verify_turn(fake(tmp_path), "gpt-test", "test prompt", str(tmp_path), timeout=5)
    assert result == {"backend": str(tmp_path / "fake-codex"), "model": "gpt-test", "thread_id": "th-1", "turn_id": "turn-1", "turn_status": "completed", "reply": "PANDACODE_REAL_MODEL_OK"}


def test_unlisted_model_is_not_success(tmp_path):
    with pytest.raises(SmokeError, match="catalog"):
        verify_turn(fake(tmp_path), "not-available", "test", str(tmp_path), timeout=5)


def test_failed_turn_is_not_success(tmp_path):
    with pytest.raises(SmokeError, match="did not complete"):
        verify_turn(fake(tmp_path), "gpt-test", "simulate-failed", str(tmp_path), timeout=5)


def test_empty_completion_is_not_success(tmp_path):
    with pytest.raises(SmokeError, match="empty"):
        verify_turn(fake(tmp_path), "gpt-test", "simulate-empty", str(tmp_path), timeout=5)


def test_model_must_be_explicit(tmp_path):
    with pytest.raises(SmokeError, match="explicit"):
        verify_turn(fake(tmp_path), "default", "test", str(tmp_path), timeout=5)
