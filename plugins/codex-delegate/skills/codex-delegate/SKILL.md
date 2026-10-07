---
name: codex-delegate
description: Delegate a well-scoped task to the Codex CLI (GPT) running non-interactively, then review only its short final message and the git diff. Use to save Claude context tokens on exploratory or mechanical work with clear acceptance criteria (sweeping many files, repetitive edits across many files, end-to-end checks with curl/docker, digging through logs). Not for tiny edits or tasks that need decisions from the user. Usage: /codex-delegate <task description>
---

Delegate work to **Codex CLI** (GPT) as a worker. Codex spends its own tokens on reading files, running commands and retrying; Claude only pays for writing the prompt and reading back a compact result. Claude stays responsible for the decision, the review and the final verification.

## When to delegate

Good fit (tell the user in one line that you are delegating, then do it):
- exploration with a compact answer (search many files, collect data from logs);
- mechanical edits across many files with a clear rule;
- end-to-end verification on a local stack (curl, docker, DB checks) with explicit pass/fail criteria.

Do it yourself instead when:
- the change is a few lines (prompt + review would cost as much);
- the task needs decisions or approvals from the user mid-way (Codex cannot ask);
- it touches production, real credentials or secrets.

## Step 1 — write the prompt to a file

Write the prompt in English to `${TMPDIR:-/tmp}/codex-delegate/<task-name>-prompt.txt` (create the directory). Always include:

1. **Repo and rules**: "Work in the <repo> repo. Read AGENTS.md (or CLAUDE.md) and follow it."
2. **Non-interactive**: "You are running non-interactively: you cannot ask questions. If something blocks you, stop and report it."
3. **Context you already have**: the facts Codex needs, already verified, so it does not re-investigate ("do not re-investigate").
4. **Scope**: exact files it may change; what it must not touch. If it must not fix code on failure, say "report, do not fix".
5. **Approvals, explicit and narrow**: any local writes the user approved for this task only (e.g. "create a temporary user, delete it at the end, confirm cleanup with a query"). Never give real passwords or production access: use temporary test data.
6. **Acceptance criteria**: a checklist with what evidence to show for each item.
7. **Git**: "Do not commit or push."
8. **Final message format**: "Final message (it is all the reviewer will read): under 25 lines, in <user's language>: result of each check with evidence, cleanup confirmation, files changed."

## Step 2 — run it in the background

```bash
bash "<this skill's base directory>/run.sh" "<repo_dir>" "<prompt_file>" "<task-name>"
```

Run it with the Bash tool and `run_in_background: true` (tasks take minutes). You are notified when it ends; do not poll. The script:
- runs `codex exec -C <repo> --approve-for-me -o <summary> "<prompt>" < /dev/null` (stdin must be closed, otherwise Codex hangs on "Reading additional input from stdin...");
- uses the user's Codex config for model and reasoning effort; extra flags go in `CODEX_DELEGATE_ARGS`;
- prints only: exit code, elapsed time, tokens used by Codex, Codex's final message, `git status --short`, `git diff --stat`, and the path of the full log.

## Step 3 — review (mandatory)

- Read the script output. **Do not read the full log** unless the final message is missing or something does not add up.
- Read the actual `git diff` of the changed code files (not only the stat) and check it against the scope.
- Verify side effects yourself with one cheap check (e.g. the cleanup query, a lint run, a curl) instead of trusting the summary.
- Report to the user: outcome, what you checked yourself, files changed, tokens used by Codex. Do not commit unless the user asks.

If Codex went out of scope or failed, say so plainly; fix the prompt and rerun, or do the task yourself.
