"""
MediTwin AI — Submission Preparation Script
Automates copying project files into a forked IBM_Db2_TechX_Project_Submission repository.

Usage:
    python scripts/prepare_submission.py --fork-dir "C:/path/to/IBM_Db2_TechX_Project_Submission"
"""

import os
import sys
import shutil
import argparse
from pathlib import Path

# Files and directories to package into submissions/meditwin-ai/
PACKAGE_ITEMS = [
    "README.md",
    "architecture.md",
    "submission.json",
    ".env.example",
    "requirements.txt",
    "pytest.ini",
    "app.py",
    "config",
    "db",
    "ingestion",
    "graph",
    "services",
    "sample_data",
    "tests",
    "docs",
]


def prepare_submission(target_fork_dir: str):
    fork_path = Path(target_fork_dir).resolve()
    if not fork_path.exists():
        print(f"Error: Target directory does not exist: {fork_path}")
        sys.exit(1)

    submissions_dir = fork_path / "submissions"
    if not submissions_dir.exists():
        print(f"Warning: 'submissions' directory not found in {fork_path}. Creating it.")
        submissions_dir.mkdir(parents=True, exist_ok=True)

    dest_dir = submissions_dir / "meditwin-ai"
    if dest_dir.exists():
        print(f"Destination {dest_dir} already exists. Cleaning up before copy...")
        shutil.rmtree(dest_dir)

    dest_dir.mkdir(parents=True, exist_ok=True)
    source_root = Path(__file__).parent.parent.resolve()

    print(f"Copying MediTwin AI project files from {source_root} to {dest_dir}...")

    copied_count = 0
    for item in PACKAGE_ITEMS:
        src = source_root / item
        dst = dest_dir / item
        if not src.exists():
            print(f"  Skipping {item} (not found)")
            continue

        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))
            print(f"  Copied directory: {item}/")
        else:
            shutil.copy2(src, dst)
            print(f"  Copied file: {item}")
        copied_count += 1

    print("\n" + "=" * 60)
    print("SUCCESS: MediTwin AI packaged for official submission!")
    print(f"Target path: {dest_dir}")
    print("=" * 60)
    print("\nNext steps to submit:")
    print("1. In your forked repository:")
    print("   git checkout -b submission/meditwin-ai")
    print("   git add submissions/meditwin-ai")
    print("   git commit -m 'feat: submit MediTwin AI for IBM Db2Hack 2026'")
    print("   git push origin submission/meditwin-ai")
    print("2. Open a Pull Request against KunalGolaIBM/IBM_Db2_TechX_Project_Submission")
    print("3. Submit your PR link via the official Google Form before 5:00 PM IST.")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare MediTwin AI submission folder")
    parser.add_argument("--fork-dir", required=True, help="Path to your clone of IBM_Db2_TechX_Project_Submission")
    args = parser.parse_args()
    prepare_submission(args.fork_dir)

