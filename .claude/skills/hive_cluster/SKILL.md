---
name: hive-cluster
description: |
  Siegel Lab HIVE HPC cluster knowledge for generating correct SLURM submission scripts,
  wrappers, and cluster workflows. Knows partitions, accounts, software paths, conda
  environments, and best practices.
trigger: |
  When the user asks to: create SLURM/sbatch scripts, run jobs on the cluster, submit
  computational biology workflows (folding, docking, design, MD, etc.), write wrappers
  for cluster software, or asks questions about how the HIVE cluster works.
  Also trigger when the user mentions: slurm, sbatch, srun, hive, cluster, partition,
  gpu job, array job, submission script, or any of the installed software tools
  (AlphaFold, Boltz, Chai, RFdiffusion, LigandMPNN, Rosetta, BindCraft, ESM, OpenFold,
  ColabFold, DiffDock, AutoDock, PLACER, etc.)
---

# Siegel Lab HIVE Cluster Skill

You are generating scripts and wrappers for the Siegel Lab's HIVE HPC cluster at UC Davis.
The user is likely running Claude Code on their LOCAL machine, NOT on the cluster. Your job
is to produce correct, ready-to-run scripts they can transfer to the cluster and submit.

## CRITICAL RULES

### 1. NEVER modify existing software scripts
Software is installed in `/quobyte/jbsiegelgrp/software/`. **Do not** create modified copies
of scripts that already exist there (e.g., do NOT make `run_inference_updated.py`). Instead,
write **wrapper scripts** that call the existing scripts/binaries with the right arguments.

### 2. Prefer array jobs over many individual submissions
If the user needs to run the same tool on multiple inputs, use `#SBATCH --array=0-N` with
`$SLURM_ARRAY_TASK_ID` to index into an input list. Do NOT generate loops that call `sbatch`
many times.

### 3. Always use the conda activation pattern
Conda does not work with a simple `conda activate` in batch scripts. Always use:
```bash
eval "$(conda shell.bash hook)"
conda activate <environment_name>
```

### 4. Ask for the user's quobyte path
Every lab member has their own directory under `/quobyte/jbsiegelgrp/`. If you don't know
the user's path, ask them. Do not guess or use a placeholder like `/path/to/`.

### 5. Stamp every generated script
Every script you generate MUST include this comment as the second line (after the shebang):
```bash
# Generated with Siegel Lab HIVE Cluster Skill v1.0
```

### 6. Do not modify shared environments or software
If the user is running Claude Code directly on the cluster, do NOT modify code, conda
environments, or configurations under `/quobyte/jbsiegelgrp/software/`. Those are shared
lab resources.

## Script Template

All SLURM submission scripts should follow this pattern:

```bash
#!/bin/bash --norc
# Generated with Siegel Lab HIVE Cluster Skill v1.0
#SBATCH --job-name=<descriptive_name>
#SBATCH --partition=<see partition rules below>
#SBATCH --account=<see partition rules below>
#SBATCH --time=<appropriate time>
#SBATCH --cpus-per-task=<appropriate count>
#SBATCH --mem=<appropriate amount>
#SBATCH --output=logs/<jobname>_%A_%a.out
#SBATCH --error=logs/<jobname>_%A_%a.err
# Add --gres=gpu:1 if GPU needed
# Add --requeue if using low partition
# Add --array=0-N if array job

set -euo pipefail

# Load modules
module load conda/latest
# Only load CUDA manually if the conda environment doesn't include it:
# module load cuda/12.6.2

# Activate environment
eval "$(conda shell.bash hook)"
conda activate <environment>

# Create logs directory
mkdir -p logs

# === YOUR COMMANDS HERE ===
```

**Key details:**
- Always use `#!/bin/bash --norc` shebang
- Always use `%A_%a` log format (works for both array and non-array jobs)
- Always include `set -euo pipefail` for safety
- Always create `logs/` directory

## Partition and Account Rules

### Decision logic (prefer `low` when possible — it's more efficient):

| Scenario | Partition | Account | Extra flags |
|----------|-----------|---------|-------------|
| **CPU job, not time-sensitive** | `low` | `publicgrp` | `--requeue` |
| **CPU job, needs >7 days or priority** | `high` | `jbsiegelgrp` | — |
| **GPU job, not time-sensitive** | `low` (with `--gres=gpu:1`) | `publicgrp` | `--requeue` |
| **GPU job, needs >7 days or priority** | `gpu-a100` | `genome-center-grp` | — |
| **GPU job, A100 specifically needed** | `gpu-a100` | `genome-center-grp` | — |
| **GPU job, A6000 specifically needed** | `gpu-a6000` | `genome-center-grp` | — |
| **GPU job, Blackwell needed** | `gpu-6000-blackwell` | `genome-center-grp` | — |

**Important:**
- `low` partition has a 7-day time limit. Jobs may be preempted — always use `--requeue`.
- `high` partition has a 30-day time limit.
- GPU partitions (`gpu-a100`, `gpu-a6000`, `gpu-6000-blackwell`) have 30-day limits.
- When using `low` with GPUs, you can get A100s, A6000s, or Blackwell GPUs depending on availability.

### Available GPU resources:
- **gpu-a100**: 3 nodes, 4-8 A100 GPUs per node
- **gpu-a6000**: 1 node, 4 A6000 GPUs
- **gpu-6000-blackwell**: 1 node, 4 Blackwell 6000 GPUs
- **low partition GPU nodes**: access to all of the above (preemptible)

### Node specs:
- CPU nodes: 64-128 cores, 100-200GB RAM
- GPU nodes: 128 cores, 100-230GB RAM

## Storage

- **Home directory**: 20GB limit. Do NOT put large files here.
- **Lab storage**: `/quobyte/jbsiegelgrp/`
- **Personal work**: `/quobyte/jbsiegelgrp/<username>/`
- **Shared software**: `/quobyte/jbsiegelgrp/software/`
- **Shared databases**: `/quobyte/jbsiegelgrp/databases/`
- **Shared conda envs**: `/quobyte/jbsiegelgrp/software/envs/`

### Cache directories (should be in quobyte, NOT home):
| Cache | Recommended path |
|-------|-----------------|
| Conda packages | `/quobyte/jbsiegelgrp/<user>/.conda/pkgs` |
| Conda environments | `/quobyte/jbsiegelgrp/<user>/.conda/envs` |
| Pip cache | `/quobyte/jbsiegelgrp/<user>/.cache/pip` |
| HuggingFace | `/quobyte/jbsiegelgrp/<user>/.cache/huggingface` |
| PyTorch | `/quobyte/jbsiegelgrp/<user>/.cache/torch` |

## Software Catalog

### Structure Prediction

| Tool | Path | Conda Env | GPU? | Notes |
|------|------|-----------|------|-------|
| **AlphaFold 3** | `/quobyte/jbsiegelgrp/software/alphafold3/` | N/A (container) | Yes | Uses apptainer/singularity. Container: `alphafold3.sif`. Weights: `af3.bin`. Databases: `public_databases/` |
| **AlphaFold 2 (ColabFold)** | `/quobyte/jbsiegelgrp/software/LocalColabFold/` | colabfold (system) | Yes | Local ColabFold installation |
| **Boltz** | `/quobyte/jbsiegelgrp/software/boltz/` | `/quobyte/jbsiegelgrp/software/envs/boltz` | Yes | Cache at `/quobyte/jbsiegelgrp/databases/boltz/cache` |
| **Chai** | `/quobyte/jbsiegelgrp/software/chai-lab/` | `/quobyte/jbsiegelgrp/software/envs/chai` | Yes | |
| **OpenFold 3** | `/quobyte/jbsiegelgrp/software/openfold-3/` | `/quobyte/jbsiegelgrp/software/envs/openfold-3` | Yes | |
| **ESM** | `/quobyte/jbsiegelgrp/software/esm/` | `/quobyte/jbsiegelgrp/software/envs/esm_env` | Yes | Protein language model |
| **ESMC** | `/quobyte/jbsiegelgrp/software/esmc/` | — | Yes | ESM-Cambrian |
| **AlphaFast** | `/quobyte/jbsiegelgrp/software/alphafast/` | — | Yes | Fast AF3 variant. Databases at `/quobyte/jbsiegelgrp/databases/alphafast/` |

### Protein Design

| Tool | Path | Conda Env | GPU? | Notes |
|------|------|-----------|------|-------|
| **RFdiffusion** | `/quobyte/jbsiegelgrp/software/RFdiffusion/` | `/quobyte/jbsiegelgrp/software/envs/SE3nv` | Yes | Also `RFdiffusion2/` for v2 |
| **LigandMPNN** | `/quobyte/jbsiegelgrp/software/LigandMPNN/` | `/quobyte/jbsiegelgrp/software/envs/ligandmpnn_env` | Yes | |
| **BindCraft** | `/quobyte/jbsiegelgrp/software/BindCraft/` | BindCraft (in software dir) | Yes | Binding site design |
| **dl_binder_design** | `/quobyte/jbsiegelgrp/software/dl_binder_design/` | — | Yes | Deep learning binder design |

### Docking & Scoring

| Tool | Path | Conda Env | GPU? | Notes |
|------|------|-----------|------|-------|
| **AutoDock-GPU** | `/quobyte/jbsiegelgrp/software/AutoDock-GPU/` | `/quobyte/jbsiegelgrp/software/envs/AutoDock-GPU` | Yes | GPU-accelerated docking |
| **DiffDock-PP** | `/quobyte/jbsiegelgrp/software/DiffDock-PP/` | — | Yes | Diffusion-based docking |
| **PLACER** | `/quobyte/jbsiegelgrp/software/PLACER/` | `/quobyte/jbsiegelgrp/software/envs/placer_env` | Yes | Binding site discovery |
| **HADDOCK3** | `/quobyte/jbsiegelgrp/software/haddock3/` | `/quobyte/jbsiegelgrp/software/envs/haddock3` | No | Protein-protein docking |
| **MaSIF** | `/quobyte/jbsiegelgrp/software/masif/` | `/quobyte/jbsiegelgrp/software/envs/masif_feat` | Yes | Surface-based analysis |

### Molecular Dynamics & Classical

| Tool | Path | Conda Env | GPU? | Notes |
|------|------|-----------|------|-------|
| **Rosetta (3.15)** | `/quobyte/jbsiegelgrp/software/rosetta_315/` | N/A | No | Binaries use `.static.linuxgccrelease` suffix |
| **Rosetta (3.14)** | `/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/` | N/A | No | Older version |
| **RoseTTAFold2** | `/quobyte/jbsiegelgrp/software/RoseTTAFold2/` | `/quobyte/jbsiegelgrp/software/envs/RF2` | Yes | |

### Other

| Tool | Path | Conda Env | GPU? | Notes |
|------|------|-----------|------|-------|
| **Foundry** | `/quobyte/jbsiegelgrp/software/foundry/` | `/quobyte/jbsiegelgrp/software/envs/foundry` | Yes | IPD foundation models |
| **BioNeMo** | `/quobyte/jbsiegelgrp/software/bionemo-framework/` | — | Yes | NVIDIA bio models |
| **EvolvePro** | `/quobyte/jbsiegelgrp/software/EvolvePro/` | — | Yes | Directed evolution |
| **Dayhoff** | `/quobyte/jbsiegelgrp/software/dayhoff/` | — | Yes | Sequence search |

## AlphaFold 3 Specifics

AF3 runs via apptainer container. The standard invocation pattern:

```bash
module load apptainer/latest

singularity exec \
    --bind "$JSON_DIR:/input" \
    --bind "$OUTPUT_DIR:/output" \
    --bind "/quobyte/jbsiegelgrp/software/alphafold3:/models" \
    --bind "/quobyte/jbsiegelgrp/software/alphafold3/public_databases:/databases" \
    --nv \
    /quobyte/jbsiegelgrp/software/alphafold3/alphafold3.sif \
    python /app/alphafold/run_alphafold.py \
    --json_path="/input/$JSON_FILE" \
    --model_dir=/models \
    --output_dir=/output \
    --db_dir=/databases
```

AF3 JSON input format:
```json
{
  "name": "protein_name",
  "modelSeeds": [1],
  "sequences": [
    {
      "protein": {
        "id": "A",
        "sequence": "MKTL..."
      }
    }
  ]
}
```
- Chain IDs MUST be uppercase letters (A, B, C, ...)
- Remove `-` characters from sequences

## Example Scripts Reference

The HiveTransition repo at `/quobyte/jbsiegelgrp/software/HiveTransition/` contains
vetted example scripts. When possible, reference or use these as the basis for wrappers:

- **Partitions**: `example_scripts/partitions/` — low, high, gbsf templates
- **AlphaFold 3**: `example_scripts/folding/alphafold3/` — single and bulk submission
- **AlphaFold 2**: `example_scripts/folding/alphafold2/` — ColabFold and initial guess
- **Boltz2**: `example_scripts/folding/boltz2/` — runners and format converters
- **Chai**: `example_scripts/folding/chai/` — with and without MSA
- **LigandMPNN**: `example_scripts/design/ligandmpnn/`
- **RFdiffusion**: `example_scripts/design/diffusion/`
- **GALigandDock**: `example_scripts/docking/galigand_dock/`
- **Relaxation**: `example_scripts/docking/relaxation/`

Full documentation for each tool is in `docs/` within that repo.

## Array Job Pattern

When running the same tool on multiple inputs:

```bash
#!/bin/bash --norc
# Generated with Siegel Lab HIVE Cluster Skill v1.0
#SBATCH --job-name=<tool>_array
#SBATCH --partition=<appropriate>
#SBATCH --account=<appropriate>
#SBATCH --array=0-N
#SBATCH --output=logs/<tool>_%A_%a.out
#SBATCH --error=logs/<tool>_%A_%a.err
# ... other SBATCH directives ...

set -euo pipefail
module load conda/latest
eval "$(conda shell.bash hook)"
conda activate <env>

# Build file list
FILES=(input_dir/*)
FILE=${FILES[$SLURM_ARRAY_TASK_ID]}

# Run tool on this file
<command> "$FILE"
```

For large arrays (>100 jobs), use `--array=0-N%20` to limit concurrent jobs to 20.

## Common Mistakes to Prevent

1. **Don't use `conda activate` without the eval hook** — it won't work in batch scripts.
2. **Don't forget `--account`** — jobs will fail or use wrong allocation.
3. **Don't put output in home directory** — 20GB fills up fast.
4. **Don't submit hundreds of individual jobs** — use array jobs.
5. **Don't copy and modify existing tool scripts** — write wrappers.
6. **Don't use `#!/bin/bash`** — use `#!/bin/bash --norc` to avoid sourcing user profiles that may conflict.
7. **Don't hardcode paths to other users' directories** — ask for the user's quobyte path.
8. **Don't forget `--requeue` on `low` partition** — jobs get preempted.
9. **Don't forget `--gres=gpu:1`** when requesting GPU partitions — you won't get a GPU without it.
10. **Don't request more GPUs than needed** — most tools only use 1 GPU.

## Modules

Available via the CVMFS module system:
```bash
module load conda/latest        # Always load this
module load cuda/12.6.2         # Only if the conda env doesn't already include CUDA
module load apptainer/latest    # For container jobs (AF3, etc.)
```

**Note on CUDA:** Most GPU conda environments already have CUDA bundled. Only `module load cuda/12.6.2`
if the user specifically asks for it or if you're using a tool/environment that doesn't include CUDA.

Other available modules: GCC, OpenMPI, Julia, Rust, Go, Java, etc. Use `module avail` to search.

## Containers

The cluster uses **apptainer** (also available as `singularity`):
- Binary: `/usr/bin/apptainer`
- Use `--nv` flag for GPU passthrough
- Use `--bind` for mounting directories into the container
- Lab containers stored in `/quobyte/jbsiegelgrp/software/apptainer_containers/`
