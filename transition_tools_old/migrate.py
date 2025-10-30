#!/usr/bin/env python3
"""
Unified migration script for HIVE cluster transition.

This script consolidates all migration functionality:
  - Software path updates (ColabFold, LigandMPNN, RFdiffusion, Rosetta)
  - SLURM configuration updates (partitions, accounts, requeue flags)
  - Time limit adjustments for partition constraints
  - General /share/siegellab/ → /quobyte/jbsiegelgrp/ migration

Replaces: colab_fix.py, ligandmpnn_fix.py, rfdiffusion_fix.py, rosetta_fix.py

Usage:
    python migrate.py <file_or_directory>              # Auto-detect and fix
    python migrate.py <file_or_directory> --high       # Use high partition for Rosetta
    python migrate.py <file_or_directory> --dry-run    # Preview changes
    python migrate.py <file_or_directory> -v           # Verbose output
"""

import sys
import os
import re
import argparse
import mimetypes
from pathlib import Path
from typing import Tuple, List


# ============================================================================
# PATH MIGRATION FUNCTIONS
# ============================================================================

def fix_colabfold_paths(content: str) -> Tuple[str, List[str]]:
    """Fix ColabFold installation paths."""
    changes = []

    old_path = "/toolbox/LocalColabFold/localcolabfold/colabfold-conda/bin"
    new_path = "/quobyte/jbsiegelgrp/software/LocalColabFold/localcolabfold/colabfold-conda/bin"

    if old_path in content:
        content = content.replace(old_path, new_path)
        changes.append(f"ColabFold PATH: {old_path} → {new_path}")

    return content, changes


def fix_ligandmpnn_paths(content: str) -> Tuple[str, List[str]]:
    """Fix LigandMPNN installation paths (case-insensitive)."""
    changes = []

    pattern = r'/toolbox/([Ll]igand[Mm][Pp][Nn][Nn])'
    matches = re.findall(pattern, content)

    if matches:
        content = re.sub(pattern, r'/quobyte/jbsiegelgrp/\1', content)
        for match in set(matches):
            old_path = f"/toolbox/{match}"
            new_path = f"/quobyte/jbsiegelgrp/{match}"
            changes.append(f"LigandMPNN: {old_path} → {new_path}")

    return content, changes


def fix_rfdiffusion_paths(content: str) -> Tuple[str, List[str]]:
    """Fix RFdiffusion installation paths from various locations."""
    changes = []

    new_rfdiffusion_path = '/quobyte/jbsiegelgrp/software/RFdiffusion'

    rfdiffusion_patterns = [
        r'/home/[^/\s]+/RFdiffusion',
        r'/share/[^/\s]+/[^/\s]+/RFdiffusion',
        r'/toolbox/RFdiffusion',
        r'/opt/RFdiffusion',
        r'/usr/local/RFdiffusion',
        r'\./RFdiffusion',
        r'~/RFdiffusion',
        r'\$HOME/RFdiffusion',
    ]

    for pattern in rfdiffusion_patterns:
        matches = re.findall(pattern, content)
        if matches:
            for match in set(matches):
                content = content.replace(match, new_rfdiffusion_path)
                changes.append(f"RFdiffusion: {match} → {new_rfdiffusion_path}")

    return content, changes


def fix_rfdiffusion_conda_envs(content: str) -> Tuple[str, List[str]]:
    """Fix RFdiffusion conda environment paths."""
    changes = []

    new_env = '/quobyte/jbsiegelgrp/software/envs/SE3nv'

    conda_pattern = r'conda\s+activate\s+([^\s\n]+)'
    matches = re.findall(conda_pattern, content)

    for match in matches:
        if any(env_name in match.lower() for env_name in ['se3', 'rfdiff', 'rf-diff', 'diffusion']):
            old_command = f'conda activate {match}'
            new_command = f'conda activate {new_env}'
            content = content.replace(old_command, new_command)
            changes.append(f"RFdiffusion conda env: {match} → {new_env}")

    return content, changes


def fix_rosetta_paths(content: str) -> Tuple[str, List[str]]:
    """Fix Rosetta installation paths and binary names."""
    changes = []

    # Fix Rosetta base paths
    rosetta_base_pattern = r'(/[^ \t\n]+/[Rr]osetta[^ \t\n]*/main)'
    new_rosetta_base = '/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main'

    matches = re.findall(rosetta_base_pattern, content)
    for old_base in set(matches):
        # Skip if it's already the correct path
        if old_base != new_rosetta_base:
            content = content.replace(old_base, new_rosetta_base)
            changes.append(f"Rosetta base: {old_base} → {new_rosetta_base}")

    # Fix Rosetta binary names: .default.linuxgccrelease → .static.linuxgccrelease
    old_suffix = '.default.linuxgccrelease'
    new_suffix = '.static.linuxgccrelease'

    if old_suffix in content:
        count = content.count(old_suffix)
        content = content.replace(old_suffix, new_suffix)
        changes.append(f"Rosetta binaries: .default → .static ({count} occurrence(s))")

    return content, changes


def fix_hardcoded_paths(content: str) -> Tuple[str, List[str]]:
    """Replace hardcoded paths from /share/siegellab/ to /quobyte/jbsiegelgrp/."""
    changes = []

    old_base = '/share/siegellab/'
    new_base = '/quobyte/jbsiegelgrp/'

    count = content.count(old_base)
    if count > 0:
        content = content.replace(old_base, new_base)
        changes.append(f"General paths: {old_base} → {new_base} ({count} occurrence(s))")

    return content, changes


# ============================================================================
# SLURM CONFIGURATION FUNCTIONS
# ============================================================================

def parse_time_to_days(time_str: str) -> float:
    """Parse SLURM time format to days."""
    if '-' in time_str:
        days, time_part = time_str.split('-', 1)
        return int(days)
    else:
        parts = time_str.split(':')
        if len(parts) >= 1:
            hours = int(parts[0])
            return hours / 24.0
    return 0


def fix_slurm_partitions(content: str, use_high_partition: bool = False) -> Tuple[str, List[str]]:
    """Fix SLURM partition configurations."""
    changes = []
    lines = content.split('\n')
    modified_lines = []

    gpu_detected = False
    cpu_partition_target = 'high' if use_high_partition else 'low'

    for line in lines:
        if not line.strip().startswith('#SBATCH'):
            modified_lines.append(line)
            continue

        original_line = line

        # Detect GPU partitions
        if any(gpu_part in line for gpu_part in ['jbsiegel-gpu', 'gpu-a100']):
            gpu_detected = True

            # Fix old GPU partition name
            if 'jbsiegel-gpu' in line:
                line = re.sub(r'--partition=jbsiegel-gpu', '--partition=gpu-a100', line)
                line = re.sub(r'-p jbsiegel-gpu', '-p gpu-a100', line)
                if line != original_line:
                    changes.append("GPU partition: jbsiegel-gpu → gpu-a100")

            # Add account for GPU jobs if missing
            if 'gpu-a100' in line and '--account=' not in line and '-A ' not in line:
                line = line + ' --account=genome-center-grp'
                changes.append("Added GPU account: genome-center-grp")

        # Fix CPU partitions (production → low/high)
        elif '--partition=production' in line or '-p production' in line:
            line = re.sub(r'--partition=production', f'--partition={cpu_partition_target}', line)
            line = re.sub(r'-p production', f'-p {cpu_partition_target}', line)
            changes.append(f"CPU partition: production → {cpu_partition_target}")

        modified_lines.append(line)

    content = '\n'.join(modified_lines)

    # Add account line for GPU jobs if needed
    if gpu_detected and '--account=genome-center-grp' not in content and '-A genome-center-grp' not in content:
        final_lines = []
        account_added = False

        for line in modified_lines:
            final_lines.append(line)
            if line.strip().startswith('#SBATCH') and 'gpu-a100' in line and not account_added:
                final_lines.append('#SBATCH --account=genome-center-grp')
                changes.append("Added GPU account line: --account=genome-center-grp")
                account_added = True

        content = '\n'.join(final_lines)
        modified_lines = final_lines

    # Add --requeue for low partition if missing
    if not use_high_partition and '--partition=low' in content and '--requeue' not in content:
        final_lines = []
        requeue_added = False

        for i, line in enumerate(modified_lines):
            final_lines.append(line)
            if line.strip().startswith('#SBATCH') and not requeue_added:
                # Add after last SBATCH line
                has_more_sbatch = any(l.strip().startswith('#SBATCH') for l in modified_lines[i+1:])
                if not has_more_sbatch:
                    final_lines.append('#SBATCH --requeue')
                    changes.append("Added --requeue flag for low partition")
                    requeue_added = True

        content = '\n'.join(final_lines)

    return content, changes


def fix_time_limits(content: str, use_high_partition: bool = False) -> Tuple[str, List[str]]:
    """Adjust time limits based on partition constraints."""
    changes = []

    # Only enforce time limits for low partition
    if use_high_partition:
        return content, changes

    if '--partition=low' not in content:
        return content, changes

    lines = content.split('\n')
    modified_lines = []
    time_adjusted = False

    for line in lines:
        if line.strip().startswith('#SBATCH'):
            # Check for time specification
            time_match = re.search(r'--time=([^\s]+)', line)
            if not time_match:
                time_match = re.search(r'-t\s+([^\s]+)', line)

            if time_match:
                time_str = time_match.group(1)
                days = parse_time_to_days(time_str)

                if days > 3:
                    line = re.sub(r'--time=[^\s]+', '--time=3-00:00:00', line)
                    line = re.sub(r'-t\s+[^\s]+', '-t 3-00:00:00', line)
                    time_adjusted = True
                    changes.append(f"Time limit: {time_str} → 3-00:00:00 (low partition max)")

        modified_lines.append(line)

    return '\n'.join(modified_lines), changes


# ============================================================================
# FILE PROCESSING
# ============================================================================

def is_text_file(filepath: Path) -> bool:
    """Check if a file is a text file."""
    mime_type, _ = mimetypes.guess_type(str(filepath))
    if mime_type and mime_type.startswith('text'):
        return True

    text_extensions = {
        '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
        '.md', '.rst', '.csv', '.log', '.ini', '.cfg', '.conf', '.sh', '.bash',
        '.c', '.cpp', '.h', '.hpp', '.java', '.r', '.R', '.m', '.mat', '.dat',
        '.sbatch', '.slurm'
    }

    if filepath.suffix.lower() in text_extensions:
        return True

    # Check for files without extensions (like scripts)
    if not filepath.suffix:
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(512)
                if b'\x00' in chunk:
                    return False
                try:
                    chunk.decode('utf-8')
                    return True
                except UnicodeDecodeError:
                    return False
        except:
            return False

    return False


def process_file(filepath: Path, args: argparse.Namespace) -> bool:
    """Process a single file and apply all fixes."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
        return False

    original_content = content
    all_changes = []

    # Apply all path fixes
    content, changes = fix_colabfold_paths(content)
    all_changes.extend(changes)

    content, changes = fix_ligandmpnn_paths(content)
    all_changes.extend(changes)

    content, changes = fix_rfdiffusion_paths(content)
    all_changes.extend(changes)

    content, changes = fix_rfdiffusion_conda_envs(content)
    all_changes.extend(changes)

    content, changes = fix_rosetta_paths(content)
    all_changes.extend(changes)

    content, changes = fix_hardcoded_paths(content)
    all_changes.extend(changes)

    # Apply SLURM fixes
    content, changes = fix_slurm_partitions(content, args.high)
    all_changes.extend(changes)

    content, changes = fix_time_limits(content, args.high)
    all_changes.extend(changes)

    # No changes needed
    if not all_changes:
        return False

    # Determine output filename
    if args.in_place:
        output_filepath = filepath
    else:
        output_filepath = filepath.parent / f"{filepath.stem}_fixed{filepath.suffix}"

    # Show changes
    if args.dry_run:
        print(f"\n[DRY RUN] Would modify: {filepath}")
        for change in all_changes:
            print(f"  • {change}")

        if args.verbose:
            lines = original_content.split('\n')
            new_lines = content.split('\n')
            for i, (old_line, new_line) in enumerate(zip(lines, new_lines), 1):
                if old_line != new_line:
                    print(f"  Line {i}:")
                    print(f"    - {old_line.strip()}")
                    print(f"    + {new_line.strip()}")

        if not args.in_place:
            print(f"  Output would be: {output_filepath}")
    else:
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"\nModified: {filepath}")
            for change in all_changes:
                print(f"  • {change}")

            if not args.in_place:
                print(f"  → Output: {output_filepath}")

            return True
        except Exception as e:
            print(f"Error writing file '{output_filepath}': {e}", file=sys.stderr)
            return False

    return True


def process_path(path: Path, args: argparse.Namespace) -> Tuple[int, int]:
    """Process a file or directory."""
    files_checked = 0
    files_modified = 0

    if path.is_file():
        if is_text_file(path):
            files_checked = 1
            if process_file(path, args):
                files_modified = 1
    elif path.is_dir():
        for root, dirs, files in os.walk(path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            for filename in files:
                filepath = Path(root) / filename

                if not is_text_file(filepath):
                    continue

                files_checked += 1
                if process_file(filepath, args):
                    files_modified += 1
    else:
        print(f"Error: '{path}' is neither a file nor directory", file=sys.stderr)
        sys.exit(1)

    return files_checked, files_modified


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Unified migration script for HIVE cluster transition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script consolidates all migration functionality:
  • Software paths: ColabFold, LigandMPNN, RFdiffusion, Rosetta
  • SLURM configs: Partitions, accounts, requeue flags
  • Time limits: Enforces partition constraints
  • General paths: /share/siegellab/ → /quobyte/jbsiegelgrp/

Examples:
  python migrate.py script.sh                  # Fix single file
  python migrate.py /path/to/scripts/          # Fix directory recursively
  python migrate.py script.sh --high           # Use high partition (Rosetta)
  python migrate.py script.sh --in-place       # Modify file directly
  python migrate.py . --dry-run                # Preview changes
  python migrate.py . -v --dry-run             # Verbose preview

Replaces:
  • colab_fix.py
  • ligandmpnn_fix.py
  • rfdiffusion_fix.py
  • rosetta_fix.py
  • pathMigrator.py (for SLURM configs)
"""
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='File or directory to process (default: current directory)'
    )
    parser.add_argument(
        '--high',
        action='store_true',
        help='Use high partition instead of low (for long Rosetta jobs)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )
    parser.add_argument(
        '--in-place',
        action='store_true',
        help='Modify files in place instead of creating _fixed versions'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed line-by-line changes'
    )

    args = parser.parse_args()
    path = Path(args.path)

    if not path.exists():
        print(f"Error: Path '{path}' does not exist", file=sys.stderr)
        sys.exit(1)

    # Print header
    print("=" * 70)
    print("HIVE Cluster Migration Tool")
    print("=" * 70)

    abs_path = path.resolve()
    print(f"\nTarget: {abs_path}")

    if args.high:
        print("Mode: Using HIGH partition (30 day max)")
    else:
        print("Mode: Using LOW partition (3 day max, auto-requeue)")

    if args.dry_run:
        print("*** DRY RUN MODE - No files will be modified ***")

    if args.in_place:
        print("*** IN-PLACE MODE - Files will be modified directly ***")
    else:
        print("Mode: Creating *_fixed versions of modified files")

    # Confirmation for non-dry-run
    if not args.dry_run and path.is_dir():
        print(f"\n⚠️  WARNING: This will process ALL files in:")
        print(f"   {abs_path}")
        print(f"   and ALL subdirectories beneath it!")

        response = input("\nContinue? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Aborted.")
            return

    print()

    # Process the path
    files_checked, files_modified = process_path(path, args)

    # Print summary
    print("\n" + "=" * 70)
    print("Summary:")
    print(f"  Files checked: {files_checked}")
    print(f"  Files {'that would be' if args.dry_run else ''} modified: {files_modified}")

    if files_modified > 0:
        if args.dry_run:
            print(f"\nRe-run without --dry-run to apply changes")
        else:
            print(f"\nIMPORTANT: Review the changes and test your scripts!")


if __name__ == '__main__':
    main()
