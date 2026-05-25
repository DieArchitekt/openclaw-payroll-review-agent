#!/usr/bin/env bash
set -euo pipefail

output_root="./outputs/reviews"
prepared_by="OpenClaw verification"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-root)
      output_root="$2"
      shift 2
      ;;
    --prepared-by)
      prepared_by="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

timestamp="$(date +%Y%m%d_%H%M%S)"
prefix="openclaw_verify_$timestamp"
output_folder="$output_root/$prefix"

bash ./scripts/run_openclaw_payroll_review.sh \
  --incoming-root ./incoming_payroll \
  --output-folder "$output_folder" \
  --output-prefix "$prefix" \
  --prepared-by "$prepared_by"

python -m processors.openclaw_runtime_v1 check-env
python -m processors.openclaw_runtime_v1 check-outputs "$output_folder" "$prefix"

echo ""
echo "OpenClaw workflow verification passed."
echo "Output folder: $output_folder"
echo "Output prefix: $prefix"
