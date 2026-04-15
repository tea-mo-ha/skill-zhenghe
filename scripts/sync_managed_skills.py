#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def managed_sources(root: Path) -> list[Path]:
    sources = [root / "skill-suite-orchestrator"]
    for folder in ("addy-skills", "extra-skills"):
        base = root / folder
        sources.extend(sorted(path for path in base.iterdir() if path.is_dir()))
    return sources


def target_dirs() -> dict[str, Path]:
    home = Path.home()
    return {
        "antigravity": home / ".gemini" / "antigravity" / "skills",
        "codex": home / ".agents" / "skills",
    }


def sync_target(source_dirs: list[Path], destination: Path, dry_run: bool) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    changes: list[str] = []

    for source in source_dirs:
        target = destination / source.name
        changes.append(f"{source.name} -> {target}")

        if dry_run:
            continue

        if target.exists() or target.is_symlink():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()

        shutil.copytree(source, target, symlinks=False)

    return changes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync managed skills from this repository into runtime skill directories.",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        choices=sorted(target_dirs().keys()),
        default=sorted(target_dirs().keys()),
        help="Runtime targets to refresh. Defaults to all supported targets.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned sync without copying files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    sources = managed_sources(root)
    targets = target_dirs()

    print(f"Repository root: {root}")
    print(f"Managed skill count: {len(sources)}")

    for name in args.targets:
        destination = targets[name]
        print(f"\n[{name}] {destination}")
        for change in sync_target(sources, destination, args.dry_run):
            print(f"  - {change}")

    if args.dry_run:
        print("\nDry run only. No files were copied.")
    else:
        print("\nSync complete.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
