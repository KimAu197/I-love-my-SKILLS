# Domino Reference

## Internal Roles

Domino uses these internal workflow roles:

| Role | Purpose |
|------|---------|
| `Planner` | Produces standard task specs for sequential, repair, or review-only work |
| `ParallelPlanner` | Produces standard task specs and a wave plan for parallel work |
| `Executor` | Implements one task spec |
| `Debugger` | Diagnoses and fixes one task spec |
| `Reviewer` | Reviews completed work against the task spec |
| `Verifier` | Performs final end-to-end verification |
| `MemorySaver` | Persists project state, context summary, and skill memory candidates |

## Standard Task Schema

Every standard task file should keep this shape:

```markdown
# Task {NNN}: {short title}
_Created by: Domino Planner_
_Assigned to: {Executor | Debugger | Reviewer}_
_Status: pending_

## Objective
One sentence: what should be true when this task is done?

## Context
- Relevant files: [exact paths]
- Current state: [what exists now]
- Dependencies: [task IDs, or "none"]
- Domino assumptions: [list active assumptions, or "none"]
- User decisions: [list binding answers, or "none"]
- Data Validation Thread: [target criteria, audit evidence, sample checks, smoke test, or "not applicable"]
- Artifact hygiene: [allowed retained artifacts, cleanup expectations, final artifact locations, or "not applicable"]
- Artifact hygiene triggers: [after meaningful data stage, after smoke/tiny train if disposable outputs are created, before task completion, final verify, or task-specific triggers; allow not-needed/deferred decisions]
- Run boundaries: [test/ for smoke tests, test_run.py for dry/mock runs, main.py for real runs, dry_ prefixes for dry outputs, or "not applicable"]
- Resource checks: [pre-run GPU/CPU check, recommended parameters, mid-run lightweight check, evidence location, or "not applicable"]
- Incomplete run cleanup: [move failed/interrupted run artifacts to incomplete/{timestamp}_{run_name}/, terminal summary line, or "not applicable"]

## Instructions
Precise, step-by-step instructions.

## Acceptance Criteria
- [ ] [specific, checkable condition]
- [ ] [for data-dependent tasks: data criteria, audit evidence, sample checks, and smoke test expectations are satisfied]
- [ ] [for data or training tasks: unnecessary intermediate artifacts are cleaned or organized, with retained artifacts documented]
- [ ] [for experiment or training tasks: pre-run and mid-run resource checks are recorded with recommended parameters]
- [ ] [for incomplete runs: produced checkpoints, logs, outputs, predictions, and metrics are moved to incomplete/{timestamp}_{run_name}/ and summarized in one terminal line]

## Output
- Modified files: [list]
- Result summary: write under `## Result`
```

## Worker Contracts

### Planner

Use for sequential, repair, review-only segments, and for **serial phases** inside **Hybrid** workflows.

Required output:

- Write standard task specs to `.cursor/tasks/`
- Keep assumptions and user decisions explicit
- For data-dependent work, define concrete data selection criteria, audit artifacts, sample checks, and end-to-end smoke checks before implementation begins
- For data or training work, define artifact hygiene expectations so intermediate files do not accumulate silently
- Define artifact hygiene triggers explicitly; default to after each meaningful data processing stage, after dry runs or tiny training runs that create disposable outputs, before task completion, and final verification. Triggers are decision points, not mandatory deletion steps.
- For smoke tests, dry runs, mock runs, or real output generation, define run boundaries: smoke tests under `test/`, dry/mock through `test_run.py`, real runs through `main.py`, and dry outputs marked with `dry_`.
- For experiments, training, evaluation, benchmarks, or research runs, require resource checks before launch and once during execution, with recommended parameters recorded before running.
- For any run that can produce checkpoints, logs, outputs, predictions, or metrics, require incomplete-run cleanup instructions: if the run stops early, move run artifacts to `incomplete/{timestamp}_{run_name}/`, do not delete them, do not leave them in place, and print one terminal summary line.
- Do not ask the user to manually trigger a worker if Domino can dispatch it next
- When `.cursor/domino-plan.md` uses **`## Chosen Strategy` `Hybrid`**, ensure **`## Phases`** exists and keep each Planner batch aligned with the current serial phase until its exit conditions are met.

### ParallelPlanner

Use for parallel or hybrid wave planning.

Required output:

- Write standard task specs to `.cursor/tasks/`
- Write `.cursor/parallel-plan.md`
- Only parallelize work with explicit interface clarity
- Carry assumptions and user decisions into both task specs and wave plan
- Do not parallelize data production and data validation unless artifacts and handoff points are explicit
- Do not parallelize cleanup-sensitive tasks unless artifact ownership and final handoff paths are explicit

### Executor

Use this contract:

1. Read the task file first.
2. Read `Domino assumptions` and `User decisions`.
3. Treat them as binding execution constraints.
4. Stay in scope.
5. For data-dependent tasks, inspect the data artifact itself: counts, filters, splits, representative samples, and dry-run or tiny-train logs when requested.
6. For data or training tasks, trigger artifact hygiene checks after meaningful data stages, after smoke or tiny training runs that create disposable outputs, and before completion. Clean or organize unnecessary intermediate artifacts without deleting user-provided data or expensive outputs unless explicitly safe; record `not needed` or `deferred` when cleanup is unnecessary or unsafe.
7. Keep run boundaries intact: do not add temporary smoke tests to business modules, do not run dry/mock validation through `main.py`, and do not create unprefixed dry outputs.
8. For experiments or training tasks, run the resource check before launch, record recommended parameters, trigger one lightweight mid-run check, and include evidence in logs or task results.
9. If a run stops early, move its artifacts to `incomplete/{timestamp}_{run_name}/`, do not delete them, do not leave them in their original directories, and print one terminal line summarizing moved files and reason.
10. Write a result section including:
   - `Files changed`
   - `Acceptance criteria`
   - `Data validation` when applicable
   - `Artifact hygiene` when applicable
   - `Run boundaries` when applicable
   - `Resource checks` when applicable
   - `Incomplete run cleanup` when applicable
   - `Constraint check`

### Debugger

Use this contract:

1. Diagnose before fixing.
2. Read `Domino assumptions` and `User decisions`.
3. Do not apply a fix that violates those constraints.
4. For data-dependent failures, check whether unsuitable data criteria, filtering, splits, generated data, missing audit evidence, sample quality, or skipped smoke tests caused the issue.
5. For data or training fixes, trigger artifact hygiene after reproducing/fixing the run if disposable outputs were created and before completion. Check whether the repair left behind unnecessary temporary files, failed-run checkpoints, partial generated outputs, or duplicated logs; record `not needed` or `deferred` when cleanup is unnecessary or unsafe.
6. Check that the fix does not blur run boundaries between smoke tests, dry/mock runs, and real runs.
7. For experiment or training fixes, check whether missing or incorrect resource checks contributed to the failure.
8. For early-terminated runs, check whether incomplete-run artifacts were moved to `incomplete/{timestamp}_{run_name}/` and summarized in the terminal.
9. Write a result section including:
   - `Root cause`
   - `Fix applied`
   - `Verification`
   - `Data validation` when applicable
   - `Artifact hygiene` when applicable
   - `Run boundaries` when applicable
   - `Resource checks` when applicable
   - `Incomplete run cleanup` when applicable
   - `Memory candidates` when a repeated or reusable lesson was found
   - `Constraint check`

### Reviewer

Use this contract:

1. Read the task file and the completed result.
2. Read actual files, not just the reported summary.
3. Check acceptance criteria explicitly.
4. Check whether `Domino assumptions` and `User decisions` were satisfied.
5. For data-dependent tasks, review the data audit evidence, representative samples, split logic, and smoke-test logs against the target criteria.
6. For data or training tasks, review whether artifact hygiene decisions happened at the required triggers and whether intermediate artifacts were cleaned, organized, intentionally retained, marked not needed, or deferred.
7. Review run boundaries: smoke tests live under `test/`, dry/mock runs use `test_run.py`, real runs use `main.py`, and dry outputs are `dry_`-marked.
8. For experiment or training tasks, review pre-run resource state, recommended parameters, mid-run utilization, and evidence location.
9. For early-terminated runs, review whether run artifacts were moved to `incomplete/{timestamp}_{run_name}/`, not deleted or left in place, and summarized in one terminal line.
10. Write a result section including:
   - `Verdict`
   - `Criteria review`
   - `Data validation review` when applicable
   - `Artifact hygiene review` when applicable
   - `Run boundary review` when applicable
   - `Resource check review` when applicable
   - `Incomplete run cleanup review` when applicable
   - `Additional findings`
   - `Memory candidates` when a repeated or reusable lesson was found
   - `Constraint check`

### Verifier

Use this contract:

1. Re-read the actual changed files.
2. Compare them to the goal and plan.
3. Check for correctness, completeness, references, and consistency.
4. For data-dependent work, verify that data processing served the target goal, not just that files exist. Review audit artifacts, sample evidence, and dry-run or tiny-train outputs when present.
5. For data or training work, verify that artifact hygiene decisions happened at the required triggers, unnecessary intermediate artifacts are cleaned or organized, and retained, not-needed, or deferred artifacts are intentional.
6. Verify run boundaries for smoke tests, dry/mock runs, real runs, and output naming.
7. For experiment or training work, verify pre-run resource checks, recommended parameters, mid-run resource checks, and evidence in logs or summaries.
8. For early-terminated runs, verify artifacts were moved to `incomplete/{timestamp}_{run_name}/`, not deleted or left in place, and a terminal summary line was printed.
9. If there are issues, create repair follow-up work through the Planner role.
10. Identify `Memory candidates` for repeated mistakes, project conventions, or systematic process gaps.
11. If everything passes, report clearly that verification passed.

### MemorySaver

Use this contract:

1. Scan the actual workspace.
2. Write `.cursor/project_state.md`.
3. Write `.cursor/context_summary.md`.
4. Scan task results, verifier findings, and debugger/reviewer notes for `Memory candidates`.
5. Write project-specific or repeated workspace lessons to `.cursor/project-skills-memory.md`.
6. Write broader cross-project candidates to `.cursor/cursor-skills-memory-candidates.md` unless the user has explicitly approved direct global promotion.
7. Keep all memory files precise and self-sufficient.

## Runtime File Contract

Domino relies on `.cursor/domino-runtime.json` to coordinate hooks and follow-up turns.

Expected fields:

```json
{
  "version": 1,
  "active": true,
  "workflow_status": "running",
  "current_phase": null,
  "last_worker_role": null,
  "last_task_id": null,
  "last_worker_status": null,
  "last_worker_summary": null,
  "last_dispatch_at_ms": null,
  "last_subagent_generation_id": null,
  "last_stop_generation_id": null
}
```

`current_phase` is an optional short string mirrored from `## Phases` in the plan (same conceptual phase, not a separate source of truth). Update via `set-current-phase`; cleared on `complete`. Hooks append it to automatic continuation messages.

`last_dispatch_at_ms` is set when `mark-dispatch` runs (worker handoff). It supports `check-stuck` / `read-state --stuck-after-minutes` when the workflow stays in `waiting_for_worker` too long. Older workspaces may lack this field until the next dispatch.

`last_worker_summary` is a pointer string after success when `last_task_id` is set, not a copy of large results; authoritative output is under `## Result` in the task file.

## Hook Behavior

### subagentStop

Process once per stop event when generation id has not already been processed:

- the runtime state is active
- `workflow_status` is `waiting_for_worker`

If the subagent status is not `completed`, set `workflow_status` to `running`, record `last_worker_status`, and emit a follow-up aimed at Debugger or repair planning.

If the subagent status is `completed`, set `workflow_status` to `running` and emit a follow-up that points at `.cursor/tasks/<task-id>.md` and `## Result` (no large embedded summary). Continuation text includes `current_phase` when set.

### stop

Trigger a follow-up only when:

- the runtime state is active
- `workflow_status` is `verify_pending` or `memory_save_pending`
- the stop event status is `completed`
- the generation id has not already been processed

Continuation text includes `current_phase` when set.

## Parallel Note

Parallel execution is phase-two quality, not phase-one quality.

The first stable target is:

- sequential
- repair
- review-only
- final verify
- memory save

Only expand the parallel path once the sequential hook loop is reliable.
