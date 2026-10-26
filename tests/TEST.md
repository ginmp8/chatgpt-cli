# Verification contract — chatgpt-cli

## Required semantics

The adapter must delegate app-server stdin/stdout **without rewriting JSON-RPC**,
resolve a separate official executable, reject malformed paths and self-recursion,
and never interpret model/list as proof of model entitlement.

The optional real-model smoke command must:

1. Start a real Codex app-server child.
2. Exchange initialize/initialized.
3. Retrieve model/list; require an explicit matching model ID.
4. Start a read-only thread and issue a real user turn.
5. Observe streamed assistant text and turn/completed with status=completed.
6. Fail for unavailable model, empty assistant output, a failed/interrupted turn,
   process exit, transport errors, oversized frames and timeouts.
7. Preserve credentials solely in the official Codex authentication context.
8. Log no OAuth or API credentials.

## Test inventory

- tests/test_bridge.py: five unit/subprocess tests for backend path validation,
  metadata probing and unmodified argument/stdin forwarding.
- tests/test_smoke.py: five JSON-RPC fixture tests for successful model selection,
  unlisted model rejection, failed completion, empty completion and default
  model rejection.

Tests with a fake app-server are **transport and oracle tests**; they cannot
demonstrate any real OpenAI inference or authentication.

## Executed local evidence

- 2026-10-26: \`PYTHONPATH=. python3 -m pytest -q tests\`
- Result: **10 passed in 2.55s**, Python 3.13.5, Linux sandbox.
- Run assembled in an isolated local mirror; smoke.py and test_smoke.py text
  matches the committed additions, while the existing CLI entrypoint was
  recreated locally for the execution test. Exact GitHub-checkout CI remains
  a separate gate.

## Not executed / not complete

- Official authenticated Codex app-server handshake or real model response.
- Credentialed SIWC OAuth flow, consent, login or token renewal.
- Native PandaCode Extended installation and screenshot of real Settings > Agents
  plus model selection and completed chat turn.
- Live two-turn thread continuity or multi-model entitlement.

All unexecuted gates remain **UNVERIFIED**. Never write \`PASS\` for these
based on mock tests or CLI installation.
