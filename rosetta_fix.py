#!/usr/bin/env python3
"""
Script to fix Rosetta paths and SLURM configurations for Hive transition.
Usage: python rosetta_fix.py <script_filename>
"""

import sys
import os
import re
from pathlib import Path


def fix_rosetta_paths(content):
    """Fix Rosetta installation paths and binary names."""
    changes = []
    
    # First, replace the base Rosetta path
    old_rosetta_base = '/share/siegellab/software/kschu/Rosetta/main'
    new_rosetta_base = '/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main'
    
    # Count base path replacements
    base_count = content.count(old_rosetta_base)
    if base_count > 0:
        content = content.replace(old_rosetta_base, new_rosetta_base)
        changes.append(f"Updated Rosetta base path ({base_count} occurrences): {old_rosetta_base} -> {new_rosetta_base}")
    
    # Now fix the binary names from default.linuxgccrelease to static.linuxgccrelease
    # Pattern to match Rosetta binaries with .default.linuxgccrelease extension
    pattern = r'(\w+)\.default\.linuxgccrelease'
    
    # Find all matches
    matches = re.findall(pattern, content)
    if matches:
        unique_binaries = list(set(matches))
        for binary in unique_binaries:
            old_binary = f"{binary}.default.linuxgccrelease"
            new_binary = f"{binary}.static.linuxgccrelease"
            content = content.replace(old_binary, new_binary)
            changes.append(f"Updated Rosetta binary: {old_binary} -> {new_binary}")
    
    # Also check for any other Rosetta paths that might not follow the exact pattern
    # Look for other common Rosetta installation locations
    other_rosetta_patterns = [
        r'/home/[^/]+/[Rr]osetta',
        r'/opt/[Rr]osetta',
        r'/usr/local/[Rr]osetta',
        r'\$ROSETTA3?/main',  # Environment variable references
        r'\$\{ROSETTA3?\}/main',
    ]
    
    # Check if any of these patterns exist (but not the ones we already fixed)
    for pattern in other_rosetta_patterns:
        if re.search(pattern, content):
            changes.append(f"WARNING: Found potential Rosetta path pattern '{pattern}' that may need manual review")
    
    return content, changes


def parse_time_to_days(time_str):
    """Parse SLURM time format to days."""
    # Handle various time formats: D-HH:MM:SS, HH:MM:SS, MM:SS, etc.
    if '-' in time_str:
        # Format: D-HH:MM:SS
        days, time_part = time_str.split('-', 1)
        return int(days)
    else:
        # Format: HH:MM:SS or MM:SS
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
    max_days = 30 if use_high_partition else 3
    
    for line in lines:
        original_line = line
        
        # Check if this is an sbatch line
        if line.strip().startswith('#SBATCH'):
            # Fix partition from production to low/high
            if '--partition=production' in line or '-p production' in line:
                line = re.sub(r'--partition=production', f'--partition={target_partition}', line)
                line = re.sub(r'-p production', f'-p {target_partition}', line)
                changes.append(f"Updated partition: production -> {target_partition}")
            
            # Also check for GPU partitions that shouldn't be there
            elif '--partition=jbsiegel-gpu' in line or '-p jbsiegel-gpu' in line:
                line = re.sub(r'--partition=jbsiegel-gpu', f'--partition={target_partition}', line)
                line = re.sub(r'-p jbsiegel-gpu', f'-p {target_partition}', line)
                changes.append(f"Updated partition: jbsiegel-gpu -> {target_partition} (Rosetta doesn't need GPUs)")
            elif '--partition=gpu-a100' in line or '-p gpu-a100' in line:
                line = re.sub(r'--partition=gpu-a100', f'--partition={target_partition}', line)
                line = re.sub(r'-p gpu-a100', f'-p {target_partition}', line)
                changes.append(f"Updated partition: gpu-a100 -> {target_partition} (Rosetta doesn't need GPUs)")
            
            # Check time limits
            time_match = re.search(r'--time=([^\s]+)', line) or re.search(r'-t\s+([^\s]+)', line)
            if time_match and target_partition == 'low':
                time_str = time_match.group(1)
                days = parse_time_to_days(time_str)
                if days > 3:
                    # Replace with 3 days
                    line = re.sub(r'--time=[^\s]+', '--time=3-00:00:00', line)
                    line = re.sub(r'-t\s+[^\s]+', '-t 3-00:00:00', line)
                    time_adjusted = True
                    changes.append(f"Adjusted time limit from {time_str} to 3-00:00:00 (max for low partition)")
        
        modified_lines.append(line)
    
    # Add requeue for low partition if not already present
    if target_partition == 'low':
        content_check = '\n'.join(modified_lines)
        if '--requeue' not in content_check:
            # Find where to add requeue
            final_lines = []
            for i, line in enumerate(modified_lines):
                final_lines.append(line)
                if line.strip().startswith('#SBATCH') and not requeue_added:
                    # Look ahead to see if there are more #SBATCH lines
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
    
    # Only replace the base path, keeping everything after it
    old_base = '/share/siegellab/'
    new_base = '/quobyte/jbsiegelgrp/'
    
    # Count occurrences for reporting (excluding the Rosetta paths we already handled)
    # We need to count only the non-Rosetta paths
    temp_content = content.replace('/share/siegellab/software/kschu/Rosetta', 'TEMP_ROSETTA_MARKER')
    count = temp_content.count(old_base)
    
    if count > 0:
        changes.append(f"Updated {count} occurrence(s) of {old_base} to {new_base} (non-Rosetta paths)")
    
    # Simple replacement - this preserves everything after the base path
    content = content.replace(old_base, new_base)
    
    return content, changes


def process_script(filename, use_high_partition=False):
    """Process the script file and apply all fixes."""
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found.")
        return False
    
    # Read the original file
    try:
        with open(filename, 'r') as f:
            original_content = f.read()
    except Exception as e:
        print(f"Error reading file '{filename}': {e}")
        return False
    
    content = original_content
    all_changes = []
    
    # Apply Rosetta fixes first (before general path fixes)
    content, rosetta_changes = fix_rosetta_paths(content)
    all_changes.extend(rosetta_changes)
    
    content, slurm_changes, time_adjusted = fix_slurm_flags(content, use_high_partition)
    all_changes.extend(slurm_changes)
    
    # Apply general path fixes last
    content, hardcoded_changes = fix_hardcoded_paths(content)
    all_changes.extend(hardcoded_changes)
    
    # Generate output filename
    path = Path(filename)
    stem = path.stem
    suffix = path.suffix
    output_filename = str(path.parent / f"{stem}_fixed{suffix}")
    
    # Write the fixed content
    try:
        with open(output_filename, 'w') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing file '{output_filename}': {e}")
        return False
    
    # Show summary
    print(f"Processing complete!")
    print(f"Input file: {filename}")
    print(f"Output file: {output_filename}")
    print(f"\nChanges made:")
    
    if all_changes:
        for i, change in enumerate(all_changes, 1):
            print(f"  {i}. {change}")
    else:
        print("  No changes were needed.")
    
    # Additional note about Rosetta version
    if any('Rosetta' in change for change in all_changes):
        print("\nNOTE: This script has updated to Rosetta 3.14 (Rosetta_314).")
        print("      Binary names have been changed from .default.linuxgccrelease to .static.linuxgccrelease")
    
    # Note about time adjustment
    if time_adjusted:
        print("\nWARNING: Time limit was adjusted to 3 days (maximum for low partition).")
        print("         Consider using --high flag for longer jobs (up to 30 days).")
    
    return True


def main():
    """Main function."""
    # Check for --high flag
    use_high = '--high' in sys.argv
    if use_high:
        sys.argv.remove('--high')
    
    if len(sys.argv) != 2:
        print("Usage: python rosetta_fix.py <script_filename> [--high]")
        print("\nThis script fixes Rosetta paths and SLURM configurations for Hive transition:")
        print("  - Updates Rosetta paths from /share/siegellab/software/kschu/Rosetta/main/")
        print("    to /quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/")
        print("  - Changes Rosetta binaries from .default.linuxgccrelease to .static.linuxgccrelease")
        print("  - Changes SLURM partition from production to low (default) or high (with --high flag)")
        print("  - Adds --requeue flag for low partition jobs")
        print("  - Enforces time limits: 3 days max for low, 30 days max for high")
        print("  - Updates base paths from /share/siegellab/ to /quobyte/jbsiegelgrp/")
        print("  - Saves result with '_fixed' appended to filename")
        print("\nOptions:")
        print("  --high    Use high partition (max 30 days) instead of low (max 3 days)")
        sys.exit(1)
    
    script_filename = sys.argv[1]
    success = process_script(script_filename, use_high)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()