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

    if status != "completed":
        print(json.dumps({}))
        return 0

    if generation_id and generation_id == state.get("last_stop_generation_id"):
        print(json.dumps({}))
        return 0

    if state.get("workflow_status") == "waiting_for_worker":
        print(json.dumps({}))
        return 0

    followup = None
    workflow_status = state.get("workflow_status")
    if workflow_status == "verify_pending":
        followup = (
            "Continue the active Domino workflow and run final verification now. "
            "Read `.cursor/domino-plan.md`, `.cursor/domino-runtime.json`, and task files under `.cursor/tasks/` "
            "(especially each `## Result`) before acting."
        )
    elif workflow_status == "memory_save_pending":
        followup = (
            "Continue the active Domino workflow and persist memory now. "
            "Write `.cursor/project_state.md` and `.cursor/context_summary.md`, then mark the workflow complete."
        )

    if followup:
        followup += phase_suffix(state)

    if not followup:
        print(json.dumps({}))
        return 0

    state["last_stop_generation_id"] = generation_id
    save_state(workspace, state)
    print(json.dumps({"followup_message": followup}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
