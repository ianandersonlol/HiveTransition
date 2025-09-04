[View Script: bash_profile_migration.py](../bash_profile_migration.py)

# Bash Profile Migration Script

## Overview
The `bash_profile_migration.py` script automates the migration of your shell configuration from the old HPC cluster to the new HIVE cluster. It handles the transition from `.bash_profile` to `.bashrc`, updates paths, manages conda environments, and sets up proper storage locations.

## What It Does

### 1. Shell Configuration Migration
- Converts `.bash_profile` to `.bashrc` (HIVE's preferred configuration)
- Creates a minimal `.bash_profile` that sources `.bashrc`

### 2. Conda/Anaconda Handling
- **Removes** conda initialization blocks (they're unnecessary with cluster modules)
- Replaces local conda installations with `module load conda/latest`
- Adds `module load cuda/12.6.2` for GPU support
- Detects various conda setups: miniconda, anaconda, mamba, micromamba

### 3. Path Updates
- Updates old paths: `/share/siegellab/` → `/quobyte/jbsiegelgrp/`
- Replaces hardcoded usernames with `$USER` variable (except in file paths)

### 4. Storage Management
- Sets up conda directories in quobyte (home directories only have 1GB!)
- Configures environment variables:
  - `CONDA_PKGS_DIRS`: Package cache location
  - `CONDA_ENVS_PATH`: Environment storage
  - `PIP_CACHE_DIR`: Pip package cache
  - `HF_HOME`: HuggingFace cache
  - `TORCH_HOME`: PyTorch cache
  - `TRANSFORMERS_CACHE`: Transformers cache

### 5. Interactive Session Aliases
Adds convenient aliases for requesting compute resources:
- `sandbox`: 8 CPU, 16GB RAM, 1 day, high partition
- `sandboxlow`: 16 CPU, 32GB RAM, 1 day, low partition  
- `sandboxgpu`: 8 CPU, 16GB RAM, 1 GPU (A6000), 1 day, high partition
- `sandboxlowgpu`: 8 CPU, 16GB RAM, 1 GPU (A6000), 1 day, low partition

### 6. Creates .condarc File
Prevents pip install conflicts and ensures proper package management:
```yaml
channels:
  - conda-forge
  - bioconda
use_lockfiles: false
envs_dirs:
  - /quobyte/jbsiegelgrp/{your_dir}/.conda/envs
  - /quobyte/jbsiegelgrp/software/envs
  - /cvmfs/hpc.ucdavis.edu/sw/conda/environments
pkgs_dirs:
  - /quobyte/jbsiegelgrp/{your_dir}/.conda/pkgs
  - /cvmfs/hpc.ucdavis.edu/sw/conda/pkgs
```

## Usage

### Basic Usage
```bash
python bash_profile_migration.py <ssh_username> <quobyte_dir>
```

### Arguments
- `ssh_username`: Your username for SSH to hive.hpc.ucdavis.edu
- `quobyte_dir`: Your directory name in `/quobyte/jbsiegelgrp/` (e.g., 'marco', 'john')

### Options
- `--dry-run`: Preview changes without uploading
- `--verbose` or `-v`: Show detailed processing information

### Examples

1. **Basic migration:**
   ```bash
   python bash_profile_migration.py jdoe john
   ```

2. **Preview changes first:**
   ```bash
   python bash_profile_migration.py jdoe john --dry-run
   ```

3. **Verbose output for debugging:**
   ```bash
   python bash_profile_migration.py jdoe john --verbose
   ```

## What Happens During Migration

1. **Reads** your local `~/.bash_profile`
2. **Processes** the content:
   - Removes conda init blocks
   - Updates paths and usernames
   - Adds environment variables
   - Comments out old module loads
3. **Creates** three temporary files:
   - New `.bashrc` with migrated content
   - New `.bash_profile` that sources `.bashrc`
   - New `.condarc` for conda configuration
4. **Backs up** existing files on HIVE (with timestamps)
5. **Creates** necessary directories on HIVE
6. **Uploads** all files via SCP

## After Migration

1. Log into HIVE:
   ```bash
   ssh username@hive.hpc.ucdavis.edu
   ```

2. Source your new configuration:
   ```bash
   source ~/.bashrc
   ```

3. Verify conda works:
   ```bash
   conda info
   ```

4. Create/activate environments in your quobyte directory:
   ```bash
   conda create -n myenv python=3.9
   conda activate myenv
   ```

## Troubleshooting

### SSH Connection Failed
- Verify you can SSH to HIVE: `ssh username@hive.hpc.ucdavis.edu`
- Check your network connection
- Ensure you're using the correct username

### Module Not Found
- Old modules might have different names on HIVE
- Use `module avail <module_name>` to search for replacements
- The script will provide hints for this

### Conda Environment Issues
- Environments are now stored in `/quobyte/jbsiegelgrp/{your_dir}/.conda/envs`
- Old environments need to be recreated on HIVE
- Use `conda env list` to see available environments

### Storage Issues
- Home directory is limited to 1GB
- Everything should go in your quobyte directory
- Check disk usage: `du -sh ~`

## Important Notes

1. **Backup**: The script creates backups, but you should keep your own copy of `.bash_profile`
2. **Manual Review**: Check the migrated files for any custom configurations
3. **Module Updates**: Some module names may have changed - check with `module avail`
4. **Conda Environments**: You'll need to recreate environments on the new cluster