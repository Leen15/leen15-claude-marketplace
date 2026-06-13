#!/usr/bin/env python3
"""UserPromptSubmit hook: when the live context grows large, inject a note
telling Claude to suggest /handoff (save a resume brief) then /clear.

Context size is read from the most recent assistant `usage` in the transcript
(input + cache_read + cache_creation), which is the real per-turn context cost.
Anti-nag: only fires once per THRESHOLD crossing, then again only after the
context has grown by RENAG_STEP more tokens (state kept per session in /tmp).
"""
import json
import os
import sys

THRESHOLD = 200_000      # tokens of live context before we suggest /handoff
RENAG_STEP = 50_000      # only remind again after this much further growth


def read_stdin_json():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def latest_context_tokens(transcript_path):
    """Sum input+cache_read+cache_creation of the last assistant usage block."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return None
    try:
        with open(transcript_path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except Exception:
        return None
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        usage = (obj.get("message") or {}).get("usage") or obj.get("usage")
        if not usage:
            continue
        return (
            usage.get("input_tokens", 0)
            + usage.get("cache_read_input_tokens", 0)
            + usage.get("cache_creation_input_tokens", 0)
        )
    return None


def already_reminded_recently(session_id, tokens):
    """True if we should stay silent (reminded recently and not much growth)."""
    if not session_id:
        return False
    state = os.path.join("/tmp", f"claude-handoff-reminder-{session_id}")
    last = None
    try:
        with open(state, "r") as fh:
            last = int(fh.read().strip())
    except Exception:
        last = None
    if last is not None and tokens < last + RENAG_STEP:
        return True
    try:
        with open(state, "w") as fh:
            fh.write(str(tokens))
    except Exception:
        pass
    return False


def main():
    data = read_stdin_json()
    tokens = latest_context_tokens(data.get("transcript_path"))
    if tokens is None or tokens < THRESHOLD:
        sys.exit(0)
    if already_reminded_recently(data.get("session_id"), tokens):
        sys.exit(0)

    k = round(tokens / 1000)
    note = (
        f"[handoff-reminder] La conversazione ha ~{k}k token di contesto vivo "
        f"(soglia {THRESHOLD // 1000}k). Il costo è quasi tutto cache-read e cresce "
        f"a ogni turno. Suggerisci all'utente, in una riga, di salvare lo stato con "
        f"/handoff e poi fare /clear (o /compact) per ripartire leggero senza perdere "
        f"il filo. Non eseguire tu i comandi: proponili e lascia decidere all'utente."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": note,
        },
        "suppressOutput": True,
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
