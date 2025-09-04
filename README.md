# HIVE Cluster Migration Tools

This repository contains scripts to help migrate from the old HPC cluster to the new HIVE cluster.

## Table of Contents

- [HIVE vs Cacao Comparison](#hive-vs-cacao-comparison)
  - [Key Differences Between Clusters](#key-differences-between-clusters)
  - [Software Locations](#software-locations)
  - [Storage Management](#storage-management)
  - [SLURM Changes](#slurm-changes)
  - [Interactive Sessions](#interactive-sessions)
- [Quick Start](#quick-start)
- [Available Scripts](#available-scripts)
- [Common Migration Tasks](#common-migration-tasks)
  - [Setting Up Your Environment](#setting-up-your-environment)
  - [Migrating Job Scripts](#migrating-job-scripts)
  - [Interactive Sessions](#interactive-sessions-1)
- [Important Notes](#important-notes)
- [Troubleshooting](#troubleshooting)
- [File Structure](#file-structure)
- [Example Scripts](#Example-scripts)
   - [Colabfold](#colabfold)
   - [Chai](#run_chai.py)
   - [Chai with MSA](#chai_with_msa.py)

## HIVE vs Cacao Comparison

### Key Differences Between Clusters

| Component | Cacao (Old Cluster) | HIVE (New Cluster) |
|-----------|-------------------|-------------------|
| **Storage Path** | `/share/siegellab/` | `/quobyte/jbsiegelgrp/` |
| **Home Directory Size** | 1GB limit | 20GB limit |
| **Shell Config** | `.bash_profile` | `.bashrc` (with minimal `.bash_profile`) |
| **Conda/Python** | Local installations (~/miniconda3, etc.) | `module load conda/latest` |
| **CUDA** | Various local installations | `module load cuda/12.6.2` |
| **GPU Partition** | `jbsiegel-gpu` | `gpu-a100` |
| **GPU Account** | Not required | `--account=genome-center-grp` required |
| **CPU Partitions** | `production` | `low` (3 day max) or `high` (30 day max) |
| **Job Requeue** | Not standard | `--requeue` flag for low partition |

### Software Locations

| Software | Cacao Path | HIVE Path |
|----------|-----------|-----------|
| **ColabFold** | `/toolbox/LocalColabFold/` | `/quobyte/jbsiegelgrp/software/LocalColabFold/` |
| **LigandMPNN** | `/toolbox/ligandMPNN/` | `/quobyte/jbsiegelgrp/ligandMPNN/` |
| **RFdiffusion** | Various (~/RFdiffusion, /toolbox/RFdiffusion, etc.) | `/quobyte/jbsiegelgrp/software/RFdiffusion/` |
| **RFdiff Conda Env** | Various (SE3nv, rfdiffusion, etc.) | `/quobyte/jbsiegelgrp/software/envs/SE3nv` |
| **Rosetta** | `/share/siegellab/software/kschu/Rosetta/main/` | `/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/` |
| **Rosetta Version** | Older version | Rosetta 3.14 |
| **Rosetta Binaries** | `.default.linuxgccrelease` | `.static.linuxgccrelease` |

### Storage Management

| Storage Type | Cacao | HIVE |
|-------------|-------|------|
| **Conda Packages** | `~/.conda/pkgs` | `/quobyte/jbsiegelgrp/{user}/.conda/pkgs` |
| **Conda Environments** | `~/.conda/envs` or local | `/quobyte/jbsiegelgrp/{user}/.conda/envs` |
| **Pip Cache** | `~/.cache/pip` | `/quobyte/jbsiegelgrp/{user}/.cache/pip` |
| **HuggingFace Cache** | `~/.cache/huggingface` | `/quobyte/jbsiegelgrp/{user}/.cache/huggingface` |
| **PyTorch Cache** | `~/.cache/torch` | `/quobyte/jbsiegelgrp/{user}/.cache/torch` |
| **Transformers Cache** | `~/.cache/transformers` | `/quobyte/jbsiegelgrp/{user}/.cache/transformers` |

### SLURM Changes

| Parameter | Cacao | HIVE |
|-----------|-------|------|
| **GPU Jobs** | `#SBATCH -p jbsiegel-gpu` | `#SBATCH -p gpu-a100`<br>`#SBATCH --account=genome-center-grp` |
| **CPU Jobs** | `#SBATCH -p production` | `#SBATCH -p low` (default) or<br>`#SBATCH -p high` (long jobs) |
| **Low Priority** | N/A | `#SBATCH --requeue` (auto-requeue if preempted) |
| **Time Limits** | 30 days max | `low`: 3 days max<br>`high`: 30 days max |

### Interactive Sessions

The `bash_profile_migration.py` script adds these convenient aliases for requesting interactive sessions:

| Command | Resources | Partition |
|---------|-----------|-----------|
| `sandbox` | 8 CPU, 16GB RAM, 1 day | high |
| `sandboxlow` | 16 CPU, 32GB RAM, 1 day | low |
| `sandboxgpu` | 8 CPU, 16GB RAM, 1 GPU, 1 day | high |
| `sandboxlowgpu` | 8 CPU, 16GB RAM, 1 GPU, 1 day | low |

## Quick Start

### Step 1: Migrate Your Shell Configuration (Run from Cacao/Barbera)

**IMPORTANT**: Run this from your old cluster (cacao/barbera), NOT from HIVE!

```bash
# SSH to cacao or barbera first
ssh username@cacao.genomecenter.ucdavis.edu

# Download just the bash profile migration script
wget https://raw.githubusercontent.com/ianandersonlol/HiveTransition/main/bash_profile_migration.py

# Run it
python bash_profile_migration.py <ssh_username> <quobyte_dir>

# Example:
python bash_profile_migration.py jdoe john
```

### Step 2: Fix Your Job Scripts

For fixing job scripts, clone the repository where YOUR scripts are located:

```bash
git clone https://github.com/ianandersonlol/HiveTransition.git
cd HiveTransition

# Fix individual scripts
python colab_fix.py /path/to/colabfold_job.sh      # For ColabFold
python ligandmpnn_fix.py /path/to/ligandmpnn_job.sh # For LigandMPNN
python rfdiffusion_fix.py /path/to/rfdiff_job.sh    # For RFdiffusion
python rosetta_fix.py /path/to/rosetta_job.sh       # For Rosetta

# Or update all paths at once (no SLURM changes)
python pathMigrator.py /path/to/scripts/directory    # Update all software paths
```

## Available Scripts

### 1. pathMigrator.py (Comprehensive Path Migration)
Updates ALL software paths in a directory:
- Combines path fixes from all other scripts
- Does NOT modify SLURM settings
- Can process entire directories at once
- Includes all software: ColabFold, LigandMPNN, RFdiffusion, Rosetta

**[Full Documentation](docs/pathMigrator.md)**

### 2. bash_profile_migration.py
Migrates your shell configuration to HIVE:
- Converts `.bash_profile` to `.bashrc`
- Sets up conda in quobyte directory
- Adds interactive session aliases
- Updates paths and modules

**[Full Documentation](docs/bash_profile_migration.md)**

### 3. colab_fix.py
Updates ColabFold scripts:
- Fixes ColabFold installation path
- Updates GPU partition settings
- Migrates storage paths

**[Full Documentation](docs/colab_fix.md)**

### 4. ligandmpnn_fix.py
Updates LigandMPNN scripts:
- Fixes LigandMPNN installation path
- Updates GPU partition settings
- Migrates storage paths

**[Full Documentation](docs/ligandmpnn_fix.md)**

### 5. rfdiffusion_fix.py
Updates RFdiffusion scripts:
- Standardizes RFdiffusion installation path
- Updates conda environment to shared SE3nv
- Updates GPU partition settings

**[Full Documentation](docs/rfdiffusion_fix.md)**

### 6. rosetta_fix.py
Updates Rosetta scripts:
- Migrates to Rosetta 3.14
- Changes binary names (`.default.` → `.static.`)
- Handles CPU partition selection
- Enforces time limits

**[Full Documentation](docs/rosetta_fix.md)**

### 7. broken.py
Reports issues with scripts:
- Generates GitHub issue URL
- Pre-fills script content
- Auto-assigns to maintainer

**[Full Documentation](docs/broken.md)**

### 8. run_chai.py
This script performs protein structure prediction using the `chai_lab` library. It takes a FASTA file containing the protein sequence as input and generates a PDB file with the predicted structure.

**[Full Documentation](docs/run_chai.md)**

### 9. chai_with_msa.py
This script performs protein structure prediction using the `chai_lab` library with support for Multiple Sequence Alignments (MSAs). It can use either a pre-computed MSA or an MSA server (ColabFold's MMseqs2).

**[Full Documentation](docs/chai_with_msa.md)**

### 10. submit_chai.sh & submit_chai_with_msa.sh
These scripts are used to submit ChAI jobs to a SLURM cluster. They handle the setup of the environment and the execution of the ChAI python scripts.

**[Full Documentation](docs/submit_chai.md)**


## Common Migration Tasks

### Setting Up Your Environment

1. **Run the migration script from old cluster (cacao/barbera):**
   ```bash
   python bash_profile_migration.py myusername mydirectory
   ```

2. **Log into HIVE:**
   ```bash
   ssh myusername@hive.hpc.ucdavis.edu
   ```

3. **Source your configuration:**
   ```bash
   source ~/.bashrc
   ```

### Migrating Job Scripts

1. **Identify script type** (ColabFold, Rosetta, etc.)

2. **Run appropriate fix script:**
   ```bash
   python <tool>_fix.py myscript.sh
   ```

3. **Review changes:**
   ```bash
   diff myscript.sh myscript_fixed.sh
   ```

4. **Test on HIVE:**
   ```bash
   sbatch myscript_fixed.sh
   ```

### Interactive Sessions

Use the aliases added by bash_profile_migration.py:

```bash
sandbox      # 8 CPU, 16GB RAM, high priority
sandboxlow   # 16 CPU, 32GB RAM, low priority
sandboxgpu   # 8 CPU, 16GB RAM, 1 GPU, high priority
sandboxlowgpu # 8 CPU, 16GB RAM, 1 GPU, low priority
```

## Important Notes

### Storage Management
- Home directory: 20GB limit
- Store everything in `/quobyte/jbsiegelgrp/{your_directory}/`
- Conda environments go in `.conda/envs/`
- Package caches go in `.cache/`

### Module Loading
Instead of local conda:
```bash
module load conda/latest
module load cuda/12.6.2  # For GPU jobs Good to have even when you're not using a GPU so you have the drivers up!
```
**IF YOU USED MY BASH MIGRATION TOOL IT WILL PUT IT IN YOUR BASHRC**
### Partition Selection
- Use `low` for most jobs (< 3 days)
- Use `high` for long jobs (> 3 days)
- GPU jobs need `--account=genome-center-grp`

## Troubleshooting

### Common Issues

1. **"Module not found"**
   - Use `module avail <name>` to find the new module name
   - Some modules have different names on HIVE

2. **"Permission denied"**
   - Check you're writing to your quobyte directory
   - Create directories if they don't exist

3. **"Command not found"**
   - Ensure you've sourced `~/.bashrc`
   - Check if software is in a different location

4. **Time limit errors**
   - Use `--high` flag for Rosetta jobs > 3 days
   - Break large jobs into smaller chunks

### Getting Help

1. **Check documentation:**
   - See `docs/` folder for detailed guides
   - Each script has `--help` option

2. **Report issues:**
   ```bash
   python broken.py problematic_script.sh
   ```

3. **GitHub Issues:**
   - https://github.com/ianandersonlol/HiveTransition/issues

## Contributing

If you find issues or have improvements:

1. Use `broken.py` to report script issues
2. Submit pull requests for fixes
3. Share working examples with the community

## File Structure

```
HiveTransition/
├── README.md                    # This file
├── pathMigrator.py             # Comprehensive path migration (all software)
├── bash_profile_migration.py    # Shell config migration
├── colab_fix.py                # ColabFold script fixer (with SLURM)
├── ligandmpnn_fix.py           # LigandMPNN script fixer (with SLURM)
├── rfdiffusion_fix.py          # RFdiffusion script fixer (with SLURM)
├── rosetta_fix.py              # Rosetta script fixer (with SLURM)
├── broken.py                   # Issue reporter
├── docs/                       # Detailed documentation
│   ├── pathMigrator.md
│   ├── bash_profile_migration.md
│   ├── colab_fix.md
│   ├── ligandmpnn_fix.md
│   ├── rfdiffusion_fix.md
│   ├── rosetta_fix.md
│   └── broken.md
│   ├── run_chai.md
│   ├── chai_with_msa.md
│   └── submit_chai.md
└── .github/
    └── ISSUE_TEMPLATE/
        └── script_not_working.md
```

## Example Scripts

This project includes example scripts to demonstrate how to run common bioinformatics tools in a cluster environment.

### ColabFold

-   **Script:** `example_scripts/colabfold.sh`
-   **Description:** A SLURM submission script for running ColabFold. It is pre-configured with resource requests and sets up the necessary environment.
-   **[Full Documentation](docs/colabfold.md)**

### Chai

-   **Script:** `example_scripts/run_chai.py`
-   **Description:** A script to run protein structure prediction using the `chai_lab` library.
-   **[Full Documentation](docs/run_chai.md)**

-   **Script:** `example_scripts/chai_with_msa.py`
-   **Description:** A script to run protein structure prediction using the `chai_lab` library with MSA support.
-   **[Full Documentation](docs/chai_with_msa.md)**

-   **Scripts:** `example_scripts/submit_chai.sh`, `example_scripts/submit_chai_with_msa.sh`
-   **Description:** SLURM submission scripts for `run_chai.py` and `chai_with_msa.py`.
-   **[Full Documentation](docs/submit_chai.md)**
