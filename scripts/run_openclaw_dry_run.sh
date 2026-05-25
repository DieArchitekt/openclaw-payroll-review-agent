#!/usr/bin/env bash
set -euo pipefail

output_folder="./outputs/reviews/dry_run"
print_json=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-folder)
      output_folder="$2"
      shift 2
      ;;
    --print-json)
      print_json="--print-json"
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$repo_root/scripts/run_openclaw_payroll_review.sh" \
  --incoming-root "$repo_root/incoming_payroll" \
  --output-folder "$output_folder" \
  --output-prefix "sample_openclaw" \
  --prepared-by "OpenClaw dry run" \
  $print_json
