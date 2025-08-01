# Path Migrator - Comprehensive Software Path Migration

## ⚠️ WARNING: RECURSIVE DIRECTORY PROCESSING

**This script processes ALL files in the specified directory AND ALL SUBDIRECTORIES!**

- **ALWAYS run from YOUR directory**, not shared locations
- **DO NOT run from parent directories** like `/home/` or `/share/`
- **ALWAYS use --dry-run first** to preview changes

## Overview
The `pathMigrator.py` script is a comprehensive tool that updates ALL software paths in your scripts for the HIVE cluster transition. It combines the path migration functionality from all the individual fix scripts into one powerful tool.

## What It Does

The script automatically detects and updates paths for:

1. **ColabFold**
   - `/toolbox/LocalColabFold` → `/quobyte/jbsiegelgrp/software/LocalColabFold`

2. **LigandMPNN** (case-insensitive)
   - `/toolbox/ligandMPNN` → `/quobyte/jbsiegelgrp/ligandMPNN`
   - `/toolbox/LigandMPNN` → `/quobyte/jbsiegelgrp/LigandMPNN`

3. **RFdiffusion** (from various locations)
   - `/home/*/RFdiffusion` → `/quobyte/jbsiegelgrp/software/RFdiffusion`
   - `/toolbox/RFdiffusion` → `/quobyte/jbsiegelgrp/software/RFdiffusion`
   - `~/RFdiffusion` → `/quobyte/jbsiegelgrp/software/RFdiffusion`
   - And many other common locations

4. **RFdiffusion Conda Environments**
   - Detects environments with names containing: `se3`, `rfdiff`, `rf-diff`, `diffusion`
   - Updates to: `/quobyte/jbsiegelgrp/software/envs/SE3nv`

5. **Rosetta**
   - Path: `/share/siegellab/software/kschu/Rosetta/main` → `/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main`
   - Binaries: `.default.linuxgccrelease` → `.static.linuxgccrelease`

6. **General Paths**
   - `/share/siegellab/` → `/quobyte/jbsiegelgrp/`

## Usage

### Basic Usage
```bash
python pathMigrator.py
```
This processes all files in the current directory and subdirectories.

### Process Specific Directory
```bash
python pathMigrator.py /path/to/scripts
```

### Preview Mode (Dry Run)
```bash
python pathMigrator.py --dry-run
```
Shows what would be changed without modifying any files.

### Verbose Mode
```bash
python pathMigrator.py -v
```
Shows detailed line-by-line changes.

### Combine Options
```bash
python pathMigrator.py /my/scripts --dry-run -v
```

## Example Output

### Normal Mode
```
HIVE Path Migration Tool
==================================================
Processing directory: /home/user/scripts

Modified: /home/user/scripts/colabfold_job.sh
  • ColabFold: /toolbox/LocalColabFold → /quobyte/jbsiegelgrp/software/LocalColabFold
  • General paths: /share/siegellab/ → /quobyte/jbsiegelgrp/ (3 occurrences)

Modified: /home/user/scripts/rosetta_design.sh
  • Rosetta: /share/siegellab/software/kschu/Rosetta/main → /quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main
  • Rosetta binary: rosetta_scripts.default.linuxgccrelease → rosetta_scripts.static.linuxgccrelease

==================================================
Summary:
  Files checked: 15
  Files modified: 2

IMPORTANT: Please review the changes and test your scripts!
```

### Dry Run Mode
```
[DRY RUN] Would modify: /home/user/scripts/rfdiffusion.sh
  • RFdiffusion: ~/RFdiffusion → /quobyte/jbsiegelgrp/software/RFdiffusion
  • RFdiffusion env: SE3nv → /quobyte/jbsiegelgrp/software/envs/SE3nv
```

### Verbose Mode
```
[DRY RUN] Would modify: script.sh
  • ColabFold: /toolbox/LocalColabFold → /quobyte/jbsiegelgrp/software/LocalColabFold
  Line 5:
    - export PATH=/toolbox/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH
    + export PATH=/quobyte/jbsiegelgrp/software/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH
```

## How It Works

1. **File Detection**: Automatically detects text files including:
   - Shell scripts (`.sh`, `.bash`)
   - SLURM scripts (`.sbatch`, `.slurm`)
   - Python scripts (`.py`)
   - Configuration files
   - Files without extensions

2. **Smart Replacement**: 
   - Applies software-specific fixes first (ColabFold, Rosetta, etc.)
   - Then applies general path migration
   - Preserves all other content exactly as-is

3. **Safety Features**:
   - Skips binary files
   - Handles encoding properly
   - Reports errors without stopping

## Important Notes

### What It Changes
- **Only software paths** - no SLURM configurations
- **Only text files** - binary files are skipped
- **Preserves structure** - only paths are changed

### What It Doesn't Change
- SLURM partition settings
- Account flags
- Time limits
- Any other job parameters

### Order of Operations
The script applies changes in this specific order:
1. ColabFold paths
2. LigandMPNN paths
3. RFdiffusion paths
4. RFdiffusion conda environments
5. Rosetta paths and binaries
6. General `/share/siegellab/` paths

This ensures specific software paths are handled correctly before general replacements.

## Best Practices

1. **VERIFY YOUR LOCATION FIRST**:
   ```bash
   pwd  # Make sure you're in YOUR directory!
   ls   # Check you're not in a shared location!
   ```

2. **Always use dry run first**:
   ```bash
   python pathMigrator.py . --dry-run
   ```

3. **Be specific with paths**:
   ```bash
   # GOOD - specific directory
   python pathMigrator.py ./my_scripts --dry-run
   
   # BAD - too broad!
   python pathMigrator.py /home --dry-run
   ```

4. **Review verbose output for critical scripts**:
   ```bash
   python pathMigrator.py important_script.sh --dry-run -v
   ```

5. **Back up your scripts**:
   ```bash
   cp -r scripts/ scripts_backup/
   ```

6. **Test after migration**:
   - Submit a test job
   - Verify paths exist on HIVE
   - Check output logs

## Comparison with Individual Scripts

This tool combines the path-fixing functionality of:
- `colab_fix.py` (ColabFold paths)
- `ligandmpnn_fix.py` (LigandMPNN paths)
- `rfdiffusion_fix.py` (RFdiffusion paths and environments)
- `rosetta_fix.py` (Rosetta paths and binaries)

**Key difference**: This script does NOT modify SLURM settings. Use the individual scripts if you need SLURM configuration updates.

## Troubleshooting

### "No files modified"
- Check if you're in the right directory
- Verify files contain old paths
- Try verbose mode to see what's being checked

### Encoding Errors
- The script handles UTF-8 encoding
- Binary files are automatically skipped
- Report issues with `broken.py` if needed

### Missing Paths
- The script covers common patterns
- Unusual installations might need manual updates
- Check verbose output to see what's detected

## When to Use This vs Individual Scripts

**Use pathMigrator.py when**:
- You have many scripts to update
- You only need path changes
- You want to process entire directories

**Use individual scripts when**:
- You need SLURM configuration updates
- You want software-specific handling only
- You're updating one script at a time