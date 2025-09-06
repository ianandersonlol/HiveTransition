#!/usr/bin/env python3
"""
Script to fix Rosetta paths and SLURM configurations for Hive transition.
Usage:
    python rosetta_fix.py <script_filename_or_directory> [--high]

Features:
    - Handles either a single script file or all .sh files recursively within a directory
    - Updates Rosetta paths and binaries
    - Normalizes SLURM partition and time settings
    - Adds --requeue flag if missing (low partition)
    - Fixes hardcoded /share/siegellab/ paths
    - Saves result with '_fixed' appended to filename
"""

import sys
import os
import re
from pathlib import Path

# --- Fix functions ---

def fix_rosetta_jobfile(content):
    """Normalize Rosetta paths, binaries, and SLURM flags."""
    changes = []
    rosetta_base_pattern = r'(/[^ \t\n]+/[Rr]osetta[^ \t\n]*/main)'
    new_rosetta_base = '/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main'

    matches = re.findall(rosetta_base_pattern, content)
    unique_matches = set(matches)
    for old_base in unique_matches:
        content = content.replace(old_base, new_rosetta_base)
        changes.append(f"Updated base path: {old_base} -> {new_rosetta_base}")

    # Replace .default.linuxgccrelease with .static.linuxgccrelease
    content, n1 = re.subn(r'\.default\.linuxgccrelease', '.static.linuxgccrelease', content)
    if n1 > 0:
        changes.append(f"Updated {n1} binaries from 'default' to 'static'")

    # Partition: from production to low
    content, n2 = re.subn(r'(#SBATCH\s+--partition=)\S+', r'\1low', content)
    if n2 > 0:
        changes.append("Updated --partition= to 'low'")

    # Add --requeue if missing
    if "--requeue" not in content:
        content = content.replace("#SBATCH --partition=low",
                                  "#SBATCH --partition=low\n#SBATCH --requeue")
        changes.append("Added --requeue flag")

    return content, changes


def parse_time_to_days(time_str):
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


def fix_slurm_flags(content, use_high_partition=False):
    """Fix SLURM sbatch flags for Rosetta (CPU-only jobs)."""
    changes = []
    lines = content.split('\n')
    modified_lines = []
    requeue_added = False
    time_adjusted = False

    target_partition = 'high' if use_high_partition else 'low'

    for line in lines:
        if line.strip().startswith('#SBATCH'):
            if '--partition=production' in line or '-p production' in line:
                line = re.sub(r'--partition=production', f'--partition={target_partition}', line)
                line = re.sub(r'-p production', f'-p {target_partition}', line)
                changes.append(f"Updated partition: production -> {target_partition}")

            elif '--partition=jbsiegel-gpu' in line or '-p jbsiegel-gpu' in line:
                line = re.sub(r'--partition=jbsiegel-gpu', f'--partition={target_partition}', line)
                line = re.sub(r'-p jbsiegel-gpu', f'-p {target_partition}', line)
                changes.append("Updated GPU partition -> Rosetta is CPU-only")

            elif '--partition=gpu-a100' in line or '-p gpu-a100' in line:
                line = re.sub(r'--partition=gpu-a100', f'--partition={target_partition}', line)
                line = re.sub(r'-p gpu-a100', f'-p {target_partition}', line)
                changes.append("Updated A100 GPU partition -> Rosetta is CPU-only")

            elif (time_match := re.search(r'--time=([^\s]+)', line)
                    or re.search(r'-t\s+([^\s]+)', line)):
                if target_partition == 'low':
                    time_str = time_match.group(1)
                    days = parse_time_to_days(time_str)
                    if days > 3:
                        line = re.sub(r'--time=[^\s]+', '--time=3-00:00:00', line)
                        line = re.sub(r'-t\s+[^\s]+', '-t 3-00:00:00', line)
                        time_adjusted = True
                        changes.append("Adjusted time limit to 3 days (low partition max)")

        modified_lines.append(line)

    # Add --requeue if needed
    if target_partition == 'low':
        content_check = '\n'.join(modified_lines)
        if '--requeue' not in content_check:
            final_lines = []
            for i, line in enumerate(modified_lines):
                final_lines.append(line)
                if line.strip().startswith('#SBATCH') and not requeue_added:
                    has_more_sbatch = any(l.strip().startswith('#SBATCH') for l in modified_lines[i+1:])
                    if not has_more_sbatch:
                        final_lines.append('#SBATCH --requeue')
                        changes.append("Added --requeue flag for low partition")
                        requeue_added = True
            modified_lines = final_lines

    return '\n'.join(modified_lines), changes, time_adjusted


def fix_hardcoded_paths(content):
    """Replace hardcoded paths from /share/siegellab/ to /quobyte/jbsiegelgrp/."""
    changes = []
    old_base = '/share/siegellab/'
    new_base = '/quobyte/jbsiegelgrp/'

    temp_content = content.replace('/share/siegellab/software/kschu/Rosetta', 'TEMP_ROSETTA_MARKER')
    count = temp_content.count(old_base)

    if count > 0:
        changes.append(f"Updated {count} occurrence(s) of {old_base} to {new_base}")

    content = content.replace(old_base, new_base)
    return content, changes


# --- Main file processor ---

def process_script(filename, use_high_partition=False):
    """Process the script file and apply all fixes."""
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return False

    try:
        with open(filename, 'r') as f:
            original_content = f.read()
    except Exception as e:
        print(f"Error reading file '{filename}': {e}")
        return False

    content = original_content
    all_changes = []

    content, rosetta_changes = fix_rosetta_jobfile(content)
    all_changes.extend(rosetta_changes)

    content, slurm_changes, time_adjusted = fix_slurm_flags(content, use_high_partition)
    all_changes.extend(slurm_changes)

    content, hardcoded_changes = fix_hardcoded_paths(content)
    all_changes.extend(hardcoded_changes)

    path = Path(filename)
    output_filename = str(path.parent / f"{path.stem}_fixed{path.suffix}")

    try:
        with open(output_filename, 'w') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing file '{output_filename}': {e}")
        return False

    print(f"\n=== Processed {filename} ===")
    print(f"Output written to: {output_filename}")

    if all_changes:
        for i, change in enumerate(all_changes, 1):
            print(f"  {i}. {change}")
    else:
        print("  No changes were needed.")

    if any('Rosetta' in change for change in all_changes):
        print("NOTE: Updated to Rosetta 3.14 binaries.")

    if time_adjusted:
        print("WARNING: Time adjusted to 3 days (low partition max). Use --high for longer jobs.")

    return True


# --- Entry point ---

def main():
    use_high = '--high' in sys.argv
    if use_high:
        sys.argv.remove('--high')

    if len(sys.argv) != 2:
        print("Usage: python rosetta_fix.py <script_filename_or_directory> [--high]")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if input_path.is_file():
        process_script(str(input_path), use_high)

    elif input_path.is_dir():
        sh_files = list(input_path.rglob("*.sh"))
        if not sh_files:
            print(f"No .sh files found under {input_path}")
            sys.exit(1)

        for sh_file in sh_files:
            process_script(str(sh_file), use_high)

    else:
        print(f"Error: Path '{input_path}' is neither a file nor a directory.")
        sys.exit(1)


if __name__ == "__main__":
    main()
