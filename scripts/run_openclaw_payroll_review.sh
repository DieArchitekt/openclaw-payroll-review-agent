#!/usr/bin/env bash
set -euo pipefail

incoming_root="./incoming_payroll"
current=""
previous=""
output_folder="./outputs/reviews"
output_prefix=""
prepared_by="OpenClaw"
variance_threshold="20.0"
wait_for_pair="false"
wait_timeout_seconds="60.0"
poll_interval_seconds="2.0"
stable_checks="2"
print_json="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --incoming-root)
      incoming_root="$2"
      shift 2
      ;;
    --current)
      current="$2"
      shift 2
      ;;
    --previous)
      previous="$2"
      shift 2
      ;;
    --output-folder)
      output_folder="$2"
      shift 2
      ;;
    --output-prefix)
      output_prefix="$2"
      shift 2
      ;;
    --prepared-by)
      prepared_by="$2"
      shift 2
      ;;
    --variance-threshold)
      variance_threshold="$2"
      shift 2
      ;;
    --wait-for-pair)
      wait_for_pair="true"
      shift
      ;;
    --wait-timeout-seconds)
      wait_timeout_seconds="$2"
      shift 2
      ;;
    --poll-interval-seconds)
      poll_interval_seconds="$2"
      shift 2
      ;;
    --stable-checks)
      stable_checks="$2"
      shift 2
      ;;
    --print-json)
      print_json="true"
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 2
      ;;
  esac
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
mkdir -p "$output_folder"

args=(-m processors.payroll_review_cli)

if [[ -n "$current" && -n "$previous" ]]; then
  args+=("$current" "$previous")
else
  args+=(--incoming-root "$incoming_root")

  if [[ "$wait_for_pair" == "true" ]]; then
    args+=(
      --wait-for-pair
      --wait-timeout "$wait_timeout_seconds"
      --poll-interval "$poll_interval_seconds"
      --stable-checks "$stable_checks"
    )
  fi
fi

args+=(
  --output-dir "$output_folder"
  --variance-threshold "$variance_threshold"
  --prepared-by "$prepared_by"
)

if [[ -n "$output_prefix" ]]; then
  args+=(--output-prefix "$output_prefix")
fi

if [[ "$print_json" == "true" ]]; then
  args+=(--print-json)
fi

python "${args[@]}"
