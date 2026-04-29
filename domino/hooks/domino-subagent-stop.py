#!/usr/bin/env python3

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".cursor" / "skills" / "domino" / "scripts"))

from domino_runtime import load_state, save_state, workspace_path  # noqa: E402


def phase_suffix(state: dict) -> str:
    label = state.get("current_phase")
    if not label:
        return ""
    return f"\n\nCurrent phase (runtime `current_phase`): {label}"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({}))
        return 0

    workspace_roots = payload.get("workspace_roots") or []
    if not workspace_roots:
        print(json.dumps({}))
        return 0

    workspace = workspace_path(workspace_roots[0])
    state = load_state(workspace)
    generation_id = payload.get("generation_id")
    status = payload.get("status")

    if not state.get("active"):
        print(json.dumps({}))
        return 0

    if state.get("workflow_status") != "waiting_for_worker":
        print(json.dumps({}))
        return 0

    # Dedupe hook replays for the same subagent stop event (success or failure).
    if generation_id and generation_id == state.get("last_subagent_generation_id"):
        print(json.dumps({}))
        return 0

    if status != "completed":
        task_id = state.get("last_task_id") or "unknown"
        state["last_worker_status"] = status
        state["workflow_status"] = "running"
        state["last_subagent_generation_id"] = generation_id
        state["last_worker_summary"] = (
            f"Worker ended with status {status}. See `.cursor/tasks/{task_id}.md` for any written result."
        )
        save_state(workspace, state)
        followup = (
            "Continue the active Domino workflow in this workspace. "
            f"The worker subagent did not complete successfully (status: {status}). "
            "Read `.cursor/domino-plan.md`, `.cursor/domino-runtime.json`, and "
            f"`.cursor/tasks/{task_id}.md`. "
            "Dispatch the Debugger role to diagnose and propose a fix, or have the Planner create a repair task."
        )
        followup += phase_suffix(state)
        print(json.dumps({"followup_message": followup}))
        return 0

    summary = (payload.get("summary") or "").strip()
    task = (payload.get("task") or "").strip()
    modified_files = payload.get("modified_files") or []

    state["workflow_status"] = "running"
    state["last_worker_status"] = status
    task_id = state.get("last_task_id")
    if task_id:
        state["last_worker_summary"] = (
            "Full worker output: read `.cursor/tasks/"
            + task_id
            + ".md` section `## Result` (hooks do not embed large summaries)."
        )
    else:
        state["last_worker_summary"] = summary[:4000] if summary else None
    state["last_modified_files"] = modified_files
    state["last_subagent_generation_id"] = generation_id
    save_state(workspace, state)

    followup = (
        "Continue the active Domino workflow in this workspace. "
        "A worker subagent just completed successfully. "
        "Read `.cursor/domino-plan.md`, `.cursor/domino-runtime.json`, and `.cursor/tasks/` before deciding the next step."
    )
    if task_id:
        followup += (
            f"\n\nPrimary task file for the completed worker: `.cursor/tasks/{task_id}.md`. "
            "Read the full `## Result` section there. Do not rely on truncated chat summaries."
        )
    if task:
        followup += f"\n\nCompleted worker task label: {task}"
    followup += phase_suffix(state)

    print(json.dumps({"followup_message": followup}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
