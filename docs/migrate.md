# migrate.py - Unified Migration Script

**Location:** `transition_tools_old/migrate.py`

## Overview

The unified migration script consolidates all cluster transition functionality into a single, comprehensive tool. It replaces the individual fix scripts (`colab_fix.py`, `ligandmpnn_fix.py`, `rfdiffusion_fix.py`, `rosetta_fix.py`) while adding enhanced features.

## What It Does

This script handles all aspects of migrating SLURM job scripts from Cacao to HIVE:

### Path Migrations
- **ColabFold**: `/toolbox/LocalColabFold` → `/quobyte/jbsiegelgrp/software/LocalColabFold`
- **LigandMPNN**: `/toolbox/ligandMPNN` → `/quobyte/jbsiegelgrp/ligandMPNN`
- **RFdiffusion**: Various paths → `/quobyte/jbsiegelgrp/software/RFdiffusion`
- **RFdiffusion environments**: Various conda envs → `/quobyte/jbsiegelgrp/software/envs/SE3nv`
- **Rosetta**: Old paths → `/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main`
- **Rosetta binaries**: `.default.linuxgccrelease` → `.static.linuxgccrelease`
- **General paths**: `/share/siegellab/` → `/quobyte/jbsiegelgrp/`

### SLURM Configuration Updates
- **GPU partitions**: `jbsiegel-gpu` → `gpu-a100`
- **GPU accounts**: Adds `--account=genome-center-grp` for GPU jobs
- **CPU partitions**: `production` → `low` (default) or `high` (with `--high` flag)
- **Requeue flags**: Adds `--requeue` for low partition jobs
- **Time limits**: Enforces 3-day max for low partition (adjusts longer times)

## Usage

### Basic Usage

```bash
# Fix a single file (creates script_fixed.sh)
python migrate.py script.sh

# Fix all files in a directory recursively
python migrate.py /path/to/scripts/

# Fix files in current directory
python migrate.py .
```

### Advanced Options

```bash
# Use high partition for long jobs (30 day max)
python migrate.py script.sh --high

# Modify files in place (no _fixed versions)
python migrate.py script.sh --in-place

# Preview changes without modifying files
python migrate.py . --dry-run

# Verbose output showing line-by-line changes
python migrate.py . --dry-run -v
```

## Options

| Option | Description |
|--------|-------------|
| `path` | File or directory to process (default: current directory) |
| `--high` | Use high partition instead of low (for Rosetta jobs > 3 days) |
| `--dry-run` | Preview changes without modifying files |
| `--in-place` | Modify files directly instead of creating `_fixed` versions |
| `-v, --verbose` | Show detailed line-by-line changes |

## Examples

### Example 1: Fix a ColabFold Script

```bash
$ python migrate.py colabfold_job.sh

======================================================================
HIVE Cluster Migration Tool
======================================================================

Target: /path/to/colabfold_job.sh
Mode: Using LOW partition (3 day max, auto-requeue)
Mode: Creating *_fixed versions of modified files

Modified: /path/to/colabfold_job.sh
  • ColabFold PATH: /toolbox/LocalColabFold/... → /quobyte/jbsiegelgrp/software/LocalColabFold/...
  • GPU partition: jbsiegel-gpu → gpu-a100
  • Added GPU account: genome-center-grp
  • General paths: /share/siegellab/ → /quobyte/jbsiegelgrp/ (2 occurrence(s))
  → Output: /path/to/colabfold_job_fixed.sh

======================================================================
Summary:
  Files checked: 1
  Files modified: 1

IMPORTANT: Review the changes and test your scripts!
```

### Example 2: Fix Rosetta Scripts for Long Jobs

```bash
$ python migrate.py rosetta_scripts/ --high

======================================================================
HIVE Cluster Migration Tool
======================================================================

Target: /path/to/rosetta_scripts
Mode: Using HIGH partition (30 day max)
Mode: Creating *_fixed versions of modified files

⚠️  WARNING: This will process ALL files in:
   /path/to/rosetta_scripts
   and ALL subdirectories beneath it!

Continue? (y/N): y

Modified: /path/to/rosetta_scripts/relax.sh
  • Rosetta base: /share/siegellab/software/.../Rosetta/main → /quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main
  • Rosetta binaries: .default → .static (3 occurrence(s))
  • CPU partition: production → high
  • General paths: /share/siegellab/ → /quobyte/jbsiegelgrp/ (5 occurrence(s))
  → Output: /path/to/rosetta_scripts/relax_fixed.sh

======================================================================
Summary:
  Files checked: 4
  Files modified: 1

IMPORTANT: Review the changes and test your scripts!
```

### Example 3: Preview Changes

```bash
$ python migrate.py rfdiffusion.sh --dry-run -v

======================================================================
HIVE Cluster Migration Tool
======================================================================

Target: /path/to/rfdiffusion.sh
Mode: Using LOW partition (3 day max, auto-requeue)
*** DRY RUN MODE - No files will be modified ***
Mode: Creating *_fixed versions of modified files

[DRY RUN] Would modify: /path/to/rfdiffusion.sh
  • RFdiffusion: /home/user/RFdiffusion → /quobyte/jbsiegelgrp/software/RFdiffusion
  • RFdiffusion conda env: SE3nv → /quobyte/jbsiegelgrp/software/envs/SE3nv
  • GPU partition: jbsiegel-gpu → gpu-a100
  • Added GPU account: genome-center-grp
  Line 15:
    - conda activate SE3nv
    + conda activate /quobyte/jbsiegelgrp/software/envs/SE3nv
  Line 23:
    - #SBATCH --partition=jbsiegel-gpu
    + #SBATCH --partition=gpu-a100 --account=genome-center-grp
  Output would be: /path/to/rfdiffusion_fixed.sh

======================================================================
Summary:
  Files checked: 1
  Files that would be modified: 1

Re-run without --dry-run to apply changes
```

### Example 4: In-Place Modification

```bash
$ python migrate.py script.sh --in-place

======================================================================
HIVE Cluster Migration Tool
======================================================================

Target: /path/to/script.sh
Mode: Using LOW partition (3 day max, auto-requeue)
*** IN-PLACE MODE - Files will be modified directly ***

Modified: /path/to/script.sh
  • General paths: /share/siegellab/ → /quobyte/jbsiegelgrp/ (3 occurrence(s))
  • CPU partition: production → low
  • Added --requeue flag for low partition

======================================================================
Summary:
  Files checked: 1
  Files modified: 1

IMPORTANT: Review the changes and test your scripts!
```

## When to Use --high Flag

Use the `--high` flag for Rosetta jobs that require more than 3 days:

```bash
# Low partition (default): 3 day max, can be preempted
python migrate.py rosetta_relax.sh

# High partition: 30 day max, uses jbsiegelgrp account
python migrate.py rosetta_relax.sh --high
```

The script will automatically:
- Set partition to `high` instead of `low`
- NOT add `--requeue` flag (high partition jobs don't need it)
- NOT adjust time limits (high partition allows up to 30 days)

## What Gets Changed

### GPU Jobs (ColabFold, LigandMPNN, RFdiffusion)

**Before:**
```bash
#!/bin/bash
#SBATCH --partition=jbsiegel-gpu
#SBATCH --gres=gpu:1

export PATH="/toolbox/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH"
```

**After:**
```bash
#!/bin/bash
#SBATCH --partition=gpu-a100 --account=genome-center-grp
#SBATCH --gres=gpu:1

export PATH="/quobyte/jbsiegelgrp/software/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH"
```

### CPU Jobs (Rosetta) - Default

**Before:**
```bash
#!/bin/bash
#SBATCH --partition=production
#SBATCH --time=7-00:00:00

/share/siegellab/software/.../Rosetta/main/source/bin/relax.default.linuxgccrelease
```

**After:**
```bash
#!/bin/bash
#SBATCH --partition=low
#SBATCH --requeue
#SBATCH --time=3-00:00:00

/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/source/bin/relax.static.linuxgccrelease
```

### CPU Jobs (Rosetta) - With --high Flag

**Before:**
```bash
#!/bin/bash
#SBATCH --partition=production
#SBATCH --time=7-00:00:00
```

**After:**
```bash
#!/bin/bash
#SBATCH --partition=high
#SBATCH --time=7-00:00:00
```

## Safety Features

1. **Dry-run mode**: Preview changes before applying them
2. **Confirmation prompt**: Asks for confirmation when processing directories
3. **Separate output files**: Creates `_fixed` versions by default (use `--in-place` to override)
4. **Verbose mode**: Shows line-by-line changes for verification
5. **Text file detection**: Only processes text files, skips binaries

## Advantages Over Individual Scripts

1. **Single command**: No need to remember which fix script to use
2. **Comprehensive**: Applies all fixes in one pass
3. **Consistent**: Same logic for all file types
4. **Better options**: Dry-run, in-place, verbose modes
5. **Smarter detection**: Automatically detects which fixes are needed
6. **Directory support**: Process entire directories recursively
7. **Less code duplication**: ~70% less duplicate code

## Comparison with Old Scripts

| Old Script | What migrate.py Does Instead |
|------------|------------------------------|
| `colab_fix.py` | Automatically detects and fixes ColabFold paths + SLURM |
| `ligandmpnn_fix.py` | Automatically detects and fixes LigandMPNN paths + SLURM |
| `rfdiffusion_fix.py` | Automatically detects and fixes RFdiffusion paths + conda envs + SLURM |
| `rosetta_fix.py` | Automatically detects and fixes Rosetta paths + binaries + SLURM |
| `path_migrator.py` | All path fixes PLUS SLURM configurations |

## Troubleshooting

### No Changes Made

If the script reports "No changes were needed", it means your script is already using HIVE paths and configurations.

### File Not Detected

If you have a script file that's not being processed, check:
1. Is it a text file? (not a binary)
2. Does it have a recognized extension (`.sh`, `.py`, `.sbatch`, etc.)?
3. Try running with `-v` to see what's being checked

### Wrong Output Path

By default, creates `_fixed` versions. Use `--in-place` to modify files directly.

### Time Limit Changed Unexpectedly

The low partition has a 3-day maximum. If your job needs more time:
1. Use `--high` flag, or
2. Manually edit the `_fixed` script and change partition to `high`

## See Also

- [Transition Tools Overview](transition_tools.md)
- [Partition Documentation](partitions.md)
- [HIVE vs Cacao Comparison](../README.md#hive-vs-cacao-comparison)
