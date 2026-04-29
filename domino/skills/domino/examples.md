# Domino Examples

## Example 1: New Sequential Run

User message:

```text
Build a small evaluation pipeline for dataset X using Domino.
```

Expected flow:

1. Domino resolves the workspace root.
2. Domino initializes `.cursor/domino-runtime.json`.
3. Domino dispatches the `Planner` role.
4. Before dispatch, Domino marks:

```bash
python3 ~/.cursor/skills/domino/scripts/domino_runtime.py mark-dispatch --workspace "<workspace-root>" --role "planner" --task-id "plan-001"
```

5. The `subagentStop` hook auto-submits a continuation message.
6. Domino reads the task queue and dispatches the next worker.

## Hybrid sketch (serial then parallel)

1. In `.cursor/domino-plan.md`, set `## Chosen Strategy` to **`Hybrid`** and add **`## Phases`** (each phase: strategy type, dependencies, exit conditions). For parallel segments, point to `.cursor/parallel-plan.md` when it exists.
2. When switching into a new phase (especially a parallel segment), update the runtime mirror:

```bash
python3 ~/.cursor/skills/domino/scripts/domino_runtime.py set-current-phase --workspace "<workspace-root>" --phase "Phase 2 — Parallel experiments"
```

3. Automatic hook continuations append `Current phase (runtime current_phase): ...` when this field is set.

## Example 2: Automatic Continuation After Worker Completion

The `subagentStop` hook should emit a follow-up like:

```text
Continue the active Domino workflow in this workspace. A worker subagent just completed successfully. Read `.cursor/domino-plan.md`, `.cursor/domino-runtime.json`, and `.cursor/tasks/` before deciding the next step.

Primary task file for the completed worker: `.cursor/tasks/task-001.md`. Read the full `## Result` section there. Do not rely on truncated chat summaries.
```

Domino should then:

- re-read the runtime files
- read `## Result` in the finished task file on disk
- decide whether to accept, revise, or dispatch the next worker

## Example 3: Verification Continuation

When all tasks are done, Domino should set:

```bash
python3 ~/.cursor/skills/domino/scripts/domino_runtime.py set-status --workspace "<workspace-root>" --status "verify_pending"
```

The `stop` hook should then emit:

```text
Continue the active Domino workflow and run final verification now. Read `.cursor/domino-plan.md`, `.cursor/domino-runtime.json`, and task files under `.cursor/tasks/` (especially each `## Result`) before acting.
```

## Example 4: Memory Save Continuation

After verification passes, Domino should set:

```bash
python3 ~/.cursor/skills/domino/scripts/domino_runtime.py set-status --workspace "<workspace-root>" --status "memory_save_pending"
```

The `stop` hook should then emit:

```text
Continue the active Domino workflow and persist memory now. Write `.cursor/project_state.md` and `.cursor/context_summary.md`, then mark the workflow complete.
```

## Example 5: Worker Failure Continuation

If the worker subagent exits without `completed`, `subagentStop` sets `workflow_status` to `running` and may emit:

```text
Continue the active Domino workflow in this workspace. The worker subagent did not complete successfully (status: error). Read `.cursor/domino-plan.md`, `.cursor/domino-runtime.json`, and `.cursor/tasks/task-001.md`. Dispatch the Debugger role to diagnose and propose a fix, or have the Planner create a repair task.
```

## Example 6: Stuck Worker Detection

If Domino suspects the workflow is stuck in `waiting_for_worker`:

```bash
python3 ~/.cursor/skills/domino/scripts/domino_runtime.py check-stuck --workspace "<workspace-root>" --minutes 30
```

Or merge into `read-state`:

```bash
python3 ~/.cursor/skills/domino/scripts/domino_runtime.py read-state --workspace "<workspace-root>" --stuck-after-minutes 30
```

## Example 7: Blocked Workflow

If a worker is blocked, Domino should not ask the user to run another command manually.

Instead, Domino should ask one question like:

```text
Domino needs one decision before proceeding.

Question: Which dataset split should this pipeline target first?
Options:
  A) validation only
  B) train + validation
Recommendation: A — smaller blast radius for the first pass
```
