#!/usr/bin/env python3
"""
Script to fix ColabFold paths and SLURM configurations for Hive transition.
Usage: python colab_fix.py <script_filename>
"""

import sys
import os
import re
from pathlib import Path


def fix_path_exports(content):
    """Fix PATH export statements for ColabFold."""
    changes = []
    
    # Pattern to match the old ColabFold path in export statements
    old_path = "/toolbox/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH"
    new_path = "/quobyte/jbsiegelgrp/software/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH"
    
    if old_path in content:
        content = content.replace(old_path, new_path)
        changes.append(f"Updated ColabFold PATH: {old_path} -> {new_path}")
    
    return content, changes


def fix_slurm_flags(content):
    """Fix SLURM sbatch flags."""
    changes = []
    lines = content.split('\n')
    modified_lines = []
    
    for line in lines:
        original_line = line
        
        # Check if this is an sbatch line
        if line.strip().startswith('#SBATCH'):
            # Fix partition
            if '--partition=jbsiegel-gpu' in line or '-p jbsiegel-gpu' in line:
                line = re.sub(r'--partition=jbsiegel-gpu', '--partition=gpu-a100', line)
                line = re.sub(r'-p jbsiegel-gpu', '-p gpu-a100', line)
                changes.append(f"Updated partition: jbsiegel-gpu -> gpu-a100")
            
            # Add account if not present and this is a partition line for gpu-a100
            if ('--partition=gpu-a100' in line or '-p gpu-a100' in line) and '--account=' not in line and '-A ' not in line:
                # Add account flag to the line
                line = line + ' --account=genome-center-grp'
                changes.append("Added SLURM account: genome-center-grp")
        
        # Check for standalone account additions needed
        elif line.strip().startswith('#SBATCH') and '--account=' not in content and '-A ' not in content:
            # This is a bit more complex - we need to check if we have gpu partition anywhere
            if 'gpu-a100' in content and '#SBATCH --account=genome-center-grp' not in content:
                # We'll handle this by adding the account line after we find the first #SBATCH line
                pass
        
        modified_lines.append(line)
    
    # Check if we need to add account line for gpu-a100 partitions
    content_check = '\n'.join(modified_lines)
    if 'gpu-a100' in content_check and '--account=genome-center-grp' not in content_check and '-A genome-center-grp' not in content_check:
        # Find the first #SBATCH line and add account after it
        final_lines = []
        account_added = False
        for line in modified_lines:
            final_lines.append(line)
            if line.strip().startswith('#SBATCH') and not account_added:
                final_lines.append('#SBATCH --account=genome-center-grp')
                changes.append("Added SLURM account line: --account=genome-center-grp")
                account_added = True
        modified_lines = final_lines
    
    return '\n'.join(modified_lines), changes


def fix_hardcoded_paths(content):
    """Replace hardcoded paths from /share/siegellab/ to /quobyte/jbsiegelgrp/."""
    changes = []
    
    # Only replace the base path, keeping everything after it
    old_base = '/share/siegellab/'
    new_base = '/quobyte/jbsiegelgrp/'
    
    # Count occurrences for reporting
    count = content.count(old_base)
    if count > 0:
        changes.append(f"Updated {count} occurrence(s) of {old_base} to {new_base}")
    
    # Simple replacement - this preserves everything after the base path
    content = content.replace(old_base, new_base)
    
    return content, changes


def process_script(filename):
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
    
    # Apply all fixes
    content, path_changes = fix_path_exports(content)
    all_changes.extend(path_changes)
    
    content, slurm_changes = fix_slurm_flags(content)
    all_changes.extend(slurm_changes)
    
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
    
    return True


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python colab_fix.py <script_filename>")
        print("\nThis script fixes ColabFold paths and SLURM configurations for Hive transition:")
        print("  - Updates ColabFold PATH from /toolbox/ to /quobyte/jbsiegelgrp/")
        print("  - Changes SLURM partition from jbsiegel-gpu to gpu-a100")
        print("  - Adds --account=genome-center-grp for GPU jobs")
        print("  - Updates hardcoded paths from /share/siegellab/ to /quobyte/jbsiegelgrp/")
        print("  - Saves result with '_fixed' appended to filename")
        sys.exit(1)
    
    script_filename = sys.argv[1]
    success = process_script(script_filename)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()