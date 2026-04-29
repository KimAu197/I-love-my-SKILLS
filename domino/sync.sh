#!/bin/bash

set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
CURSOR_HOME="$HOME/.cursor"
TARGET_SKILL_DIR="$CURSOR_HOME/skills/domino"
TARGET_SCRIPT_DIR="$TARGET_SKILL_DIR/scripts"
TARGET_HOOK_DIR="$CURSOR_HOME/hooks"
SOURCE_HOOKS_JSON="$SRC/hooks/hooks.json"
TARGET_HOOKS_JSON="$CURSOR_HOME/hooks.json"

echo "Syncing Domino runtime from: $SRC"

mkdir -p "$TARGET_SCRIPT_DIR"
mkdir -p "$TARGET_HOOK_DIR"

cp "$SRC/skills/domino/SKILL.md" "$TARGET_SKILL_DIR/SKILL.md"
cp "$SRC/skills/domino/reference.md" "$TARGET_SKILL_DIR/reference.md"
cp "$SRC/skills/domino/examples.md" "$TARGET_SKILL_DIR/examples.md"
cp "$SRC/skills/domino/scripts/domino_runtime.py" "$TARGET_SCRIPT_DIR/domino_runtime.py"

cp "$SRC/hooks/domino-subagent-stop.py" "$TARGET_HOOK_DIR/domino-subagent-stop.py"
cp "$SRC/hooks/domino-stop.py" "$TARGET_HOOK_DIR/domino-stop.py"

python3 - "$SOURCE_HOOKS_JSON" "$TARGET_HOOKS_JSON" <<'PY'
import json
import sys
from pathlib import Path

source_path = Path(sys.argv[1])
target_path = Path(sys.argv[2])

source_data = json.loads(source_path.read_text(encoding="utf-8"))

if target_path.exists():
    existing_data = json.loads(target_path.read_text(encoding="utf-8"))
else:
    existing_data = {}

if not isinstance(existing_data, dict):
    existing_data = {}

if not isinstance(source_data, dict):
    raise SystemExit("Source hooks.json must contain a JSON object.")

existing_hooks = existing_data.get("hooks")
if not isinstance(existing_hooks, dict):
    existing_hooks = {}

source_hooks = source_data.get("hooks")
if not isinstance(source_hooks, dict):
    raise SystemExit("Source hooks.json must contain a hooks object.")

merged = dict(existing_data)
merged["version"] = source_data.get("version", merged.get("version", 1))
merged["hooks"] = dict(existing_hooks)

domino_commands = {
    "subagentStop": "python3 ./hooks/domino-subagent-stop.py",
    "stop": "python3 ./hooks/domino-stop.py",
}

for event_name, domino_command in domino_commands.items():
    existing_entries = merged["hooks"].get(event_name, [])
    if not isinstance(existing_entries, list):
        existing_entries = []

    filtered_entries = [
        entry
        for entry in existing_entries
        if not (
            isinstance(entry, dict)
            and entry.get("command") == domino_command
        )
    ]

    source_entries = source_hooks.get(event_name, [])
    if not isinstance(source_entries, list):
        raise SystemExit(f"Source hook '{event_name}' must be a list.")

    filtered_entries.extend(source_entries)
    merged["hooks"][event_name] = filtered_entries

target_path.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
PY

chmod +x "$TARGET_SCRIPT_DIR/domino_runtime.py"
chmod +x "$TARGET_HOOK_DIR/domino-subagent-stop.py"
chmod +x "$TARGET_HOOK_DIR/domino-stop.py"

echo "Domino sync complete."
echo "Updated:"
echo "  - $TARGET_SKILL_DIR"
echo "  - $TARGET_HOOK_DIR"
echo "  - $CURSOR_HOME/hooks.json"
