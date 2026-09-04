"""CLI entry point for the developer-only Balance Lab.

This scaffold deliberately does not mutate production configuration.
Future commands should load a candidate preset, call production simulation
functions from `src`, and print or persist reproducible metrics.
"""

from __future__ import annotations

import argparse

from tools.balance_lab.experiments import list_experiments


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Baseball Player Career Simulator Balance Lab")
    parser.add_argument(
        "--list",
        action="store_true",
        help="List planned/available experiments.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.list:
        for name in list_experiments():
            print(name)
        return 0

    print("Balance Lab scaffold ready.")
    print("Use --list to inspect planned experiments.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
