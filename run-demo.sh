#!/usr/bin/env bash
set -euo pipefail
software_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# Run the merged main source; retain the existing upgraded demo database.
demo_database="$software_dir/.worktrees/feat-ai-integration-demo/backend/demo-ready-two-class-v1.db"
cd -- "$software_dir"
exec "$software_dir/backend/venv/bin/python" -m backend.scripts.run_demo \
  --env-file "$software_dir/backend/.env" \
  --database "$demo_database" "$@"
