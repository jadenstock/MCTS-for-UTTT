#!/usr/bin/env python
import argparse
import json
from pathlib import Path


def should_delete(path: Path, all_games: bool) -> bool:
    if all_games:
        return True
    try:
        data = json.loads(path.read_text())
    except Exception:
        return False
    winner = (data.get("current_state") or {}).get("winner", "")
    return winner in ("", None)


def cleanup(directory: Path, all_games: bool) -> int:
    deleted = 0
    if not directory.exists():
        return 0
    for path in directory.glob("*.json"):
        if should_delete(path, all_games=all_games):
            path.unlink(missing_ok=True)
            deleted += 1
    return deleted


def main():
    parser = argparse.ArgumentParser(description="Delete bot game JSON files.")
    parser.add_argument("--all", action="store_true", help="Delete all bot game files (not just in-progress).")
    parser.add_argument(
        "--include-benchmark-dir",
        action="store_true",
        help="Also clean data/benchmark_games files.",
    )
    args = parser.parse_args()

    root = Path("data")
    deleted_bot = cleanup(root / "bot_games", all_games=args.all)
    deleted_bench = cleanup(root / "benchmark_games", all_games=args.all) if args.include_benchmark_dir else 0
    print(f"deleted_bot_games={deleted_bot} deleted_benchmark_games={deleted_bench}")


if __name__ == "__main__":
    main()
