import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
from click.testing import CliRunner

from chatgpt_cli.main import cli, resolve_backend


def test_missing_backend(monkeypatch):
    monkeypatch.delenv("CHATGPT_CLI_CODEX_BIN", raising=False)
    monkeypatch.setattr("shutil.which", lambda name: None)
    with pytest.raises(Exception, match="missing"):
        resolve_backend()


def test_relative_path_rejected(monkeypatch):
    monkeypatch.setenv("CHATGPT_CLI_CODEX_BIN", "relative/codex")
    with pytest.raises(Exception, match="absolute"):
        resolve_backend()


def test_invalid_executable_rejected(monkeypatch, tmp_path):
    path = tmp_path / "codex"
    path.write_text("x")
    monkeypatch.setenv("CHATGPT_CLI_CODEX_BIN", str(path))
    with pytest.raises(Exception, match="executable"):
        resolve_backend()


def test_status_uses_real_version_probe(monkeypatch, tmp_path):
    backend = tmp_path / "codex"
    backend.write_text("#!/bin/sh\necho 'codex-cli 0.test'\n")
    backend.chmod(0o700)
    monkeypatch.setenv("CHATGPT_CLI_CODEX_BIN", str(backend))
    result = CliRunner().invoke(cli, ["--json", "agent", "status"])
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["version"] == "codex-cli 0.test"
    assert data["authenticated"] == "not_checked"


def test_passthrough_preserves_argv_and_stdin(tmp_path):
    backend = tmp_path / "codex"
    backend.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\ncat\n")
    backend.chmod(0o700)
    env = {**os.environ, "CHATGPT_CLI_CODEX_BIN": str(backend)}
    output = subprocess.run([sys.executable, "-m", "chatgpt_cli", "app-server", "--enable", "goals"],
        input='{"id":1,"method":"initialize"}\n', text=True, capture_output=True, env=env, timeout=5)
    assert output.returncode == 0
    assert output.stdout == 'app-server\n--enable\ngoals\n{"id":1,"method":"initialize"}\n'
