---
name: domino
description: Runs end-to-end Domino orchestration workflows from a single entry point using Cursor subagents, hooks, and file-backed runtime state. Use when the user wants a multi-step task planned, implemented, reviewed, repaired, verified, and persisted automatically from one Domino invocation.
disable-model-invocation: true
---

# Domino

## Purpose

Use this skill as the single global entry point for Domino workflows.

This skill replaces the old slash-command chain:

- `/domino`
- `/orchestrator`
- `/orchestrator-parallel`
- `/agent-executor`
- `/agent-debugger`
- `/agent-reviewer`
- `/merge-review`
- `/verify`
- `/memory-load`
- `/memory-save`

Those are now internal workflow roles. Domino should not ask the user to run them manually.

## Runtime Files

Domino uses file-backed state in the active workspace:

- `.cursor/domino-plan.md`
- `.cursor/domino-runtime.json`
- `.cursor/tasks/task-*.md`
- `.cursor/parallel-plan.md`
- `.cursor/project_state.md`
- `.cursor/context_summary.md`

## Helper Scripts

Use these deterministic helpers:

- `python3 ~/.cursor/skills/domino/scripts/domino_runtime.py ensure --workspace "<workspace-root>"`
- `python3 ~/.cursor/skills/domino/scripts/domino_runtime.py start --workspace "<workspace-root>"`
- `python3 ~/.cursor/skills/domino/scripts/domino_runtime.py read-state --workspace "<workspace-root>"`
- `python3 ~/.cursor/skills/domino/scripts/domino_runtime.py mark-dispatch --workspace "<workspace-root>" --role "<role>" --task-id "<task-id>"`
- `python3 ~/.cursor/skills/domino/scripts/domino_runtime.py set-status --workspace "<workspace-root>" --status "<status>"`
- `python3 ~/.cursor/skills/domino/scripts/domino_runtime.py complete --workspace "<workspace-root>"`
- `python3 ~/.cursor/skills/domino/scripts/domino_runtime.py next-task --workspace "<workspace-root>"`
- `python3 ~/.cursor/skills/domino/scripts/domino_runtime.py normalize-result --workspace "<workspace-root>" --task-id "<task-id>"`

If the workspace root is unclear, resolve it first with `pwd`.

## Startup

At the start of every Domino run:

1. Resolve the workspace root.
2. Run `ensure`.
3. Read `.cursor/project_state.md` and `.cursor/context_summary.md` if they exist.
4. Read `.cursor/domino-runtime.json` and `.cursor/domino-plan.md` if they exist.
5. If there is no active Domino runtime state, run `start`.

## Ambiguity Gate

Default behavior is auto-start, not approval-seeking.

Only stop if one high-impact ambiguity would materially change:

- architecture
- file layout
- data shape
- destructive behavior
- acceptance criteria

When the decision is discrete and can be expressed as 2-4 options, use structured selection instead of plain text.

When the decision is open-ended, ask one plain-text question.

Do not ask more than one high-impact question at a time.

## Strategy

Choose one of these modes:

- `Sequential`
- `Parallel`
- `Repair`
- `Review-only`
- `Hybrid`

Persist the chosen strategy in `.cursor/domino-plan.md`.

## Data-Centric Workflow Gate

If the goal involves datasets, data filtering, generated data, model training, evaluation data, synthetic data, or end-to-end ML workflows, Domino must create and preserve a Data Validation Thread.

The Data Validation Thread is mandatory when data quality could materially affect the result. It must be written into `.cursor/domino-plan.md` and carried into every relevant task spec.

Include:

- Target data criteria: what makes data suitable for the user's actual goal, not just available. Example: for motion deblurring, source images for synthetic blur should be sharp, diverse, and visually suitable for plausible motion degradation. Prefer images with dynamic subjects or scenes, handheld-camera contexts, textured backgrounds, and indoor/outdoor diversity. Avoid images that are already blurry, low-quality, over-compressed, mostly blank, or visually irrelevant.
- Filtering strategy: how data will be selected, rejected, split, and counted.
- Audit evidence: required summaries or files with source datasets, counts before and after filtering, split sizes, rejected cases, representative samples, and limitations.
- Sample inspection: whether workers must manually or programmatically inspect samples before training or evaluation.
- End-to-end smoke check: for training workflows, whether to run a dry run or tiny training run to verify the processed data actually works.
- Goal alignment checkpoints: points where workers must check that the current artifact still matches the original user goal.
- Artifact hygiene: what intermediate outputs may be kept, where final artifacts and audit evidence belong, what temporary files, partial datasets, failed-run checkpoints, or debug outputs should be removed or summarized, and when cleanup checks are triggered.

Do not treat data preparation as a black box inside implementation. If a data task lacks enough criteria to decide whether the resulting dataset is suitable, use the Ambiguity Gate before execution.
Do not allow data or training workflows to accumulate unmanaged intermediate artifacts. By default, trigger artifact hygiene checks after each meaningful data processing stage, after dry runs or tiny training runs that create disposable outputs, before task completion, and during final verification. A trigger is a decision point, not a mandatory deletion step: if no new disposable artifacts exist, cleanup would disrupt downstream work, or cleanup is unsafe, require the worker to record `not needed`, `deferred`, or the safety reason instead of deleting blindly. If cleanup could delete user-provided data or expensive outputs, preserve them and report the cleanup decision.

## Worker Roles

Domino should use subagents instead of slash-command jumps.

Use these internal roles:

- `Planner` — produces standard task specs for sequential, repair, or review-only work
- `ParallelPlanner` — produces standard task specs for parallel waves
- `Executor` — implements one task spec
- `Debugger` — fixes one task spec
- `Reviewer` — reviews one task spec
- `Verifier` — performs final end-to-end verification
- `MemorySaver` — persists `project_state.md` and `context_summary.md`

Detailed role contracts live in [reference.md](reference.md).

## Dispatch Rules

### Sequential, Repair, Review-only

1. Dispatch the `Planner` role to write standard `.cursor/tasks/task-*.md` files.
2. Use `next-task` to select the next unblocked task.
3. Dispatch the assigned worker role.
4. Before dispatching any worker subagent, run:

```bash
python3 ~/.cursor/skills/domino/scripts/domino_runtime.py mark-dispatch --workspace "<workspace-root>" --role "<role>" --task-id "<task-id>"
```

5. Let the `subagentStop` hook auto-submit the next `/domino ...` follow-up.
6. After the queue is complete, set status to `verify_pending` and allow the `stop` hook to continue the flow.

### Parallel, Hybrid

1. Dispatch the `ParallelPlanner` role to write `.cursor/tasks/task-*.md` and `.cursor/parallel-plan.md`.
2. If isolation is required, prefer isolated worker subagents or best-of-n-style isolated runners for each wave task.
3. Before dispatching each worker subagent, run `mark-dispatch`.
4. Let the `subagentStop` hook auto-submit the next `/domino ...` follow-up.
5. If a wave needs merge-style reconciliation, have Domino do that work inside the main loop using `.cursor/parallel-plan.md` and task results.
6. When the final active segment is done, set status to `verify_pending`.

## Verify And Memory Save

When all planned tasks are done:

1. Set status to `verify_pending`
2. End the turn so the `stop` hook can auto-submit the verify continuation
3. Run the `Verifier` role
4. If verification passes, set status to `memory_save_pending`
5. End the turn so the `stop` hook can auto-submit the memory-save continuation
6. Run the `MemorySaver` role
7. Call `complete`

## Hook Contract

Domino relies on user-level hooks:

- `subagentStop` continues the workflow after worker completion
- `stop` continues the workflow for verify and memory-save phases

Do not ask the user to manually continue the chain unless execution is blocked.

## Required Runtime State Transitions

Use these statuses in `.cursor/domino-runtime.json`:

- `running`
- `waiting_for_worker`
- `verify_pending`
- `memory_save_pending`
- `blocked`
- `completed`

## Non-Negotiable Rules

- Do not tell the user to manually run an old slash command as the next step.
- Do not invent ad-hoc task files outside `.cursor/tasks/`.
- Carry `Domino assumptions` and `User decisions` into task specs.
- Carry the Data Validation Thread into task specs whenever data quality affects the outcome.
- Require worker results to include `Constraint check`.
- Require worker results for data-dependent tasks to include `Data validation`, with evidence from counts, filters, samples, and smoke checks when applicable.
- Require worker results for data or training tasks to include `Artifact hygiene`, with retained artifacts, cleaned artifacts, and any cleanup deliberately skipped.
- Re-read `.cursor/domino-plan.md` and `.cursor/domino-runtime.json` on every continuation turn.
- If blocked, stop and ask exactly one high-impact question.

## Additional Resources

- Detailed role contracts: [reference.md](reference.md)
- Example flows and follow-up messages: [examples.md](examples.md)
