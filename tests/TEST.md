# Test contract

The adapter must delegate app-server without rewriting JSON-RPC, require an executable Codex backend, reject self-recursion, report authentication as unknown and retain the official backend's permissions. No mock is proof of real Codex authentication.

## Planned
- Unit tests: configuration resolution, missing/non-executable/relative path, recursion, status output.
- Subprocess: version/help, JSON status, transparent exec of a fake executable under a temporary directory.
- Integration (requires official authenticated Codex): JSON-RPC initialize/model-list handshake and actual PandaCode Extended Settings > Agents screenshot. Not complete until executed against the real backend.

## Current evidence
Not yet executed in an authenticated Codex/PandaCode runtime.
