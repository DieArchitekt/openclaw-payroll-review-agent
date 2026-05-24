import argparse
import json
from pathlib import Path

from processors.openclaw_runtime_v1 import (
    DEFAULT_POLICY_PATH,
    validate_review_outputs,
    validate_runtime_environment,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate OpenClaw runtime wiring.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    environment = subparsers.add_parser("check-env")
    environment.add_argument("--repo-root", type=Path, default=Path.cwd())
    environment.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)

    outputs = subparsers.add_parser("check-outputs")
    outputs.add_argument("output_dir", type=Path)
    outputs.add_argument("prefix")
    outputs.add_argument("--policy", type=Path, default=DEFAULT_POLICY_PATH)

    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.command == "check-env":
        result = validate_runtime_environment(args.repo_root, args.policy)
    else:
        result = validate_review_outputs(args.output_dir, args.prefix, args.policy)

    print(json.dumps(result.as_dict(), indent=2))
    raise SystemExit(0 if result.ok else 1)


if __name__ == "__main__":
    main()
