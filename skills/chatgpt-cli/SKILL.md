---
name: chatgpt-cli
description: Use an existing official Codex CLI via a transparent local app-server adapter in PandaCode Extended. Inspect executable status and configure a separate absolute backend path; never extract ChatGPT web cookies, claim browser-session access or bypass CLI permissions.
---

# ChatGPT CLI for PandaCode

Requires an officially installed and authenticated Codex CLI. This tool is a passthrough, not the ChatGPT web agent.

`CHATGPT_CLI_CODEX_BIN=/absolute/path/to/codex chatgpt-cli --json agent status`

To configure PandaCode Extended: Settings > Providers > Codex > Executable location, select the installed `chatgpt-cli` executable, save, then Settings > Agents > Refresh agents. Confirm status from an actual desktop build. No binary-only detection proves login.

`chatgpt-cli app-server --enable goals` delegates to `codex app-server --enable goals` using process replacement; protocol and authorization remain under Codex.
