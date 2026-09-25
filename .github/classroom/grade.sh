#!/usr/bin/env bash
set -euo pipefail

run_python() {
  local candidate

  for candidate in .venv/Scripts/python.exe .venv/bin/python python py python3; do
    if { [ -x "$candidate" ] || command -v "$candidate" >/dev/null 2>&1; } &&
      "$candidate" -c "import build, yaml" >/dev/null 2>&1; then
      "$candidate" "$@"
      return
    fi
  done

  echo "Kein passender Python-Interpreter gefunden."
  echo "Installiere zuerst die Test-Abhängigkeiten:"
  echo "  python -m pip install build pyyaml"
  echo "oder unter Windows:"
  echo "  py -m pip install build pyyaml"
  exit 127
}

run_python -m build
run_python .github/classroom/check_workflow.py
