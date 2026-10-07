#!/usr/bin/env bash
# Run a Codex CLI task non-interactively and print only what the reviewer needs:
# Codex's final message, the repo's git status/diff stat and the tokens Codex used.
#
# Usage: run.sh <repo_dir> <prompt_file> [task_name]
# Extra codex flags can be passed via CODEX_DELEGATE_ARGS (e.g. "-m gpt-6-sol").
set -u

repo="${1:?usage: run.sh <repo_dir> <prompt_file> [task_name]}"
prompt_file="${2:?usage: run.sh <repo_dir> <prompt_file> [task_name]}"
name="${3:-task}"

command -v codex >/dev/null 2>&1 || { echo "codex CLI not found in PATH"; exit 127; }
[ -d "$repo" ] || { echo "repo dir not found: $repo"; exit 2; }
[ -s "$prompt_file" ] || { echo "prompt file missing or empty: $prompt_file"; exit 2; }

out_dir="${TMPDIR:-/tmp}/codex-delegate"
mkdir -p "$out_dir"
stamp="$(date +%Y%m%d-%H%M%S)"
summary="$out_dir/$name-$stamp.md"
log="$out_dir/$name-$stamp.log"

start=$(date +%s)
# stdin MUST be closed: otherwise `codex exec` waits forever on
# "Reading additional input from stdin...".
# shellcheck disable=SC2086
codex exec -C "$repo" --approve-for-me ${CODEX_DELEGATE_ARGS:-} \
  -o "$summary" "$(cat "$prompt_file")" < /dev/null > "$log" 2>&1
status=$?
elapsed=$(( $(date +%s) - start ))

echo "=== codex exit=$status elapsed=${elapsed}s"
echo "=== tokens used by codex: $(grep -A1 'tokens used' "$log" | tail -1)"
echo "=== final message ($summary)"
if [ -s "$summary" ]; then cat "$summary"; else echo "(no final message; last log lines below)"; tail -20 "$log"; fi
echo
if git -C "$repo" rev-parse --git-dir >/dev/null 2>&1; then
  echo "=== git status"
  git -C "$repo" status --short
  echo "=== git diff --stat"
  git -C "$repo" diff --stat
fi
echo "=== full log (do not read unless needed): $log"
exit $status
