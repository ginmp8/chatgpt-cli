# chatgpt-cli — PandaCode Codex bridge

Opt-in, local passthrough to the **official Codex CLI** for PandaCode Extended. This does **not** run the ChatGPT website conversation as a local agent, extract cookies, store keys, or bypass authentication.

## Installation

Python 3.10+ and an independently installed official Codex CLI are prerequisites.

```sh
python -m pip install .
export CHATGPT_CLI_CODEX_BIN=/absolute/path/to/official/codex
chatgpt-cli --json agent status
```

Status deliberately reports `authenticated: not_checked`. Authenticate Codex with its own supported flow.

In PandaCode Extended use **Settings > Providers > Codex > Executable location** to point to `chatgpt-cli` and then **Settings > Agents > Refresh agents**.

The `chatgpt-cli app-server --enable goals` command uses process replacement (`os.execv`), delegating all JSON-RPC, stdin/stdout, permissions and credentials directly to Codex. Test: `python -m pytest -v tests`. A real authenticated app-server handshake and desktop screenshot have not yet been verified.

Methodology: CLI-Anything main snapshot at ChatGPT Library `/_external/cli-anything/snapshot-2026-10-26/CLI-Anything-main.zip`. See [issue #1](https://github.com/ginmp8/chatgpt-cli/issues/1).


## Proof of a real model reply (optional; requires authenticated official Codex)

The CLI now has a bounded, **read-only** JSON-RPC smoke test that explicitly selects
a model returned by the installed Codex catalog and requires an assistant response
plus the completed turn status. First complete the official Codex sign-in on the
same machine. Replace the model ID below with one returned by that account's
Codex model selector:

~~~sh
chatgpt-cli --json smoke \
  --model MODEL_ID_FROM_CODEX \
  --prompt "Reply with exactly: PANDACODE_REAL_MODEL_OK" \
  --cwd . --timeout 90
~~~

A successful test outputs the requested model ID, thread/turn identifiers,
\`turn_status=completed\`, and a nonempty response. This is a **real inference
test only when run against the official Codex executable with an authorized
account**. Test fixtures are explicitly not model inference. A CLI smoke pass
also does not replace the required PandaCode Extended native UI chat test.

Official [Sign in with ChatGPT / Codex app-server](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)
is a conditional option if the account/workspace can grant the plan-usage scopes.
It creates a new session, **not** a connection to this ChatGPT conversation's
private runtime or history. No SIWC OAuth token-sharing implementation is
included in this draft.

The separate [Workspace Agents trigger API](https://learn.chatgpt.com/workspace-agents/trigger-runs)
does not expose the generated answer to API callers and cannot provide the
streaming chat transport required here.

**Local verification evidence:** Five JSON-RPC smoke fixture tests passed
(\`PYTHONPATH=. pytest -q tests/test_smoke.py\`). The CLI repository's
existing five passthrough tests are separate. Authenticated inference,
native UI capture and end-to-end provider testing remain unverified.
