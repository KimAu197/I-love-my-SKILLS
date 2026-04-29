---
name: domino
description: Runs end-to-end Domino orchestration workflows from a single entry point using Cursor subagents, hooks, and file-backed runtime state. Use when the user wants a multi-step task planned, implemented, reviewed, repaired, verified, and persisted automatically from one Domino invocation.
disable-model-invocation: true
---

# Domino

## Purpose

Use this skill as the single global entry point for Domino workflows.

Domino coordinates planning, implementation, repair, review, verification, and memory persistence through internal roles, subagents, runtime files, hooks, and helper scripts.

## Runtime Files

Domino uses file-backed state in the active workspace:

- `.cursor/domino-plan.md`
- `.cursor/domino-runtime.json`
- `.cursor/tasks/task-*.md`
- `.cursor/parallel-plan.md`
- `.cursor/project_state.md`
- `.cursor/context_summary.md`
- `.cursor/project-skills-memory.md`
- `.cursor/cursor-skills-memory-candidates.md`

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
3. Read `.cursor/project_state.md`, `.cursor/context_summary.md`, and `.cursor/project-skills-memory.md` if they exist.
4. Read `.cursor/domino-runtime.json` and `.cursor/domino-plan.md` if they exist.
5. If there is no active Domino runtime state, run `start`.

If `.cursor/cursor-skills-memory-candidates.md` exists, read it as advisory context only. It contains global memory candidates, not necessarily approved global rules.

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

## Run Boundary Rules

Domino must keep smoke tests, dry runs, and real runs separate:

- All smoke tests and temporary test code belong under `test/`.
- Do not put smoke tests, `test_` helpers, `# test`, `# debug`, or temporary validation logic in business modules.
- Business modules may use `if __name__ == "__main__"` only for real CLI entry points, not ad hoc smoke tests.
- Dry runs, mock runs, and fake-structure validation must run through `test_run.py`.
- Files produced by `test_run.py` must use a `dry_` prefix or live under a clearly `dry_`-prefixed output directory.
- Real results must come from `main.py` and must not use `dry_` prefixes.
- If an output could be dry-run output but lacks a `dry_` marker, report it as suspicious instead of treating it as a real result.

## Resource Check Rule

Domino must require resource checks for all experiment and training work, regardless of entry point:

- Before starting any experiment, training job, evaluation run, benchmark, or real/dry research run, call the project's resource detection step.
- The pre-run resource check must record current GPU and CPU state, including available devices, memory pressure, utilization, and obvious competing processes when available.
- Before launch, compute and record recommended run parameters such as batch size, worker count, precision/device choice, concurrency, and whether the run should proceed, shrink, or wait.
- During the run, trigger one lightweight resource check at a safe midpoint or early steady-state point and record current utilization.
- This applies to `main.py`, `test_run.py`, training scripts, evaluation scripts, notebooks converted to scripts, and agent-created runners.
- Do not start or mark an experiment/training task complete unless resource check evidence is included in logs, task results, or the run summary.

## Incomplete Run Cleanup Rule

Domino must isolate artifacts from incomplete experiment and training runs:

- If an experiment, training job, evaluation run, benchmark, or research run stops early because of an error, resource problem, timeout, cancellation, or manual interruption, treat the run as incomplete.
- Move artifacts produced by that run, including checkpoints, logs, output files, manifests, temporary predictions, and partial metrics, to `incomplete/{timestamp}_{run_name}/` at the project root.
- Do not delete incomplete-run artifacts directly.
- Do not leave incomplete-run artifacts in their original output, checkpoint, log, results, runs, or artifacts directories.
- After moving artifacts, print one terminal line summarizing what was moved and why.
- If an artifact cannot be moved safely, preserve it and print one terminal line explaining the path and reason.

## Worker Roles

Domino should use subagents and internal role prompts.

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

5. Let the `subagentStop` hook auto-submit the next Domino continuation.
6. After the queue is complete, set status to `verify_pending` and allow the `stop` hook to continue the flow.

### Parallel, Hybrid

1. Dispatch the `ParallelPlanner` role to write `.cursor/tasks/task-*.md` and `.cursor/parallel-plan.md`.
2. If isolation is required, prefer isolated worker subagents or best-of-n-style isolated runners for each wave task.
3. Before dispatching each worker subagent, run `mark-dispatch`.
4. Let the `subagentStop` hook auto-submit the next Domino continuation.
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

## Skill Memory Evolution

Domino should preserve reusable lessons without polluting long-term memory.

Workers may produce `Memory candidates` when they find a repeated mistake, project-specific convention, or systematic process gap. Examples:

- Data tasks repeatedly skip audit evidence, sample inspection, or goal-specific filtering.
- End-to-end workflows repeatedly report success without reading result files or logs.
- Training runs repeatedly leave unmanaged intermediate artifacts.
- A project has a stable convention that future agents must follow.

MemorySaver owns promotion decisions:

- Write to `.cursor/project-skills-memory.md` when the lesson is project-specific or repeated in this workspace.
- Write global candidates to `.cursor/cursor-skills-memory-candidates.md` when the lesson appears broadly useful across projects.
- Do not directly promote global memory unless the user explicitly approves that policy.
- Ignore one-off, low-confidence, or vague lessons.

Each memory item must be short and executable:

```markdown
- Trigger: [when this applies]
  Rule: [what future agents should do]
  Evidence: [task ids, verifier finding, or repeated failure]
  Scope: [project-only | global-candidate]
```

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

- Do not ask the user to manually run internal workflow roles as separate steps.
- Do not invent ad-hoc task files outside `.cursor/tasks/`.
- Carry `Domino assumptions` and `User decisions` into task specs.
- Carry the Data Validation Thread into task specs whenever data quality affects the outcome.
- Carry run boundary requirements into task specs whenever work involves smoke tests, dry runs, mock runs, output files, or real execution.
- Carry resource check requirements into task specs whenever work involves experiments, training, evaluation, benchmarks, or research runs.
- Carry incomplete-run cleanup requirements into task specs whenever work can produce checkpoints, logs, outputs, predictions, metrics, or other run artifacts.
- Require worker results to include `Constraint check`.
- Require worker results for data-dependent tasks to include `Data validation`, with evidence from counts, filters, samples, and smoke checks when applicable.
- Require worker results for data or training tasks to include `Artifact hygiene`, with retained artifacts, cleaned artifacts, and any cleanup deliberately skipped.
- Require Debugger, Reviewer, Verifier, and MemorySaver outputs to consider `Memory candidates` when repeated mistakes or reusable conventions are discovered.
- Re-read `.cursor/domino-plan.md` and `.cursor/domino-runtime.json` on every continuation turn.
- If blocked, stop and ask exactly one high-impact question.

## Additional Resources

- Detailed role contracts: [reference.md](reference.md)
- Example flows and follow-up messages: [examples.md](examples.md)
