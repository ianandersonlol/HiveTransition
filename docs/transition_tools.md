# Cluster Transition Tools

**NOTE**: These tools help migrate from the old Cacao/Barbera HPC cluster to the new HIVE cluster. All tools are archived in the `transition_tools_old/` directory.

## Overview

The transition tools automate the process of updating job scripts and shell configurations when migrating from the old cluster to HIVE. They handle path updates, SLURM configuration changes, and environment setup.

## Recommended Tool

### migrate.py - Unified Migration Script (NEW)

**RECOMMENDED**: This new unified script consolidates all migration functionality into a single tool.

Handles everything in one command:
- All software path updates (ColabFold, LigandMPNN, RFdiffusion, Rosetta)
- All SLURM configuration changes (partitions, accounts, requeue flags)
- Time limit adjustments for partition constraints
- General path migration from /share/siegellab/ to /quobyte/jbsiegelgrp/
- Directory or single file processing
- Dry-run mode for previewing changes
- In-place or _fixed file creation

**Replaces**: `colab_fix.py`, `ligandmpnn_fix.py`, `rfdiffusion_fix.py`, `rosetta_fix.py`

**[Full Documentation](migrate.md)**

**Quick Examples:**
```bash
# Fix a single script
python migrate.py script.sh

# Fix all scripts in a directory
python migrate.py /path/to/scripts/

# Preview changes first
python migrate.py script.sh --dry-run

# Use high partition for long Rosetta jobs
python migrate.py rosetta_job.sh --high
```

## Legacy Tools

The following individual tools are still available but **migrate.py is recommended** for most use cases:

### 1. pathMigrator.py - Comprehensive Path Migration

Updates ALL software paths in a directory:
- Combines path fixes from all other scripts
- Does NOT modify SLURM settings
- Can process entire directories at once
- Includes all software: ColabFold, LigandMPNN, RFdiffusion, Rosetta

**[Full Documentation](pathMigrator.md)**

### 2. bash_profile_migration.py - Shell Configuration Migration

Migrates your shell configuration to HIVE:
- Converts `.bash_profile` to `.bashrc`
- Sets up conda in quobyte directory
- Adds interactive session aliases
- Updates paths and modules

**[Full Documentation](bash_profile_migration.md)**

### 3. colab_fix.py - ColabFold Script Updates

Updates ColabFold scripts:
- Fixes ColabFold installation path
- Updates GPU partition settings
- Migrates storage paths

**[Full Documentation](colab_fix.md)**

### 4. ligandmpnn_fix.py - LigandMPNN Script Updates

Updates LigandMPNN scripts:
- Fixes LigandMPNN installation path
- Updates GPU partition settings
- Migrates storage paths

**[Full Documentation](ligandmpnn_fix.md)**

### 5. rfdiffusion_fix.py - RFdiffusion Script Updates

Updates RFdiffusion scripts:
- Standardizes RFdiffusion installation path
- Updates conda environment to shared SE3nv
- Updates GPU partition settings

**[Full Documentation](rfdiffusion_fix.md)**

### 6. rosetta_fix.py - Rosetta Script Updates

Updates Rosetta scripts:
- Migrates to Rosetta 3.14
- Changes binary names (`.default.` → `.static.`)
- Handles CPU partition selection
- Enforces time limits

**[Full Documentation](rosetta_fix.md)**

### 7. broken.py - Issue Reporting

Reports issues with scripts:
- Generates GitHub issue URL
- Pre-fills script content
- Auto-assigns to maintainer

**[Full Documentation](broken.md)**

## Usage

All tools are located in the `transition_tools_old/` directory:

```bash
# Clone the repository
git clone https://github.com/ianandersonlol/HiveTransition.git
cd HiveTransition/transition_tools_old

# Use individual tools
python bash_profile_migration.py <username> <quobyte_dir>
python colab_fix.py /path/to/script.sh
python ligandmpnn_fix.py /path/to/script.sh
python rfdiffusion_fix.py /path/to/script.sh
python rosetta_fix.py /path/to/script.sh
python pathMigrator.py /path/to/scripts/directory
```

## When to Use These Tools

These tools are primarily useful if you:
- Are migrating from Cacao/Barbera to HIVE for the first time
- Have old job scripts that need updating
- Need to convert your shell configuration

For new users starting on HIVE, refer to the [Example Scripts](../README.md#example-scripts) section instead, which provides up-to-date templates for common tasks.
