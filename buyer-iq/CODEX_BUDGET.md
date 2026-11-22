# Codex / Work efficiency policy (English-only tickets)

- Do **not** waste allowances to prevent their periodic reset. Ordinary timed limits do not roll over. Banked promotional resets, if granted, have their own expiration and cannot be frozen by code.
- Inspect actual Settings > Usage (and Codex CLI /status or /usage) before expensive work; this repo has no permission to read the user's private limits.
- Default to existing scripts, local calculations, narrow file diffs and deterministic tests. Use Work/Codex for genuine multi-step coding/research only; one agent per scoped ticket unless evidence requires more.
- Never purchase credits, activate auto-reload, merge, publish, deploy, change production data, rotate secrets or touch REVLINE without explicit approval.
- After **two failed attempts** stop, diagnose root cause, change the approach.
- Preserve relevant logs, results, tests and small incremental/compressed backups where configured. Keep the user's computer disk and RAM clean.

Codex task template:

```text
Goal:
Target repository / branch:
Files allowed:
Files prohibited:
Scope and security constraints:
Acceptance tests / artifacts:
Budget and stop conditions:
Rollback:
Deployment: not authorized unless separately approved.
```

Always write tasks and instructions *to Codex* in English, even if the user's ChatGPT conversation is in Ukrainian.
