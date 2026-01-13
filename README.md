# HIVE Cluster Migration Tools

This repository contains scripts to help migrate from the old HPC cluster to the new HIVE cluster.

## Create a HIVE Account

Before you can use the HIVE cluster, you need to create an account.

### Step 1: Request Access

1. Go to [https://hippo.ucdavis.edu/](https://hippo.ucdavis.edu/)
2. Sign in with your Kerberos (campus) credentials
3. Select **"HIVE"** to create a HIVE account

![HIVE selection screen on hippo.ucdavis.edu](images/hive_setup_1.png)

### Step 2: Fill Out the Registration Form

Complete the form with your information. You'll need to provide an SSH public key. If you don't have one, follow the instructions below to create one.

![HIVE registration form](images/hive_setup_2.png)

### Setting Up an SSH Key

An SSH key allows you to securely connect to HIVE without entering a password each time. Follow the instructions for your operating system.

#### Windows (PowerShell)

**1. Check if an SSH key already exists:**

```powershell
Test-Path "$HOME\.ssh\id_ed25519.pub"
```

- If it returns `True`, you already have an SSH key—skip to step 3.
- If it returns `False`, proceed to step 2.

**2. Create an SSH key (if needed):**

```powershell
ssh-keygen -t ed25519 -C "your_email@example.com"
```

- Press **Enter** to accept the default file location
- Optionally, enter a passphrase for added security (recommended)

**3. Copy the public key to your clipboard:**

```powershell
Get-Content "$HOME\.ssh\id_ed25519.pub" | Set-Clipboard
```

Your public key is now copied and ready to paste into the HIVE registration form.

#### macOS and Linux

**1. Check if an SSH key already exists:**

```bash
if [ -f ~/.ssh/id_ed25519.pub ]; then echo "SSH key exists"; else echo "No SSH key found"; fi
```

- If the message confirms an existing key, skip to step 3.
- If not, proceed to step 2.

**2. Create an SSH key (if needed):**

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

- Press **Enter** to confirm the default location
- Optionally, add a passphrase for additional security (recommended)

**3. Copy the public key:**

On **macOS**:
```bash
pbcopy < ~/.ssh/id_ed25519.pub
```

On **Linux** (with xclip installed):
```bash
xclip -selection clipboard < ~/.ssh/id_ed25519.pub
```

Or display the key and copy it manually:
```bash
cat ~/.ssh/id_ed25519.pub
```

#### Windows Subsystem for Linux (WSL)

WSL maintains its own SSH configuration separate from Windows:

- **In PowerShell:** Follow the Windows instructions above to manage your native Windows SSH keys
- **In WSL Terminal:** Follow the macOS/Linux instructions within your WSL environment

---

## Table of Contents

- [Create a HIVE Account](#create-a-hive-account)
  - [Setting Up an SSH Key](#setting-up-an-ssh-key)
- [Getting Started](#getting-started)
  - [Understanding Shell Configuration Files](#understanding-shell-configuration-files)
  - [Logging into HIVE](#logging-into-hive)
  - [Interactive Sessions](#interactive-sessions)
- [HIVE vs Cacao Comparison](#hive-vs-cacao-comparison)
  - [Key Differences Between Clusters](#key-differences-between-clusters)
  - [Software Locations](#software-locations)
  - [Storage Management](#storage-management)
  - [SLURM Changes](#slurm-changes)
  - [Interactive Sessions Reference](#interactive-sessions-reference)
- [File Structure](#file-structure)
- [Important Notes](#important-notes)
- [Troubleshooting](#troubleshooting)
- [Example Scripts](#example-scripts)
  - [Partitions](#partitions)
  - [ColabFold](#colabfold)
  - [AlphaFold 3](#alphafold-3)
  - [AlphaFold 2 Initial Guess](#alphafold-2-initial-guess)
  - [Boltz2](#boltz2)
  - [Chai](#chai)
  - [LigandMPNN](#ligandmpnn)
  - [RFdiffusion](#rfdiffusion)
  - [MPNNP Pipeline](#mpnnp-pipeline)
  - [GALigandDock](#galigand-dock)
  - [Relaxation](#relaxation)
- [Cluster Transition Tools (Legacy)](#cluster-transition-tools-legacy)
- [Contributing](#contributing)

## Getting Started

### Understanding Shell Configuration Files

Before getting started, it's important to understand the difference between `.bashrc` and `.bash_profile`:

**`.bash_profile`:**
- Sourced for **login shells** (when you SSH into a server)
- Runs once when you first log in
- Best for setting up environment variables, PATH, and one-time setup

**`.bashrc`:**
- Sourced for **non-login interactive shells** (when you open a new terminal window or run `bash`)
- Runs every time you start a new shell
- Best for aliases, functions, and shell settings

**HIVE Configuration:**
On HIVE, we use a minimal `.bash_profile` that sources `.bashrc`. This gives us the best of both worlds:
- Your environment loads automatically when you SSH in (via `.bash_profile`)
- All your customizations live in `.bashrc` for consistency

The `bash_profile_migration.py` script sets this up automatically. If you didn't use the migration script, your `.bash_profile` should contain:
```bash
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
```

If your `.bash_profile` doesn't have this, you can manually load your environment after logging in:
```bash
source ~/.bashrc
```

### Logging into HIVE

To access the HIVE cluster, use SSH with your campus credentials:

```bash
ssh username@hive.hpc.ucdavis.edu
```

Your environment will be automatically loaded if your `.bash_profile` sources `.bashrc` (which the migration script sets up for you).

### Interactive Sessions

On Cacao, we were used to running commands directly on the head node for quick testing and development. On HIVE, running jobs on the head node is not allowed. Instead, we use **interactive sessions** to create a sandbox-like environment similar to what we had on Cacao.

Interactive sessions allocate resources on compute nodes where you can run commands interactively. Here are the commands and convenient aliases:

**High Priority CPU Session:**
```bash
# Full command:
srun -p high -c 8 --mem=16G -t 1-00:00:00 --pty bash

# Convenient alias (if you used bash_profile_migration.py):
sandbox
```

**Low Priority CPU Session:**
```bash
# Full command:
srun -p low -c 16 --mem=32G -t 1-00:00:00 --requeue --pty bash

# Convenient alias:
sandboxlow
```

**High Priority GPU Session:**
```bash
# Full command:
srun -p gpu-a100 --account=genome-center-grp -c 8 --mem=16G --gres=gpu:1 -t 1-00:00:00 --pty bash

# Convenient alias:
sandboxgpu
```

**Low Priority GPU Session:**
```bash
# Full command:
srun -p gpu-a100 --account=genome-center-grp -c 8 --mem=16G --gres=gpu:1 -t 1-00:00:00 --requeue --pty bash

# Convenient alias:
sandboxlowgpu
```

**Note:** The aliases (`sandbox`, `sandboxlow`, etc.) are automatically added to your `.bashrc` if you used the `bash_profile_migration.py` script. If you didn't use the migration script, you can still use the full `srun` commands above, or add the aliases manually to your `.bashrc`.

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

### Interactive Sessions Reference

Convenient aliases and their full `srun` commands for interactive sessions:

| Alias | Full Command | Resources | Partition |
|-------|--------------|-----------|-----------|
| `sandbox` | `srun -p high -c 8 --mem=16G -t 1-00:00:00 --pty bash` | 8 CPU, 16GB RAM, 1 day | high |
| `sandboxlow` | `srun -p low -c 16 --mem=32G -t 1-00:00:00 --requeue --pty bash` | 16 CPU, 32GB RAM, 1 day | low |
| `sandboxgpu` | `srun -p gpu-a100 --account=genome-center-grp -c 8 --mem=16G --gres=gpu:1 -t 1-00:00:00 --pty bash` | 8 CPU, 16GB RAM, 1 GPU, 1 day | gpu-a100 |
| `sandboxlowgpu` | `srun -p gpu-a100 --account=genome-center-grp -c 8 --mem=16G --gres=gpu:1 -t 1-00:00:00 --requeue --pty bash` | 8 CPU, 16GB RAM, 1 GPU, 1 day | gpu-a100 (low priority) |

**Note:** These aliases are added automatically by the `bash_profile_migration.py` script. See [Getting Started](#getting-started) for more information on interactive sessions.

## File Structure

```
HiveTransition/
├── .gitignore
├── README.md
├── CLAUDE.md
├── CHANGELOG.md
├── images/
│   ├── hive_setup_1.png
│   └── hive_setup_2.png
├── docs/
│   ├── migrate.md
│   ├── transition_tools.md
│   ├── partitions.md
│   ├── colabfold.md
│   ├── alphafold3.md
│   ├── af2_initial_guess.md
│   ├── run_boltz.md
│   ├── chai_to_boltz.md
│   ├── run_chai.md
│   ├── chai_with_msa.md
│   ├── submit_chai.md
│   ├── ligandmpnn.md
│   ├── rf_diffusion_aa.md
│   ├── mpnnp_pipeline.md
│   ├── galigand_dock.md
│   ├── relax.md
│   ├── path_migrator.md
│   ├── colab_fix.md
│   ├── ligandmpnn_fix.md
│   ├── rfdiffusion_fix.md
│   ├── rosetta_fix.md
│   ├── bash_profile_migration.md
│   └── broken.md
│
├── example_scripts/
│   ├── partitions/
│   │   ├── low_cpus.sh
│   │   ├── high_cpus.sh
│   │   └── gbsf_cpus.sh
│   │
│   ├── folding/
│   │   ├── alphafold2/
│   │   │   ├── local_colabfold/
│   │   │   │   └── colabfold.sh
│   │   │   └── af2_initial_guess/
│   │   │       ├── run_af2_initial_guess.py
│   │   │       └── submit_af2_initial_guess.sh
│   │   ├── alphafold3/
│   │   │   ├── submit_af3_single.sh
│   │   │   └── submit_af3_bulk.py
│   │   ├── boltz2/
│   │   │   ├── runners/
│   │   │   │   └── run_boltz.sh
│   │   │   └── helpers/
│   │   │       └── chai_to_boltz.py
│   │   └── chai/
│   │       ├── run_chai.py
│   │       ├── chai_with_msa.py
│   │       ├── submit_chai.sh
│   │       └── submit_chai_with_msa.sh
│   │
│   ├── design/
│   │   ├── diffusion/
│   │   │   └── rf_diffusion_aa.sh
│   │   ├── ligandmpnn/
│   │   │   └── submit_ligandmpnn.sh
│   │   └── mpnnp_pipeline/
│   │       └── run_pipeline.py
│   │
│   └── docking/
│       ├── galigand_dock/
│       │   └── submit.sh
│       └── relaxation/
│           └── relax.sh
│
└── transition_tools_old/
    ├── migrate.py
    ├── path_migrator.py
    ├── colab_fix.py
    ├── ligandmpnn_fix.py
    ├── rfdiffusion_fix.py
    ├── rosetta_fix.py
    ├── bash_profile_migration.py
    └── broken.py
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

## Example Scripts

This project includes example scripts to demonstrate how to run common bioinformatics tools in a cluster environment.

### Partitions

-   **Scripts:** `example_scripts/partitions/low_cpus.sh`, `example_scripts/partitions/high_cpus.sh`, `example_scripts/partitions/gbsf_cpus.sh`
-   **Description:** Example SLURM submission scripts demonstrating how to use different partitions on HIVE.
-   **[Full Documentation](docs/partitions.md)**

### ColabFold

-   **Script:** `example_scripts/folding/alphafold2/local_colabfold/colabfold.sh`
-   **Description:** SLURM submission script for running ColabFold structure predictions.
-   **[Full Documentation](docs/colabfold.md)**

### AlphaFold 3

-   **Scripts:** `example_scripts/folding/alphafold3/submit_af3_single.sh`, `example_scripts/folding/alphafold3/submit_af3_bulk.py`
-   **Description:** SLURM submission scripts for AlphaFold 3 predictions. Supports single predictions and bulk array jobs with GPU monitoring.
-   **[Full Documentation](docs/alphafold3.md)**

### AlphaFold 2 Initial Guess

-   **Scripts:** `example_scripts/folding/alphafold2/af2_initial_guess/run_af2_initial_guess.py`, `example_scripts/folding/alphafold2/af2_initial_guess/submit_af2_initial_guess.sh`
-   **Description:** Runs AlphaFold 2 predictions using a reference PDB structure as a template.
-   **[Full Documentation](docs/af2_initial_guess.md)**

### Boltz2

-   **Script:** `example_scripts/folding/boltz2/runners/run_boltz.sh`
-   **Description:** SLURM submission script for Boltz2 structure predictions. Supports proteins, nucleic acids, and small molecules.
-   **Helper:** `chai_to_boltz.py` converts Chai FASTA format to Boltz2 YAML format.
-   **[Full Documentation](docs/run_boltz.md)** | **[chai_to_boltz.md](docs/chai_to_boltz.md)**

### Chai

-   **Scripts:** `example_scripts/folding/chai/submit_chai.sh`, `example_scripts/folding/chai/submit_chai_with_msa.sh`
-   **Description:** SLURM submission scripts for Chai structure predictions with or without MSA.
-   **[Full Documentation](docs/submit_chai.md)** | **[run_chai.md](docs/run_chai.md)** | **[chai_with_msa.md](docs/chai_with_msa.md)**

### LigandMPNN

-   **Script:** `example_scripts/design/ligandmpnn/submit_ligandmpnn.sh`
-   **Description:** SLURM submission script for LigandMPNN protein design.
-   **[Full Documentation](docs/ligandmpnn.md)**

### RFdiffusion

-   **Script:** `example_scripts/design/diffusion/rf_diffusion_aa.sh`
-   **Description:** A SLURM submission script for running RFdiffusion for *de novo* protein design. It is pre-configured with common parameters for protein design tasks.
-   **[Full Documentation](docs/rf_diffusion_aa.md)**

### MPNNP Pipeline

-   **Script:** `example_scripts/design/mpnnp_pipeline/run_pipeline.py`
-   **Description:** A unified, automated protein design pipeline that integrates MSA generation, conservation analysis, structure prediction, and LigandMPNN design. Takes a protein sequence and produces structurally-validated designed variants.
-   **[Full Documentation](docs/mpnnp_pipeline.md)**

### GALigandDock

-   **Script:** `example_scripts/docking/galigand_dock/submit.sh`
-   **Description:** A SLURM submission script for running the GALigandDock protocol. It is pre-configured with resource requests and sets up the necessary environment.
-   **[Full Documentation](docs/galigand_dock.md)**

### Relaxation

-   **Script:** `example_scripts/docking/relaxation/relax.sh`
-   **Description:** A SLURM submission script for running Rosetta relaxation. It is pre-configured with resource requests and sets up the necessary environment.
-   **[Full Documentation](docs/relax.md)**

## Cluster Transition Tools (Legacy)

These tools were created to help migrate from the old Cacao/Barbera HPC cluster to the new HIVE cluster. As the transition is largely complete, these tools are now considered legacy and are archived in the `transition_tools_old/` directory.

For detailed information about all available transition tools (path_migrator.py, bash_profile_migration.py, colab_fix.py, ligandmpnn_fix.py, rfdiffusion_fix.py, rosetta_fix.py, and broken.py), see:

**[Cluster Transition Tools Documentation](docs/transition_tools.md)**

## Contributing

If you find issues or have improvements:

1. Use `transition_tools_old/broken.py` to report script issues
2. Submit pull requests for fixes
3. Share working examples with the lab

---

Changes to this working document can be found in [CHANGELOG.md](CHANGELOG.md).
