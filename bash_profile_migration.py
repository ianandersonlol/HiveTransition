#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import re
import subprocess
import tempfile
import socket
from pathlib import Path

def detect_conda_setup(line):
    """Detect various forms of conda initialization"""
    conda_patterns = [
        r'.*conda\.sh.*',  # source ~/miniconda3/etc/profile.d/conda.sh
        r'.*conda/bin/activate.*',  # source /path/to/conda/bin/activate
        r'.*miniconda.*init.*',  # conda init patterns
        r'.*anaconda.*init.*',  # anaconda init patterns
        r'__conda_setup=.*',  # conda init variable
        r'.*>>> conda initialize >>>.*',  # conda init markers
        r'.*<<< conda initialize <<<.*',
        r'eval "\$\(.*conda.*init.*\)"',  # eval conda init
        r'export PATH=.*conda.*/bin:',  # PATH modifications for conda
        r'export PATH=.*anaconda.*/bin:',  # PATH modifications for anaconda
        r'.*mamba.*init.*',  # mamba init patterns
        r'.*micromamba.*init.*',  # micromamba init patterns
        r'source.*activate.*base',  # Activating base environment
    ]
    return any(re.match(pattern, line, re.IGNORECASE) for pattern in conda_patterns)

def replace_username_with_user_var(line, username):
    """Replace hardcoded username with $USER, but not in filepaths"""
    # Skip if username not in line
    if username not in line:
        return line
    
    # Patterns where we should NOT replace (paths)
    path_patterns = [
        r'/home/{}'.format(username),
        r'/users/{}'.format(username),
        r'/share/.*/{}'.format(username),
        r'/quobyte/.*/{}'.format(username),
        r'~{}/'.format(username),
        r'{}@'.format(username),  # SSH format
        r'/{}/'.format(username),  # Any path component
    ]
    
    # Check if username appears in a path context
    for pattern in path_patterns:
        if re.search(pattern, line):
            return line
    
    # Common patterns where we SHOULD replace
    # Look for username in command arguments, environment variables, etc.
    replacement_patterns = [
        (r'(\s-u\s+){}(\s|$|")'.format(username), r'\1$USER\2'),  # -u username
        (r'(\s--user\s+){}(\s|$|")'.format(username), r'\1$USER\2'),  # --user username
        (r'(\s--user=){}(\s|$|")'.format(username), r'\1$USER\2'),  # --user=username
        (r'(USER=){}(\s|$|")'.format(username), r'\1$USER\2'),  # USER=username
        (r'(\$USER:-){}' .format(username), r'\1$USER'),  # ${USER:-username}
        (r'(\w+=["\']*){}'.format(username) + r'(["\']*)', r'\1$USER\2'),  # VAR=username or VAR="username"
    ]
    
    modified_line = line
    for pattern, replacement in replacement_patterns:
        modified_line = re.sub(pattern, replacement, modified_line)
    
    return modified_line

def process_bash_profile(source_path: Path, username: str, quobyte_dir: str, verbose: bool = False) -> (str, bool, bool):
    """Process bash_profile for migration to bashrc"""
    
    # Define all sandbox aliases
    sandbox_aliases = {
        'sandbox': "alias sandbox='srun -p high --cpus-per-task=8 --mem=16G --time=1-00:00:00 --pty bash'",
        'sandboxlow': "alias sandboxlow='srun -p low --cpus-per-task=16 --mem=32G --time=1-00:00:00 --pty bash'",
        'sandboxgpu': "alias sandboxgpu='srun -p high --gres=gpu:a6000:1 --cpus-per-task=8 --mem=16G --time=1-00:00:00 --pty bash'",
        'sandboxlowgpu': "alias sandboxlowgpu='srun -p low --gres=gpu:a6000:1 --cpus-per-task=8 --mem=16G --time=1-00:00:00 --pty bash'"
    }
    
    with open(source_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    module_comment_made = False
    conda_found = False
    existing_aliases = set()
    in_conda_block = False
    conda_modules_added = False
    existing_conda_module = False
    conda_env_vars_added = False

    for i, line in enumerate(lines):
        # Check for conda initialization block
        if '>>> conda initialize >>>' in line:
            in_conda_block = True
            if verbose:
                print(f"Found conda init block start at line {i+1}")
            conda_found = True
            continue  # Skip this line entirely
        elif '<<< conda initialize <<<' in line:
            in_conda_block = False
            if verbose:
                print(f"Found conda init block end at line {i+1}")
            continue  # Skip this line entirely
            
        # Skip lines within conda block
        if in_conda_block:
            continue  # Remove conda init lines entirely

        # Check for existing module load conda
        if re.match(r'^\s*module\s+load\s+conda', line):
            existing_conda_module = True
            if 'conda/latest' not in line:
                if verbose:
                    print(f"Updating module load conda to conda/latest at line {i+1}")
                line = re.sub(r'module\s+load\s+conda\S*', 'module load conda/latest', line)

        # Detect existing sandbox aliases
        for alias_name in sandbox_aliases:
            if re.match(rf'^\s*alias\s+{alias_name}=', line):
                existing_aliases.add(alias_name)

        # Replace hardcoded path
        if '/share/siegellab/' in line:
            if verbose:
                print(f"Replacing path at line {i+1}: /share/siegellab/ -> /quobyte/jbsiegelgrp/")
            line = line.replace('/share/siegellab/', '/quobyte/jbsiegelgrp/')
        
        # Replace hardcoded username with $USER (but not in paths)
        old_line = line
        line = replace_username_with_user_var(line, username)
        if old_line != line and verbose:
            print(f"Replaced username with $USER at line {i+1}")

        # Handle conda sourcing outside of conda blocks
        if detect_conda_setup(line) and not in_conda_block:
            if verbose:
                print(f"Removing conda setup line at line {i+1}: {line.strip()}")
            conda_found = True
            continue  # Skip conda setup lines entirely

        # Handle conda activate commands
        if re.match(r'^\s*conda\s+activate', line):
            if verbose:
                print(f"Removing conda activate at line {i+1}")
            continue  # Skip conda activate lines

        # Comment out module loads and insert guidance
        if re.match(r'^\s*module\s+load', line) and 'conda' not in line and 'cuda' not in line:
            module_name = line.strip().split('module load')[-1].strip()
            new_lines.append(f"# {line}")
            new_lines.append(f'echo "NOTE: Module \'{module_name}\' was loaded on the old cluster. '
                             f'Use \'module avail {module_name}\' on hive.hpc.ucdavis.edu to find it."\n')
            module_comment_made = True
        else:
            new_lines.append(line)

    # Add conda modules if conda was found but modules not added
    if (conda_found or existing_conda_module) and not existing_conda_module:
        if verbose:
            print("Adding conda and cuda modules")
        new_lines.insert(0, "# Loading conda and cuda modules\n")
        new_lines.insert(1, "module load conda/latest\n")
        new_lines.insert(2, "module load cuda/12.6.2\n")
        new_lines.insert(3, "\n")
    
    # Add conda environment variables
    if verbose:
        print(f"Adding conda environment variables for quobyte directory: {quobyte_dir}")
    new_lines.append("\n# Conda configuration for HIVE (limited home storage)\n")
    new_lines.append(f"export CONDA_PKGS_DIRS=/quobyte/jbsiegelgrp/{quobyte_dir}/.conda/pkgs\n")
    new_lines.append(f"export CONDA_ENVS_PATH=/quobyte/jbsiegelgrp/{quobyte_dir}/.conda/envs\n")
    new_lines.append("# Additional cache directories for Python packages\n")
    new_lines.append(f"export PIP_CACHE_DIR=/quobyte/jbsiegelgrp/{quobyte_dir}/.cache/pip\n")
    new_lines.append(f"export HF_HOME=/quobyte/jbsiegelgrp/{quobyte_dir}/.cache/huggingface\n")
    new_lines.append(f"export TORCH_HOME=/quobyte/jbsiegelgrp/{quobyte_dir}/.cache/torch\n")
    new_lines.append(f"export TRANSFORMERS_CACHE=/quobyte/jbsiegelgrp/{quobyte_dir}/.cache/transformers\n")

    # Add missing sandbox aliases
    missing_aliases = set(sandbox_aliases.keys()) - existing_aliases
    if missing_aliases:
        new_lines.append("\n# Interactive session aliases\n")
        for alias_name in sorted(missing_aliases):
            new_lines.append(sandbox_aliases[alias_name] + "\n")

    return ''.join(new_lines), module_comment_made, conda_found

def create_simple_bash_profile():
    """Create a simple .bash_profile that sources .bashrc"""
    return """# Source .bashrc if it exists
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
"""

def create_condarc(quobyte_dir: str):
    """Create a .condarc file with proper directory configuration"""
    return f"""channels:
  - conda-forge
  - bioconda
use_lockfiles: false
envs_dirs:
  - /quobyte/jbsiegelgrp/{quobyte_dir}/.conda/envs
  - /quobyte/jbsiegelgrp/software/envs
  - /cvmfs/hpc.ucdavis.edu/sw/conda/environments
pkgs_dirs:
  - /quobyte/jbsiegelgrp/{quobyte_dir}/.conda/pkgs
  - /cvmfs/hpc.ucdavis.edu/sw/conda/pkgs
# Prevent pip packages from installing to local site-packages
env_prompt: '({{name}}) '
"""

def scp_to_remote(temp_file: Path, remote_user: str, remote_host: str, remote_path: str):
    """Upload file to remote host"""
    subprocess.run(['scp', str(temp_file), f'{remote_user}@{remote_host}:{remote_path}'], check=True)

def check_cluster(verbose=False):
    """Check which cluster we're running on and prevent running on HIVE."""
    try:
        hostname = socket.gethostname().lower()
        
        # Check if we're on HIVE
        if 'hive' in hostname or hostname.endswith('.hpc.ucdavis.edu'):
            print("ERROR: This script should NOT be run on HIVE!")
            print("Please run this script from your old cluster (cacao or barbera):")
            print("  ssh username@cacao.genomecenter.ucdavis.edu")
            print("  ssh username@barbera.genomecenter.ucdavis.edu")
            print("\nThis script migrates FROM the old cluster TO HIVE.")
            return False
            
        # Check if we're on a known old cluster
        if any(cluster in hostname for cluster in ['cacao', 'barbera', 'genomecenter']):
            if verbose:
                print(f"Running on {hostname} - this is correct!")
            return True
            
        # Unknown cluster - warn but allow
        print(f"Warning: Running on unknown host '{hostname}'")
        print("This script should be run from cacao or barbera.")
        response = input("Continue anyway? (y/N): ")
        return response.lower() in ['y', 'yes']
        
    except Exception as e:
        print(f"Warning: Could not determine hostname: {e}")
        print("Proceeding with caution...")
        return True


def main():
    parser = argparse.ArgumentParser(description="Migrate bash_profile to bashrc for new HIVE cluster.")
    parser.add_argument("ssh_username", help="Username for SSH to hive.hpc.ucdavis.edu")
    parser.add_argument("quobyte_dir", help="Your directory name in /quobyte/jbsiegelgrp/ (e.g., 'marco')")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without uploading")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed processing information")
    args = parser.parse_args()

    # Check if we're running on the correct cluster
    if not check_cluster(args.verbose):
        return

    original_path = Path.home() / '.bash_profile'
    if not original_path.exists():
        print(f"Error: {original_path} does not exist.")
        return

    print("Processing .bash_profile for migration to .bashrc...")
    new_bashrc_contents, module_comment_made, conda_found = process_bash_profile(
        original_path, args.ssh_username, args.quobyte_dir, args.verbose
    )

    if args.dry_run:
        print("\n=== DRY RUN MODE ===")
        print("\nNew .bashrc contents would be:")
        print("-" * 50)
        print(new_bashrc_contents[:1000] + "..." if len(new_bashrc_contents) > 1000 else new_bashrc_contents)
        print("-" * 50)
        print("\nNew .bash_profile would contain:")
        print("-" * 50)
        print(create_simple_bash_profile())
        print("-" * 50)
        print("\nNew .condarc would contain:")
        print("-" * 50)
        print(create_condarc(args.quobyte_dir))
        print("-" * 50)
        return

    # Create temporary files for all config files
    bashrc_tmp = None
    bash_profile_tmp = None
    condarc_tmp = None
    
    try:
        # Create temporary .bashrc
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, prefix='bashrc_hive_', dir='/tmp', encoding='utf-8') as tmp:
            tmp.write(new_bashrc_contents)
            bashrc_tmp = Path(tmp.name)

        # Create temporary .bash_profile
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, prefix='bash_profile_hive_', dir='/tmp', encoding='utf-8') as tmp:
            tmp.write(create_simple_bash_profile())
            bash_profile_tmp = Path(tmp.name)

        # Create temporary .condarc
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, prefix='condarc_hive_', dir='/tmp', encoding='utf-8') as tmp:
            tmp.write(create_condarc(args.quobyte_dir))
            condarc_tmp = Path(tmp.name)

        # Create backup on remote
        print("Creating backup of existing files on remote...")
        subprocess.run(['ssh', f'{args.ssh_username}@hive.hpc.ucdavis.edu', 
                       'cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true; '
                       'cp ~/.bash_profile ~/.bash_profile.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true; '
                       'cp ~/.condarc ~/.condarc.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true'])

        # Create necessary directories on remote
        print("Creating conda and cache directories on remote...")
        conda_dirs_cmd = (
            f'mkdir -p /quobyte/jbsiegelgrp/{args.quobyte_dir}/.conda/pkgs '
            f'/quobyte/jbsiegelgrp/{args.quobyte_dir}/.conda/envs '
            f'/quobyte/jbsiegelgrp/{args.quobyte_dir}/.cache/pip '
            f'/quobyte/jbsiegelgrp/{args.quobyte_dir}/.cache/huggingface '
            f'/quobyte/jbsiegelgrp/{args.quobyte_dir}/.cache/torch '
            f'/quobyte/jbsiegelgrp/{args.quobyte_dir}/.cache/transformers'
        )
        subprocess.run(['ssh', f'{args.ssh_username}@hive.hpc.ucdavis.edu', conda_dirs_cmd], check=True)

        # Upload all files
        print("Uploading modified .bashrc...")
        scp_to_remote(bashrc_tmp, args.ssh_username, 'hive.hpc.ucdavis.edu', '~/.bashrc')
        
        print("Uploading new .bash_profile...")
        scp_to_remote(bash_profile_tmp, args.ssh_username, 'hive.hpc.ucdavis.edu', '~/.bash_profile')
        
        print("Uploading .condarc...")
        scp_to_remote(condarc_tmp, args.ssh_username, 'hive.hpc.ucdavis.edu', '~/.condarc')
        
        print("Upload successful.")
        
    except subprocess.CalledProcessError as e:
        print(f"Upload failed: {e}")
        print("Please check your SSH access or network connection.")
        return
    finally:
        # Clean up temporary files
        if bashrc_tmp and bashrc_tmp.exists():
            bashrc_tmp.unlink()
        if bash_profile_tmp and bash_profile_tmp.exists():
            bash_profile_tmp.unlink()
        if condarc_tmp and condarc_tmp.exists():
            condarc_tmp.unlink()

    # Print summary
    print("\n=== Migration Summary ===")
    if conda_found:
        print("[✓] Conda/Miniconda setup was found and removed, replaced with cluster modules")
        print("  - Added: module load conda/latest")
        print("  - Added: module load cuda/12.6.2")
    
    if module_comment_made:
        print("[✓] Some 'module load' commands were commented out")
        print("  Use 'module avail <module_name>' on hive to find replacements")
    
    print("[✓] Added conda configuration for limited home storage:")
    print(f"  - Conda packages: /quobyte/jbsiegelgrp/{args.quobyte_dir}/.conda/pkgs")
    print(f"  - Conda environments: /quobyte/jbsiegelgrp/{args.quobyte_dir}/.conda/envs")
    print(f"  - Pip cache: /quobyte/jbsiegelgrp/{args.quobyte_dir}/.cache/pip")
    print("  - Created .condarc to prevent pip conflicts")
    
    print("\n[✓] Added interactive session aliases:")
    print("  - sandbox: 8 CPU, 16GB RAM, 1 day, high partition")
    print("  - sandboxlow: 16 CPU, 32GB RAM, 1 day, low partition")
    print("  - sandboxgpu: 8 CPU, 16GB RAM, 1 GPU (A6000), 1 day, high partition")
    print("  - sandboxlowgpu: 8 CPU, 16GB RAM, 1 GPU (A6000), 1 day, low partition")
    
    print("\n[✓] Created simple .bash_profile that sources .bashrc")
    print("[✓] Replaced /share/siegellab/ paths with /quobyte/jbsiegelgrp/")
    print("[✓] Replaced hardcoded usernames with $USER variable (except in filepaths)")
    
    print("\nNext steps:")
    print("1. Log into hive.hpc.ucdavis.edu")
    print("2. Run: source ~/.bashrc")
    print("3. Review any commented module loads and update as needed")
    print("4. Your conda environments will now be stored in your quobyte directory")

if __name__ == "__main__":
    main()