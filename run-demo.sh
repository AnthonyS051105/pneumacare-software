#!/usr/bin/env bash
set -euo pipefail
software_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
demo_dir="$software_dir/.worktrees/feat-ai-integration-demo"
cd -- "$demo_dir"
exec "$software_dir/backend/venv/bin/python" -m backend.scripts.run_demo \
  --env-file "$software_dir/backend/.env" \
  --database "$demo_dir/backend/demo-ready-two-class.db" "$@"
