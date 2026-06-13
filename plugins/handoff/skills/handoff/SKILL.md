---
name: handoff
description: Save a cold-start resume brief of the current session before /clear, or resume from one. Use when the conversation has grown long on a deep/complex task and you want to reset context without re-explaining. Usage: /handoff [save] | /handoff resume [ticket] | /handoff list
---

Manage **handoff briefs**: compact, cold-start documents that let a fresh session resume a long/complex task without re-explaining anything. The brief captures the *conversation state* (decisions, dead ends, next steps) and lives **outside the repo**, separate from the user's in-repo task file under `docs/`.

## Storage location (outside any repo)

Briefs are stored per-repo under the user's home, NOT inside the project:

```
~/.claude/handoff/<repo>/<ticket>.md
```

- `<repo>` = basename of `git rev-parse --show-toplevel` (fallback: basename of the current working directory).
- `<ticket>` = derived in **Step 0** below.

Never write a brief inside the repo. The in-repo `docs/` task file is the user's own; the skill references it but never overwrites it.

## Step 0 — resolve repo and ticket (every mode)

Run, in one block:

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
REPO=$(basename "$ROOT")
BRANCH=$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null)
echo "repo=$REPO branch=$BRANCH"
```

Derive a **proposed** `<ticket>`:
1. If `$ARGUMENTS` contains an explicit ticket after the subcommand, use it.
2. Else extract a ticket code from `$BRANCH` — the first match of `[A-Z]+-[0-9]+` (e.g. `feature/CNTPL-920-expand-opensearch` → `CNTPL-920`).
3. Else use the branch name with `/` replaced by `-` (e.g. `develop` → `develop`).

**Always confirm the reference with the user before using it** — never assume it silently. The ticket from the branch is often NOT the actual task discussed this session (e.g. meta-work on a CNTPL-920 branch). Ask explicitly, e.g.:

> Userei `<proposed-ticket>` come riferimento per il brief (da branch `<branch>`). Va bene, o preferisci un altro nome? Il lavoro di questa sessione mi sembra riguardare: `<short description of what THIS session was actually about>`.

If what the session actually covered differs from the branch ticket, say so and propose a content-based slug instead (e.g. `token-cost-and-handoff-skill`). Use the name the user confirms. In `resume`/`list` modes, if multiple briefs exist and the reference is ambiguous, confirm which one before reading.

The brief path is `~/.claude/handoff/$REPO/<confirmed-ref>.md`. Create `~/.claude/handoff/$REPO/` with `mkdir -p` before writing.

## Parse `$ARGUMENTS`

First token = subcommand. If empty, default to `save`.
- `save` (or empty) → **Save mode**
- `resume` → **Resume mode**
- `list` → **List mode**

---

## Save mode

Goal: dump everything needed to resume this task cold into the brief file, so the user can `/clear` and continue with a one-line prompt.

1. Resolve repo/ticket (Step 0) and `mkdir -p ~/.claude/handoff/$REPO/`.
2. If the brief already exists, read it first and **update** it (preserve still-valid Decisions/Pitfalls, don't lose history) rather than blindly overwriting.
3. Look for the user's in-repo task file (commonly `docs/wip-*.md`, `docs/<ticket>*.md`, or whatever they mentioned this session). If found, reference its path under **Key files** — do NOT duplicate its content into the brief.
4. Write the brief using this exact template, filled from the **current conversation**. Be concrete and specific — this is read by a fresh session with zero memory.

```markdown
# <ticket> — <one-line task title>
_Updated: <output of `date '+%Y-%m-%d %H:%M'`> · repo: <repo> · branch: <branch>_

## Objective
<2-3 lines: what we are ultimately trying to achieve>

## Current state
<where things stand right now: what works, what is in progress, what is broken>

## Decisions + why
<every non-obvious choice made this session and the reason — so it is not re-litigated>

## Next steps
<ordered, actionable list — what to do next, most specific first>

## Key files
<path:line — why it matters. Include the in-repo docs/ task file if present.>

## Pitfalls / dead ends
<approaches already tried and rejected, gotchas, constraints, things that look wrong but are intentional>

## Open questions
<anything unresolved that may need the user's input>
```

5. After writing, print to the user, verbatim, a ready-to-use resume block:

```
Brief salvato in ~/.claude/handoff/<repo>/<ticket>.md

Ora fai /clear, poi incolla:
  /handoff resume <ticket>
```

Do not run `/clear` yourself — it is the user's action.

## Self-check before finishing Save

Ask yourself: "If I had zero memory of this conversation, could I resume from this file alone?" If any answer would force the user to re-explain something, add it to the relevant section. The **Decisions + why** and **Pitfalls** sections are where hard-to-re-explain context lives — bias toward over-capturing there.

---

## Resume mode

Goal: silently reload the saved context so work can continue. This is a **drop-in replacement for `/compact`**, NOT a status meeting. Restore the context, acknowledge in one line, then stop and wait for the user.

1. Resolve repo/ticket (Step 0).
2. Read `~/.claude/handoff/$REPO/<ticket>.md` into context. If it does not exist, run List mode and ask which brief to use.
3. Also read the in-repo task file it references under **Key files**, if any.
4. Output **at most one short line** confirming what was reloaded — e.g. `Contesto ripreso da <ticket> (branch <branch>). Dimmi come procedere.` Do NOT reproduce the brief: no recap, no decisions list, no next-steps dump, no tables, no question.
5. Do NOT proactively ask the Open questions or propose next steps. The brief now lives in your context — use it to answer the user's next message. Ask a question only if the user's explicit request genuinely cannot be carried out without it.

**For the rest of the conversation after a resume:** behave normally. Do not re-summarize state, re-list next steps, or ask "how do you want to proceed" unless the user explicitly asks for a recap. Resume loads context; it does not report on it.

---

## List mode

```bash
ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd); REPO=$(basename "$ROOT")
ls -lt ~/.claude/handoff/"$REPO"/ 2>/dev/null
```

Print the available briefs for this repo (filename + last-modified). If the directory is empty or missing, say there are no briefs yet for `<repo>`.
