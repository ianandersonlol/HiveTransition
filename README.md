# HIVE Cluster Resources

This repository contains example SLURM scripts and documentation for running computational biology workflows on the HIVE HPC cluster at UC Davis.

## Create a HIVE Account

Before you can use the HIVE cluster, you need to create an account.

### Step 1: Request Access

1. Go to [https://hippo.ucdavis.edu/](https://hippo.ucdavis.edu/)
2. Sign in with your Kerberos (campus) credentials
3. Select **"HIVE"** to create a HIVE account

<img src="images/hive_setup_1.png" alt="HIVE selection screen on hippo.ucdavis.edu" width="900">

### Step 2: Fill Out the Registration Form

Complete the form with your information. You'll need to provide an SSH public key. If you don't have one, follow the instructions below to create one.

<img src="images/hive_setup_2.png" alt="HIVE registration form" width="900">

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
- [HIVE Quick Reference](#hive-quick-reference)
  - [Software Locations](#software-locations)
  - [Storage Paths](#storage-paths)
  - [SLURM Partitions](#slurm-partitions)
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
- [Contributing](#contributing)

## Getting Started

### Understanding Shell Configuration Files

Before getting started, it's helpful to understand the difference between `.bashrc` and `.bash_profile`:

**`.bash_profile`:**
- Sourced for **login shells** (when you SSH into a server)
- Runs once when you first log in
- Best for setting up environment variables, PATH, and one-time setup

**`.bashrc`:**
- Sourced for **non-login interactive shells** (when you open a new terminal window or run `bash`)
- Runs every time you start a new shell
- Best for aliases, functions, and shell settings

**Two Common Approaches:**

You can organize your shell configuration however you prefer. Here are two common approaches:

**Option 1: Everything in `.bash_profile`** (simplest)
- Put all your settings directly in `.bash_profile`
- Works fine if you only SSH into the cluster and don't spawn subshells

**Option 2: Source `.bashrc` from `.bash_profile`** (Ian's preference)
- Keep a minimal `.bash_profile` that just loads `.bashrc`
- Put all your actual configuration in `.bashrc`
- This ensures your settings are available in both login shells and subshells

To set up Option 2, add this to your `.bash_profile`:
```bash
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi
```

If you're using Option 1 and find that your aliases/settings aren't available after running `bash` or in SLURM jobs, you may want to switch to Option 2, or manually source your config:
```bash
source ~/.bash_profile
```

### Logging into HIVE

To access the HIVE cluster, use SSH with your campus credentials:

```bash
ssh username@hive.hpc.ucdavis.edu
```

### Interactive Sessions

On HIVE, running jobs on the head node is not allowed. Instead, use **interactive sessions** to get a shell on a compute node where you can run commands interactively.

Interactive sessions allocate resources on compute nodes. Here are common configurations:

**High Priority CPU Session:**
```bash
srun -p high -c 8 --mem=16G -t 1-00:00:00 --pty bash
```

**Low Priority CPU Session:**
```bash
srun -p low -c 16 --mem=32G -t 1-00:00:00 --requeue --pty bash
```

**High Priority GPU Session:**
```bash
srun -p gpu-a100 --account=genome-center-grp -c 8 --mem=16G --gres=gpu:1 -t 1-00:00:00 --pty bash
```

**Low Priority GPU Session:**
```bash
srun -p gpu-a100 --account=genome-center-grp -c 8 --mem=16G --gres=gpu:1 -t 1-00:00:00 --requeue --pty bash
```

**Tip:** These commands are long. Consider adding aliases to your shell config for commands you use frequently. For example:
```bash
alias sandbox='srun -p high -c 8 --mem=16G -t 1-00:00:00 --pty bash'
alias sandboxgpu='srun -p gpu-a100 --account=genome-center-grp -c 8 --mem=16G --gres=gpu:1 -t 1-00:00:00 --pty bash'
```

## HIVE Quick Reference

### Software Locations

| Software | Path |
|----------|------|
| **ColabFold** | `/quobyte/jbsiegelgrp/software/LocalColabFold/` |
| **LigandMPNN** | `/quobyte/jbsiegelgrp/software/LigandMPNN/` |
| **RFdiffusion** | `/quobyte/jbsiegelgrp/software/RFdiffusion/` |
| **RFdiffusion Conda Env** | `/quobyte/jbsiegelgrp/software/envs/SE3nv` |
| **Rosetta 3.14** | `/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/` |

**Note:** Rosetta binaries use the `.static.linuxgccrelease` suffix.

### Storage Paths

Your home directory has a **20GB limit**. Store large files and caches in your quobyte directory:

| What | Where to Put It |
|------|-----------------|
| **Lab storage** | `/quobyte/jbsiegelgrp/` |
| **Conda packages** | `/quobyte/jbsiegelgrp/{user}/.conda/pkgs` |
| **Conda environments** | `/quobyte/jbsiegelgrp/{user}/.conda/envs` |
| **Pip cache** | `/quobyte/jbsiegelgrp/{user}/.cache/pip` |
| **HuggingFace cache** | `/quobyte/jbsiegelgrp/{user}/.cache/huggingface` |
| **PyTorch cache** | `/quobyte/jbsiegelgrp/{user}/.cache/torch` |

### SLURM Partitions

| Partition | Max Time | Notes |
|-----------|----------|-------|
| `low` | 3 days | Default for most jobs. Use `--requeue` flag (auto-requeues if preempted) |
| `high` | 30 days | For long-running jobs |
| `gpu-a100` | — | Requires `--account=genome-center-grp` |

**GPU job example:**
```bash
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
```

**CPU job example (low priority):**
```bash
#SBATCH --partition=low
#SBATCH --requeue
```

## File Structure

```
HiveTransition/
├── README.md
├── CHANGELOG.md
├── images/
│   ├── hive_setup_1.png
│   └── hive_setup_2.png
├── docs/
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
│   └── relax.md
│
└── example_scripts/
    ├── partitions/
    │   ├── low_cpus.sh
    │   ├── high_cpus.sh
    │   └── gbsf_cpus.sh
    │
    ├── folding/
    │   ├── alphafold2/
    │   │   ├── local_colabfold/
    │   │   │   └── colabfold.sh
    │   │   └── af2_initial_guess/
    │   │       ├── run_af2_initial_guess.py
    │   │       └── submit_af2_initial_guess.sh
    │   ├── alphafold3/
    │   │   ├── submit_af3_single.sh
    │   │   └── submit_af3_bulk.py
    │   ├── boltz2/
    │   │   ├── runners/
    │   │   │   └── run_boltz.sh
    │   │   └── helpers/
    │   │       └── chai_to_boltz.py
    │   └── chai/
    │       ├── run_chai.py
    │       ├── chai_with_msa.py
    │       ├── submit_chai.sh
    │       └── submit_chai_with_msa.sh
    │
    ├── design/
    │   ├── diffusion/
    │   │   └── rf_diffusion_aa.sh
    │   ├── ligandmpnn/
    │   │   └── submit_ligandmpnn.sh
    │   └── mpnnp_pipeline/
    │       └── run_pipeline.py
    │
    └── docking/
        ├── galigand_dock/
        │   └── submit.sh
        └── relaxation/
            └── relax.sh
```

## Important Notes

### Module Loading

Load conda and CUDA using the module system:
```bash
module load conda/latest
module load cuda/12.6.2  # Good to have even when you're not using a GPU
```

You can add these to your shell config so they load automatically on login.

## Troubleshooting

### Common Issues

1. **"Module not found"**
   - Use `module avail <name>` to find the correct module name

2. **"Permission denied"**
   - Check you're writing to your quobyte directory
   - Create directories if they don't exist

3. **"Command not found"**
   - Ensure you've sourced your shell config
   - Check if software is in a different location

4. **Time limit errors**
   - Use `high` partition for jobs > 3 days
   - Break large jobs into smaller chunks

### Getting Help

1. **Check documentation:**
   - See `docs/` folder for detailed guides
   - Each script has `--help` option

2. **GitHub Issues:**
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

## Contributing

If you find issues or have improvements:

1. Open an issue on GitHub
2. Submit pull requests for fixes
3. Share working examples with the lab

---

Changes to this working document can be found in [CHANGELOG.md](CHANGELOG.md).
