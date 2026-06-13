# leen15-claude-marketplace

Personal [Claude Code](https://claude.com/claude-code) plugin marketplace.

## Plugins

### `handoff`

Cold-start **resume briefs** plus an automatic context reminder.

- **`/handoff [save] | resume [ticket] | list`** — save a compact brief of the
  current session (decisions, dead ends, next steps) outside the repo at
  `~/.claude/handoff/<repo>/<ref>.md`, so you can `/clear` and resume cold with
  one line. Resume and list modes read those briefs back.
- **Context reminder hook** (`UserPromptSubmit`) — when the live context grows
  past ~200k tokens, injects a note so Claude suggests saving a brief before
  `/clear`. Anti-nag: fires once per threshold, then only after +50k more.

## Install (teammates)

```
/plugin marketplace add <git-url-of-this-repo>
/plugin install handoff@leen15-claude-marketplace
```

Replace `<git-url-of-this-repo>` with the SSH/HTTPS URL once it's pushed
(e.g. `git@github.com:leen15/leen15-claude-marketplace.git`), or use
`leen15/leen15-claude-marketplace` for a public GitHub repo.

After install the skill is available as `/handoff:handoff` (or just `/handoff`).
The hook requires a one-time approval per teammate the first time it runs.

### Updating

```
/plugin marketplace update leen15-claude-marketplace
```

## Layout

```
.claude-plugin/marketplace.json      catalog (lists plugins + source paths)
plugins/handoff/
  .claude-plugin/plugin.json         plugin manifest
  skills/handoff/SKILL.md            the /handoff skill
  hooks/hooks.json                   UserPromptSubmit -> scripts/handoff-reminder.py
  scripts/handoff-reminder.py        context-size reminder (uses ${CLAUDE_PLUGIN_ROOT})
```

## Notes

- Hook script paths use `${CLAUDE_PLUGIN_ROOT}` so they work from any install location.
- Briefs are written under the user's home (`~/.claude/handoff/`), never inside a repo.
