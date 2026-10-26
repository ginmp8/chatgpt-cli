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
