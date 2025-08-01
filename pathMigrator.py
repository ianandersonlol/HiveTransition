#!/usr/bin/env python3
"""
Comprehensive path migration script for HIVE cluster transition.
Updates all software paths to their new locations on HIVE.
"""

import os
import sys
import re
import argparse
import mimetypes
from pathlib import Path

def is_text_file(filepath):
    """Check if a file is a text file."""
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type and mime_type.startswith('text'):
        return True
    
    text_extensions = {
        '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
        '.md', '.rst', '.csv', '.log', '.ini', '.cfg', '.conf', '.sh', '.bash',
        '.c', '.cpp', '.h', '.hpp', '.java', '.r', '.R', '.m', '.mat', '.dat',
        '.sbatch', '.slurm'
    }
    
    if Path(filepath).suffix.lower() in text_extensions:
        return True
    
    # Check for files without extensions (like scripts)
    if not Path(filepath).suffix:
        return True
    
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

def apply_software_fixes(content, verbose=False):
    """Apply all software-specific path fixes."""
    original_content = content
    changes = []
    
    # 1. ColabFold paths
    old_colabfold = "/toolbox/LocalColabFold/localcolabfold/colabfold-conda/bin"
    new_colabfold = "/quobyte/jbsiegelgrp/software/LocalColabFold/localcolabfold/colabfold-conda/bin"
    if old_colabfold in content:
        content = content.replace(old_colabfold, new_colabfold)
        changes.append(f"ColabFold: {old_colabfold} → {new_colabfold}")
    
    # 2. LigandMPNN paths (case-insensitive)
    ligandmpnn_pattern = r'/toolbox/([Ll]igand[Mm][Pp][Nn][Nn])'
    ligandmpnn_matches = re.findall(ligandmpnn_pattern, content)
    if ligandmpnn_matches:
        content = re.sub(ligandmpnn_pattern, r'/quobyte/jbsiegelgrp/\1', content)
        for match in set(ligandmpnn_matches):
            changes.append(f"LigandMPNN: /toolbox/{match} → /quobyte/jbsiegelgrp/{match}")
    
    # 3. RFdiffusion paths - various possible locations
    rfdiffusion_patterns = [
        (r'/home/[^/\s]+/RFdiffusion', '/quobyte/jbsiegelgrp/software/RFdiffusion'),
        (r'/share/[^/\s]+/[^/\s]+/RFdiffusion', '/quobyte/jbsiegelgrp/software/RFdiffusion'),
        (r'/toolbox/RFdiffusion', '/quobyte/jbsiegelgrp/software/RFdiffusion'),
        (r'/opt/RFdiffusion', '/quobyte/jbsiegelgrp/software/RFdiffusion'),
        (r'/usr/local/RFdiffusion', '/quobyte/jbsiegelgrp/software/RFdiffusion'),
        (r'\./RFdiffusion', '/quobyte/jbsiegelgrp/software/RFdiffusion'),
        (r'~/RFdiffusion', '/quobyte/jbsiegelgrp/software/RFdiffusion'),
        (r'\$HOME/RFdiffusion', '/quobyte/jbsiegelgrp/software/RFdiffusion'),
    ]
    
    for pattern, replacement in rfdiffusion_patterns:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            for match in set(matches):
                changes.append(f"RFdiffusion: {match} → {replacement}")
    
    # 4. RFdiffusion conda environments
    # Look for conda activate commands with RFdiffusion-related environments
    conda_pattern = r'conda\s+activate\s+([^\s\n]+)'
    conda_matches = re.findall(conda_pattern, content)
    
    for match in conda_matches:
        if any(env_name in match.lower() for env_name in ['se3', 'rfdiff', 'rf-diff', 'diffusion']):
            old_command = f'conda activate {match}'
            new_command = 'conda activate /quobyte/jbsiegelgrp/software/envs/SE3nv'
            content = content.replace(old_command, new_command)
            changes.append(f"RFdiffusion env: {match} → /quobyte/jbsiegelgrp/software/envs/SE3nv")
    
    # 5. Rosetta paths
    old_rosetta = '/share/siegellab/software/kschu/Rosetta/main'
    new_rosetta = '/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main'
    if old_rosetta in content:
        content = content.replace(old_rosetta, new_rosetta)
        changes.append(f"Rosetta: {old_rosetta} → {new_rosetta}")
    
    # 6. Rosetta binary names (default to static)
    rosetta_binary_pattern = r'(\w+)\.default\.linuxgccrelease'
    rosetta_matches = re.findall(rosetta_binary_pattern, content)
    if rosetta_matches:
        for binary in set(rosetta_matches):
            old_binary = f"{binary}.default.linuxgccrelease"
            new_binary = f"{binary}.static.linuxgccrelease"
            content = content.replace(old_binary, new_binary)
            changes.append(f"Rosetta binary: {old_binary} → {new_binary}")
    
    # 7. General path migration (last, so it doesn't interfere with specific paths)
    old_base = '/share/siegellab/'
    new_base = '/quobyte/jbsiegelgrp/'
    if old_base in content:
        # Count occurrences excluding the ones we already handled
        temp_content = content.replace(old_rosetta, 'TEMP_ROSETTA_MARKER')
        count = temp_content.count(old_base)
        if count > 0:
            content = content.replace(old_base, new_base)
            changes.append(f"General paths: {old_base} → {new_base} ({count} occurrences)")
    
    return content, changes

def process_file(filepath, dry_run=False, verbose=False):
    """Process a single file for path replacements."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content, changes = apply_software_fixes(content, verbose)
        
        if changes:
            if dry_run:
                print(f"\n[DRY RUN] Would modify: {filepath}")
                for change in changes:
                    print(f"  • {change}")
                
                if verbose:
                    # Show line-by-line changes
                    lines = content.split('\n')
                    new_lines = new_content.split('\n')
                    for i, (old_line, new_line) in enumerate(zip(lines, new_lines)):
                        if old_line != new_line:
                            print(f"  Line {i+1}:")
                            print(f"    - {old_line.strip()}")
                            print(f"    + {new_line.strip()}")
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"\nModified: {filepath}")
                for change in changes:
                    print(f"  • {change}")
            
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {str(e)}", file=sys.stderr)
        return False

def process_directory(directory, dry_run=False, verbose=False):
    """Process all files in a directory recursively."""
    directory = Path(directory)
    files_modified = 0
    files_checked = 0
    
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for filename in files:
            filepath = os.path.join(root, filename)
            
            if not is_text_file(filepath):
                continue
            
            files_checked += 1
            if process_file(filepath, dry_run, verbose):
                files_modified += 1
    
    return files_checked, files_modified

def main():
    parser = argparse.ArgumentParser(
        description='Migrate all software paths for HIVE cluster transition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script updates the following software paths:
  • ColabFold:   /toolbox/LocalColabFold → /quobyte/jbsiegelgrp/software/LocalColabFold
  • LigandMPNN:  /toolbox/ligandMPNN → /quobyte/jbsiegelgrp/ligandMPNN
  • RFdiffusion: Various locations → /quobyte/jbsiegelgrp/software/RFdiffusion
  • RFdiff envs: Various conda envs → /quobyte/jbsiegelgrp/software/envs/SE3nv
  • Rosetta:     Old Rosetta → /quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main
  • Rosetta bin: .default.linuxgccrelease → .static.linuxgccrelease
  • General:     /share/siegellab/ → /quobyte/jbsiegelgrp/

Examples:
  python pathMigrator.py                    # Process current directory
  python pathMigrator.py /path/to/scripts   # Process specific directory
  python pathMigrator.py --dry-run          # Preview changes without modifying
  python pathMigrator.py -v                 # Verbose output with line numbers
"""
    )
    
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to process (default: current directory)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying files'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed line-by-line changes'
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    print(f"HIVE Path Migration Tool")
    print(f"=" * 50)
    print(f"Processing directory: {os.path.abspath(args.directory)}")
    if args.dry_run:
        print("*** DRY RUN MODE - No files will be modified ***")
    print()
    
    files_checked, files_modified = process_directory(
        args.directory,
        args.dry_run,
        args.verbose
    )
    
    print(f"\n{'=' * 50}")
    print(f"Summary:")
    print(f"  Files checked: {files_checked}")
    print(f"  Files {'that would be' if args.dry_run else ''} modified: {files_modified}")
    
    if files_modified > 0 and not args.dry_run:
        print(f"\nIMPORTANT: Please review the changes and test your scripts!")

if __name__ == '__main__':
    main()