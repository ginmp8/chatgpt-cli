# Test contract

The adapter must delegate app-server without rewriting JSON-RPC, require an executable Codex backend, reject self-recursion, report authentication as unknown and retain the official backend's permissions. No mock is proof of real Codex authentication.

## Planned
- Unit tests: configuration resolution, missing/non-executable/relative path, recursion, status output.
- Subprocess: version/help, JSON status, transparent exec of a fake executable under a temporary directory.
- Integration (requires official authenticated Codex): JSON-RPC initialize/model-list handshake and actual PandaCode Extended Settings > Agents screenshot. Not complete until executed against the real backend.

## Current evidence
2026-10-26: Five focused Python tests passed in an isolated Linux Python 3.11+ environment: `PYTHONPATH=. python3 -m pytest -q tests/test_bridge.py` (`5 passed in 0.91s`). The local test copy was recreated from the exact committed Python code and test contents. The subprocess integration test used a synthetic executable intentionally; this verifies argv/stdin passthrough only, not Codex protocol compatibility or authentication.

Native authenticated Codex app-server handshake, PandaCode Extended build and Settings > Agents screenshot remain unverified. No CI for this repository was observed.
