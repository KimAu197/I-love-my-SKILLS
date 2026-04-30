# 🧠 I-LOVE-MY skills

A growing collection of personal skills for [Claude](https://claude.ai) — built to eliminate friction from my daily workflows.

> Skills are custom instructions that teach Claude how to handle specific tasks. Drop them into Claude Code or Claude Desktop and they just work.

---

## Skills

### 📚 [learn-what-you-learn](./learn-what-you-learn/)

> Zero-friction learning companion — throw any content at it and it handles the rest.

Point it at anything — a URL, PDF, local file, or YouTube link — and it will:
- Ingest the content automatically (no copy-paste)
- Give you a summary and save it straight to Notion
- Let you ask questions, with every Q&A silently saved to Notion as you go
- Accept `note: your thought` to capture your own ideas

No manual saving. No copy-pasting. Just learn.

**Supports:** Web URLs · PDFs · Local files · HTML · YouTube (via transcript) · Pasted text

```bash
/learn-what-you-learn https://example.com/article
/learn-what-you-learn /path/to/paper.pdf
/learn-what-you-learn  # then drop a file or paste content
```

**Setup:** Requires `NOTION_API_KEY` and `NOTION_LEARNING_PAGE_ID` env vars.
See [`learn-what-you-learn/README.md`](./learn-what-you-learn/README.md) for full setup instructions.

### 🎯 [task-clarification](./task-clarification/)

> Transform vague intent into execution-ready plans before any implementation begins.

Point it at any under-specified request and it will:
- Restate the goal as a precise objective
- Surface gaps, missing context, and hidden assumptions
- Produce a structured execution spec and a final prompt a downstream agent can run directly

Scales verbosity to uncertainty — compact output for clear tasks, full breakdown for ambiguous ones.

**Use when:** A request is broad, partially described, or needs a clean handoff to another agent.
**Skip when:** The task is already precise or clarification overhead isn't worth it.

```bash
/task-clarification "help me build an agent for this workflow"
/task-clarification "fix this code"
/task-clarification "I want a better prompt for this task"
```

### [domino](./domino/)

> End-to-end Cursor workflow orchestration from one skill entry point.

Domino turns a large task into a managed workflow inside Cursor. It can plan tasks, dispatch subagents, continue through hooks, verify results, and persist lightweight project memory.

It installs:
- The Cursor skill at `~/.cursor/skills/domino`
- Helper scripts under `~/.cursor/skills/domino/scripts`
- Hook scripts under `~/.cursor/hooks`
- Hook entries in `~/.cursor/hooks.json`

```bash
cd skills/domino
./sync.sh
```

After syncing, restart or reload Cursor so the skill and hooks are available.

Use it by asking Cursor to use the `domino` skill for a multi-step task. Domino coordinates planning, workers, verification, and memory through one workflow — you do not need separate commands for each phase.

**Recent behavior and documentation updates:**

- **Hooks:** Raised default `loop_limit` on Domino hook entries so long runs (many tasks plus verify and memory-save phases) are less likely to stop mid-chain; SKILL explains when to raise further or split sessions.
- **Worker results:** Continuations point at `.cursor/tasks/task-*.md` and the `## Result` section as the source of truth; large summaries are not relied on from chat. Runtime stores pointer-style `last_worker_summary` when a task id exists.
- **Worker failure:** If a subagent exits without `completed`, runtime returns to `running` and the hook submits a continuation aimed at Debugger or repair planning (not a silent stall).
- **Stuck detection:** `last_dispatch_at_ms` on dispatch; `domino_runtime.py check-stuck` and `read-state --stuck-after-minutes` detect workflows stuck in `waiting_for_worker`.
- **Hybrid workflows:** For mixed serial-then-parallel work, `domino-plan.md` uses `## Chosen Strategy` = `Hybrid` and mandatory `## Phases` (per-phase strategy, dependencies, exit conditions); parallel segments use `parallel-plan.md` and the **Parallel wave execution** rules in the skill.
- **Current phase:** Optional `current_phase` in `domino-runtime.json`, set with `set-current-phase`; subagent and stop hook continuations append the active phase label when set so orchestration knows which segment is live.

Runtime helpers include `ensure`, `start`, `read-state`, `mark-dispatch`, `set-status`, `set-current-phase`, `check-stuck`, `complete`, `next-task`, and `normalize-result`. Full contracts are in [SKILL.md](./domino/skills/domino/SKILL.md) and [reference.md](./domino/skills/domino/reference.md).

---

## How to install a skill

**Claude Code:**
```bash
claude skill install ./learn-what-you-learn
```

**Claude Desktop / Claude.ai:**
Download the `.skill` file from [Releases](../../releases) and drag it into your skills panel.

**Cursor Domino:**
```bash
git clone https://github.com/KimAu197/I-love-my-SKILLS.git
cd I-love-my-SKILLS/skills/domino
./sync.sh
```

The sync script is safe to rerun. It overwrites the local Domino skill files and hook scripts, then merges Domino hook entries into `~/.cursor/hooks.json` while preserving unrelated hook configuration.

To verify the install:
```bash
ls ~/.cursor/skills/domino
ls ~/.cursor/hooks
```

You should see `SKILL.md`, `reference.md`, `examples.md`, `scripts/domino_runtime.py`, `domino-stop.py`, and `domino-subagent-stop.py`.

---

## Updating and contributing

If you test Domino on another machine and find an issue, update the source files in this repository, rerun `./sync.sh`, test again, then push the fix back to GitHub.

Typical workflow:

```bash
git pull
cd skills/domino
./sync.sh

# edit files under skills/domino/
./sync.sh
# test in Cursor

cd ../..
git status
git add skills/domino skills/README.md
git commit -m "fix: Improve Domino workflow behavior"
git push
```

If you cloned the repo with write access, `git push` updates the original repository directly. If you do not have write access, fork the repo and open a pull request.

Domino may create runtime files such as `.cursor/domino-plan.md`, `.cursor/domino-runtime.json`, `.cursor/tasks/task-*.md`, `.cursor/project_state.md`, and `.cursor/context_summary.md` inside the workspace being tested. Treat those as task runtime state, not skill source code, unless you intentionally want to save an example.

---

## Roadmap

More skills coming as I build them. Ideas I'm exploring:
- 📋 Meeting notes → action items → Notion
- 🔍 Research assistant with auto-citation
- ✍️ Writing coach grounded in my own style

---

*Built by [Jinzi](https://github.com/KimAu197) · Made with Claude*