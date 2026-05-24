import sys

from processors.payroll_review_cli_runner import cli_failure_message, run_cli


def main() -> None:
    try:
        raise SystemExit(run_cli())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(cli_failure_message(exc.code), file=sys.stderr)
            raise SystemExit(1) from exc

        raise
    except Exception as exc:
        print(cli_failure_message(str(exc)), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
