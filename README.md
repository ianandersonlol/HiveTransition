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
  - [Step 1: Migrate Your Shell Configuration (Run from Cacao/Barbera)](#step-1-migrate-your-shell-configuration-run-from-cacaobarbera)
  - [Step 2: Fix Your Job Scripts](#step-2-fix-your-job-scripts)
- [Common Migration Tasks](#common-migration-tasks)
  - [Setting Up Your Environment](#setting-up-your-environment)
  - [Migrating Job Scripts](#migrating-job-scripts)
  - [Interactive Sessions](#interactive-sessions-1)
- [Important Notes](#important-notes)
- [Troubleshooting](#troubleshooting)
- [File Structure](#file-structure)
- [Example Scripts](#example-scripts)
  - [Partitions](#partitions)
  - [ColabFold](#colabfold)
  - [AlphaFold 3](#alphafold-3)
  - [AlphaFold 2 Initial Guess](#alphafold-2-initial-guess)
  - [Boltz2](#boltz2)
    - [run_boltz.sh](#run_boltzsh)
    - [chai_to_boltz.py](#chai_to_boltzpy)
  - [Chai](#chai)
    - [run_chai.py](#run_chaipy)
    - [chai_with_msa.py](#chai_with_msapy)
    - [submit_chai.sh & submit_chai_with_msa.sh](#submit_chaish_&_submit_chai_with_msash)
  - [LigandMPNN](#ligandmpnn)
  - [GaliGand Dock](#galigand-dock)
  - [Relaxation](#relaxation)
- [Cluster Transition Tools (Legacy)](#cluster-transition-tools-legacy)

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
wget https://raw.githubusercontent.com/ianandersonlol/HiveTransition/main/transition_tools_old/bash_profile_migration.py

# Run it
python bash_profile_migration.py <ssh_username> <quobyte_dir>

# Example:
python bash_profile_migration.py jdoe john
```

### Step 2: Fix Your Job Scripts

**RECOMMENDED**: Use the new unified migration script that handles all fix types automatically.

For fixing job scripts, clone the repository where YOUR scripts are located:

```bash
git clone https://github.com/ianandersonlol/HiveTransition.git
cd HiveTransition/transition_tools_old

# RECOMMENDED: Use the unified migration script
python migrate.py /path/to/script.sh           # Fix single script
python migrate.py /path/to/scripts/            # Fix entire directory
python migrate.py /path/to/scripts/ --dry-run  # Preview changes first

# For Rosetta jobs longer than 3 days, use --high flag
python migrate.py rosetta_job.sh --high

# Legacy: Individual fix scripts (still available but migrate.py is preferred)
python colab_fix.py /path/to/colabfold_job.sh      # For ColabFold
python ligandmpnn_fix.py /path/to/ligandmpnn_job.sh # For LigandMPNN
python rfdiffusion_fix.py /path/to/rfdiff_job.sh    # For RFdiffusion
python rosetta_fix.py /path/to/rosetta_job.sh       # For Rosetta
python pathMigrator.py /path/to/scripts/directory   # Update all software paths
```

## Common Migration Tasks

### Setting Up Your Environment

1. **Run the migration script from old cluster (cacao/barbera):**
   ```bash
   python transition_tools_old/bash_profile_migration.py myusername mydirectory
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

1. **Preview changes first:**
   ```bash
   python transition_tools_old/migrate.py myscript.sh --dry-run
   ```

2. **Run the migration:**
   ```bash
   python transition_tools_old/migrate.py myscript.sh
   ```

3. **Review changes:**
   ```bash
   diff myscript.sh myscript_fixed.sh
   ```

4. **Test on HIVE:**
   ```bash
   sbatch myscript_fixed.sh
   ```

**Tip**: For long Rosetta jobs (>3 days), add `--high` flag to use the high partition.

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
   python transition_tools_old/broken.py problematic_script.sh
   ```

3. **GitHub Issues:**
   - https://github.com/ianandersonlol/HiveTransition/issues

## Contributing

If you find issues or have improvements:

1. Use `transition_tools_old/broken.py` to report script issues
2. Submit pull requests for fixes
3. Share working examples with the community

## File Structure

```
/Users/iananderson/Desktop/HiveTransition/
├───.gitignore
├───README.md
├───.claude/
│   └───settings.local.json
├───.git/...
├───.github/
│   └───ISSUE_TEMPLATE/
│       └───script_not_working.yml
├───docs/
│   ├───bash_profile_migration.md
│   ├───broken.md
│   ├───chai_with_msa.md
│   ├───colab_fix.md
│   ├───colabfold.md
│   ├───galigand_dock.md
│   ├───ligandmpnn_fix.md
│   ├───ligandmpnn.md
│   ├───mpnnp_pipeline.md
│   ├───pathMigrator.md
│   ├───relax.md
│   ├───rfdiffusion_fix.py
│   ├───rosetta_fix.py
│   ├───run_chai.md
│   ├───submit_chai.md
│   └───transition_tools.md
├───example_scripts/
│   ├───design/
│   │   ├───Diffusion/
│   │   │   └───rf_diffusion_aa.sh
│   │   ├───LigandMPNN/
│   │   │   └───submit_ligandMPNN.sh
│   │   └───MPNNP_Pipeline/
│   │       └───run_pipeline.py
│   ├───docking/
│   │   ├───galigand_dock/
│   │   │   ├───4Epimv7.cst
│   │   │   ├───DF6.params
│   │   │   ├───docking.xml
│   │   │   ├───flags
│   │   │   ├───GatZ_F6P.pdb
│   │   │   └───submit.sh
│   │   └───relaxation/
│   │       └───relax.sh
│   └───folding/
│       ├───Alphafold2/
│       │   └───colabfold.sh
│       └───Chai/
│           ├───chai_with_msa.py
│           ├───run_chai.py
│           ├───submit_chai_with_msa.sh
│           └───submit_chai.sh
└───transition_tools_old/
    ├───bash_profile_migration.py
    ├───broken.py
    ├───colab_fix.py
    ├───ligandmpnn_fix.py
    ├───pathMigrator.py
    ├───rfdiffusion_fix.py
    └───rosetta_fix.py
```

## Example Scripts

This project includes example scripts to demonstrate how to run common bioinformatics tools in a cluster environment.

### Partitions

-   **Scripts:** `example_scripts/partitions/low_cpus.sh`, `example_scripts/partitions/high_cpus.sh`, `example_scripts/partitions/gbsf_cpus.sh`
-   **Description:** Example SLURM submission scripts demonstrating how to use different partitions on HIVE: low priority (3 day max, can be preempted), high priority with group resources (30 day max, jbsiegelgrp account), and high priority with genome center shared resources (30 day max, genomecentergrp account).
-   **[Full Documentation](docs/partitions.md)**

### ColabFold

-   **Script:** `example_scripts/folding/Alphafold2/colabfold.sh`
-   **Description:** A SLURM submission script for running ColabFold. It is pre-configured with resource requests and sets up the necessary environment.
-   **[Full Documentation](docs/colabfold.md)**

### AlphaFold 3

-   **Scripts:** `example_scripts/folding/Alphafold3/submit_af3_single.sh`, `example_scripts/folding/Alphafold3/submit_af3_bulk.py`
-   **Description:** SLURM submission scripts for running AlphaFold 3 predictions. Supports single predictions and bulk array jobs with GPU monitoring and resource tracking.
-   **[Full Documentation](docs/alphafold3.md)**

### AlphaFold 2 Initial Guess

-   **Scripts:** `example_scripts/folding/Alphafold2/AF2_InitialGuess/run_AF2IG.py`, `example_scripts/folding/Alphafold2/AF2_InitialGuess/submit_AF2IG.sh`
-   **Description:** Scripts for running AlphaFold 2 predictions on multiple sequences using a reference PDB structure as a template. Threads each sequence from a multi-sequence FASTA file onto the reference structure and runs AF2 predictions with structural constraints.
-   **[Full Documentation](docs/af2_initial_guess.md)**

### Boltz2

#### run_boltz.sh
-   **Script:** `example_scripts/folding/Boltz2/runners/run_boltz.sh`
-   **Description:** A SLURM submission script for running Boltz2 structure predictions. Supports proteins, nucleic acids (DNA/RNA), and small molecule ligands using YAML input files.
-   **[Full Documentation](docs/run_boltz.md)**

#### chai_to_boltz.py
-   **Script:** `example_scripts/folding/Boltz2/helpers/chai_to_boltz.py`
-   **Description:** A helper utility to convert Chai FASTA format files to Boltz2 YAML format, enabling easy reuse of Chai input files with Boltz2.
-   **[Full Documentation](docs/chai_to_boltz.md)**

### Chai

#### run_chai.py
-   **Script:** `example_scripts/folding/Chai/run_chai.py`
-   **Description:** A script to run protein structure prediction using the `chai_lab` library.
-   **[Full Documentation](docs/run_chai.md)**

#### chai_with_msa.py
-   **Script:** `example_scripts/folding/Chai/chai_with_msa.py`
-   **Description:** A script to run protein structure prediction using the `chai_lab` library with MSA support.
-   **[Full Documentation](docs/chai_with_msa.md)**

#### submit_chai.sh & submit_chai_with_msa.sh
-   **Scripts:** `example_scripts/folding/Chai/submit_chai.sh`, `example_scripts/folding/Chai/submit_chai_with_msa.sh`
-   **Description:** SLURM submission scripts for `run_chai.py` and `chai_with_msa.py`.
-   **[Full Documentation](docs/submit_chai.md)**

### LigandMPNN

-   **Script:** `example_scripts/design/LigandMPNN/submit_ligandMPNN.sh`
-   **Description:** A SLURM submission script for running LigandMPNN. It is pre-configured with resource requests and sets up the necessary environment.
-   **[Full Documentation](docs/ligandmpnn.md)**

### RFdiffusion

-   **Script:** `example_scripts/design/Diffusion/rf_diffusion_aa.sh`
-   **Description:** A SLURM submission script for running RFdiffusion for *de novo* protein design. It is pre-configured with common parameters for protein design tasks.
-   **[Full Documentation](docs/rf_diffusion_aa.md)**

### MPNNP Pipeline

-   **Script:** `example_scripts/design/MPNNP_Pipeline/run_pipeline.py`
-   **Description:** A unified, automated protein design pipeline that integrates MSA generation, conservation analysis, structure prediction, and LigandMPNN design. Takes a protein sequence and produces structurally-validated designed variants.
-   **[Full Documentation](docs/mpnnp_pipeline.md)**

### GaliGand Dock

-   **Script:** `example_scripts/docking/galigand_dock/submit.sh`
-   **Description:** A SLURM submission script for running the GaliGand docking protocol. It is pre-configured with resource requests and sets up the necessary environment.
-   **[Full Documentation](docs/galigand_dock.md)**

### Relaxation

-   **Script:** `example_scripts/docking/relaxation/relax.sh`
-   **Description:** A SLURM submission script for running Rosetta relaxation. It is pre-configured with resource requests and sets up the necessary environment.
-   **[Full Documentation](docs/relax.md)**

## Cluster Transition Tools (Legacy)

These tools were created to help migrate from the old Cacao/Barbera HPC cluster to the new HIVE cluster. As the transition is largely complete, these tools are now considered legacy and are archived in the `transition_tools_old/` directory.

For detailed information about all available transition tools (pathMigrator.py, bash_profile_migration.py, colab_fix.py, ligandmpnn_fix.py, rfdiffusion_fix.py, rosetta_fix.py, and broken.py), see:

**[Cluster Transition Tools Documentation](docs/transition_tools.md)**
