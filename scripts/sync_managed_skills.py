#!/usr/bin/env python3
"""Versioned managed-skill publisher for runtime skill directories.

This script does three things that the previous copy-based sync did not:

1. Builds a full release artifact before touching any live runtime skill.
2. Promotes each managed skill through a resumable per-skill transaction.
3. Keeps immutable release snapshots plus explicit rollback support.

Constraint note:
  The host runtimes expect flat skill directories such as
  `~/.agents/skills/<skill-name>` and `~/.gemini/antigravity/skills/<skill-name>`.
  Under that flat-directory constraint, we cannot atomically switch the *entire*
  managed-skill set in a single filesystem operation without introducing a
  higher-level indirection layer. What we can do safely is:

  - stage the full release before any cutover
  - publish each skill via atomic rename with crash recovery
  - retain prior releases for rollback
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTROL_DIR_NAME = ".skill-zhenghe"
RELEASE_MARKER = ".skill-zhenghe-release.json"
IGNORE_NAMES = {
    ".DS_Store",
    "__pycache__",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def managed_sources(root: Path) -> list[Path]:
    sources = [root / "skill-suite-orchestrator"]
    for folder in ("addy-skills", "extra-skills"):
        base = root / folder
        sources.extend(
            sorted(
                path
                for path in base.iterdir()
                if path.is_dir() and (path / "SKILL.md").is_file()
            )
        )
    return sources


def target_dirs() -> dict[str, Path]:
    home = Path.home()
    return {
        "antigravity": home / ".gemini" / "antigravity" / "skills",
        "codex": home / ".agents" / "skills",
    }


def control_dir(destination: Path) -> Path:
    return destination / CONTROL_DIR_NAME


def releases_dir(destination: Path) -> Path:
    return control_dir(destination) / "releases"


def transactions_dir(destination: Path) -> Path:
    return control_dir(destination) / "transactions"


def current_manifest_path(destination: Path) -> Path:
    return control_dir(destination) / "current.json"


def _remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part in IGNORE_NAMES for part in path.parts):
            continue
        if path.name == RELEASE_MARKER:
            continue
        files.append(path)
    return files


def _hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in _iter_files(root):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _release_marker(skill_name: str, release_id: str, source_hash: str, source_path: Path) -> dict[str, str]:
    return {
        "skill_name": skill_name,
        "release_id": release_id,
        "source_hash": source_hash,
        "source_path": str(source_path),
        "generated_at": utc_now(),
    }


def _read_live_release_id(skill_dir: Path) -> str | None:
    marker = skill_dir / RELEASE_MARKER
    if not marker.is_file():
        return None
    try:
        payload = _read_json(marker)
    except json.JSONDecodeError:
        return None
    value = payload.get("release_id")
    return str(value) if value else None


def _copy_skill_tree(source: Path, destination: Path) -> None:
    _remove_path(destination)
    shutil.copytree(
        source,
        destination,
        symlinks=False,
        ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"),
    )


def _build_release_id(source_dirs: list[Path]) -> tuple[str, dict[str, str]]:
    skill_hashes = {source.name: _hash_tree(source) for source in source_dirs}
    digest = hashlib.sha256()
    for name in sorted(skill_hashes):
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(skill_hashes[name].encode("utf-8"))
        digest.update(b"\0")
    release_hash = digest.hexdigest()
    release_id = f"{utc_now()}-{release_hash[:12]}"
    return release_id, skill_hashes


def _prepare_release(source_dirs: list[Path], destination: Path) -> dict[str, Any]:
    release_id, skill_hashes = _build_release_id(source_dirs)
    releases_root = releases_dir(destination)
    release_root = releases_root / release_id
    temp_root = releases_root / f"{release_id}.tmp"
    skills_root = release_root / "skills"

    _remove_path(temp_root)
    temp_skills_root = temp_root / "skills"
    temp_skills_root.mkdir(parents=True, exist_ok=True)

    manifest_skills: list[dict[str, str]] = []
    for source in source_dirs:
        skill_name = source.name
        staged_skill = temp_skills_root / skill_name
        _copy_skill_tree(source, staged_skill)
        marker = _release_marker(
            skill_name=skill_name,
            release_id=release_id,
            source_hash=skill_hashes[skill_name],
            source_path=source,
        )
        _write_json(staged_skill / RELEASE_MARKER, marker)
        manifest_skills.append(
            {
                "skill_name": skill_name,
                "source_hash": skill_hashes[skill_name],
                "source_path": str(source),
            }
        )

    manifest = {
        "release_id": release_id,
        "created_at": utc_now(),
        "repo_root": str(repo_root()),
        "destination": str(destination),
        "skills": manifest_skills,
    }
    _write_json(temp_root / "manifest.json", manifest)
    releases_root.mkdir(parents=True, exist_ok=True)
    temp_root.rename(release_root)
    manifest["release_root"] = str(release_root)
    manifest["skills_root"] = str(skills_root)
    return manifest


def _planned_release(source_dirs: list[Path], destination: Path) -> dict[str, Any]:
    release_id, skill_hashes = _build_release_id(source_dirs)
    release_root = releases_dir(destination) / release_id
    manifest_skills = [
        {
            "skill_name": source.name,
            "source_hash": skill_hashes[source.name],
            "source_path": str(source),
        }
        for source in source_dirs
    ]
    return {
        "release_id": release_id,
        "repo_root": str(repo_root()),
        "destination": str(destination),
        "skills": manifest_skills,
        "release_root": str(release_root),
        "skills_root": str(release_root / "skills"),
    }


def _recover_transactions(destination: Path, changes: list[str]) -> None:
    tx_root = transactions_dir(destination)
    if not tx_root.is_dir():
        return

    for tx_file in sorted(tx_root.glob("*.json")):
        tx = _read_json(tx_file)
        skill_name = str(tx["skill_name"])
        target = Path(str(tx["target"]))
        staging = Path(str(tx["staging"]))
        backup = Path(str(tx["backup"]))
        desired_release = str(tx["desired_release_id"])

        if target.exists() and _read_live_release_id(target) == desired_release:
            _remove_path(staging)
            tx_file.unlink()
            changes.append(f"{skill_name}: recovered already-promoted target")
            continue

        if not target.exists() and staging.exists():
            staging.rename(target)
            tx_file.unlink()
            changes.append(f"{skill_name}: resumed staged promotion")
            continue

        if not target.exists() and backup.exists():
            backup.rename(target)
            tx_file.unlink()
            changes.append(f"{skill_name}: restored rollback slot after interrupted promotion")
            continue


def _promote_skill(
    release_root: Path,
    skill_name: str,
    destination: Path,
    desired_release_id: str,
) -> str:
    staged_source = release_root / "skills" / skill_name
    target = destination / skill_name
    staging = destination / f"{skill_name}.staging"
    previous_release = _read_live_release_id(target) or "legacy-unversioned"
    backup = control_dir(destination) / "backups" / previous_release / skill_name
    tx_file = transactions_dir(destination) / f"{skill_name}.json"

    live_release = _read_live_release_id(target)
    if live_release == desired_release_id:
        _remove_path(staging)
        return f"{skill_name}: already on {desired_release_id}"

    _copy_skill_tree(staged_source, staging)
    _write_json(
        tx_file,
        {
            "skill_name": skill_name,
            "target": str(target),
            "staging": str(staging),
            "backup": str(backup),
            "desired_release_id": desired_release_id,
        },
    )

    backup.parent.mkdir(parents=True, exist_ok=True)
    _remove_path(backup)
    if target.exists() or target.is_symlink():
        target.rename(backup)

    try:
        staging.rename(target)
    except OSError:
        if backup.exists() and not target.exists():
            backup.rename(target)
        raise
    finally:
        _remove_path(staging)

    tx_file.unlink(missing_ok=True)
    return f"{skill_name}: promoted to {desired_release_id}"


def _publish_release(manifest: dict[str, Any], destination: Path) -> list[str]:
    changes: list[str] = []
    _recover_transactions(destination, changes)

    release_id = str(manifest["release_id"])
    release_root = Path(str(manifest["release_root"]))
    for skill in manifest["skills"]:
        skill_name = str(skill["skill_name"])
        changes.append(_promote_skill(release_root, skill_name, destination, release_id))

    _write_json(
        current_manifest_path(destination),
        {
            "release_id": release_id,
            "updated_at": utc_now(),
            "manifest_path": str(release_root / "manifest.json"),
            "skills_root": str(release_root / "skills"),
        },
    )
    return changes


def _load_release_manifest(destination: Path, release_id: str) -> dict[str, Any]:
    release_root = releases_dir(destination) / release_id
    manifest_path = release_root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Unknown release_id for {destination}: {release_id}")
    manifest = _read_json(manifest_path)
    manifest["release_root"] = str(release_root)
    manifest["skills_root"] = str(release_root / "skills")
    return manifest


def sync_target(
    source_dirs: list[Path],
    destination: Path,
    dry_run: bool,
    rollback_release: str | None,
) -> list[str]:
    destination.mkdir(parents=True, exist_ok=True)
    changes: list[str] = []

    if rollback_release:
        manifest = _load_release_manifest(destination, rollback_release)
        if dry_run:
            return [f"rollback {skill['skill_name']} -> {rollback_release}" for skill in manifest["skills"]]
        return _publish_release(manifest, destination)

    manifest = _planned_release(source_dirs, destination) if dry_run else _prepare_release(source_dirs, destination)
    release_id = str(manifest["release_id"])
    if dry_run:
        return [f"build release {release_id}"] + [
            f"promote {skill['skill_name']} -> {destination / skill['skill_name']}"
            for skill in manifest["skills"]
        ]
    return _publish_release(manifest, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish managed skills from this repository into runtime skill directories.",
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
    parser.add_argument(
        "--rollback-release",
        help="Rollback to a previously published release id for the selected targets.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    sources = managed_sources(root)
    targets = target_dirs()

    print(f"Repository root: {root}")
    print(f"Managed skill count: {len(sources)}")

    if args.rollback_release:
        print(f"Rollback mode: {args.rollback_release}")

    for name in args.targets:
        destination = targets[name]
        print(f"\n[{name}] {destination}")
        for change in sync_target(
            source_dirs=sources,
            destination=destination,
            dry_run=args.dry_run,
            rollback_release=args.rollback_release,
        ):
            print(f"  - {change}")

    if args.dry_run:
        print("\nDry run only. No files were copied.")
    else:
        print("\nPublish complete.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
