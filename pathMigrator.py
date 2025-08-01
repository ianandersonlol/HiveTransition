#!/usr/bin/env python3

import os
import sys
import argparse
import mimetypes
from pathlib import Path

def is_text_file(filepath):
    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type and mime_type.startswith('text'):
        return True
    
    text_extensions = {
        '.txt', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
        '.md', '.rst', '.csv', '.log', '.ini', '.cfg', '.conf', '.sh', '.bash',
        '.c', '.cpp', '.h', '.hpp', '.java', '.r', '.R', '.m', '.mat', '.dat'
    }
    
    if Path(filepath).suffix.lower() in text_extensions:
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

def replace_in_file(filepath, old_path, new_path, dry_run=False):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_path in content:
            new_content = content.replace(old_path, new_path)
            
            if dry_run:
                print(f"[DRY RUN] Would modify: {filepath}")
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if old_path in line:
                        print(f"  Line {i+1}: {line.strip()}")
                        print(f"  →        {line.replace(old_path, new_path).strip()}")
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Modified: {filepath}")
            
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {str(e)}", file=sys.stderr)
        return False

def process_directory(directory, old_path, new_path, dry_run=False):
    directory = Path(directory)
    files_modified = 0
    files_checked = 0
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            
            if not is_text_file(filepath):
                continue
            
            files_checked += 1
            if replace_in_file(filepath, old_path, new_path, dry_run):
                files_modified += 1
    
    return files_checked, files_modified

def main():
    parser = argparse.ArgumentParser(
        description='Replace /share/siegellab/ with /quobyte/jbsiegelgrp/ in all files'
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
        '--old-path',
        default='/share/siegellab/',
        help='Path to replace (default: /share/siegellab/)'
    )
    parser.add_argument(
        '--new-path',
        default='/quobyte/jbsiegelgrp/',
        help='Replacement path (default: /quobyte/jbsiegelgrp/)'
    )
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist", file=sys.stderr)
        sys.exit(1)
    
    print(f"Processing directory: {os.path.abspath(args.directory)}")
    print(f"Replacing: '{args.old_path}' → '{args.new_path}'")
    if args.dry_run:
        print("*** DRY RUN MODE - No files will be modified ***")
    print()
    
    files_checked, files_modified = process_directory(
        args.directory,
        args.old_path,
        args.new_path,
        args.dry_run
    )
    
    print()
    print(f"Summary:")
    print(f"  Files checked: {files_checked}")
    print(f"  Files {'that would be' if args.dry_run else ''} modified: {files_modified}")

if __name__ == '__main__':
    main()