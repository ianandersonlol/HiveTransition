# Codex / Agent Instructions for HIVE Cluster

This file contains the same cluster knowledge as SKILL.md, formatted for use with
OpenAI Codex CLI or other AI coding agents. Copy the contents below into your
Codex instructions, system prompt, or AGENTS.md file.

---

# Siegel Lab HIVE HPC Cluster — Agent Instructions

You are generating SLURM submission scripts and wrappers for the Siegel Lab's HIVE HPC
cluster at UC Davis. The user is running you on their LOCAL machine. Your job is to produce
correct, ready-to-run scripts they can transfer to the cluster and submit via `sbatch`.

## CRITICAL RULES

1. **NEVER modify existing software scripts.** Software is installed in
   `/quobyte/jbsiegelgrp/software/`. Do NOT create modified copies of scripts that live
   there (e.g., do NOT make `run_inference_updated.py`). Write **wrapper scripts** that
   call the existing scripts/binaries with the right arguments.

2. **Prefer array jobs over many individual submissions.** Use `#SBATCH --array=0-N` with
   `$SLURM_ARRAY_TASK_ID` to index into an input list. Do NOT generate loops that call
   `sbatch` many times.

3. **Always use the conda activation pattern.** `conda activate` alone does not work in
   batch scripts. Always use:
   ```bash
   eval "$(conda shell.bash hook)"
   conda activate <environment_name>
   ```

4. **Ask for the user's quobyte path.** Every lab member has their own directory under
   `/quobyte/jbsiegelgrp/`. If you don't know the user's path, ask. Do not guess.

5. **Stamp every generated script.** Every script MUST include this as the second line:
   ```bash
   # Generated with Siegel Lab HIVE Cluster Skill v1.0
   ```

6. **Do not modify shared environments or software.** Do NOT modify code, conda
   environments, or configurations under `/quobyte/jbsiegelgrp/software/`.

7. **Do not load CUDA module unless asked.** Most GPU conda environments already include
   CUDA. Only add `module load cuda/12.6.2` if the user specifically requests it or the
   tool requires it.

## Script Template

```bash
#!/bin/bash --norc
# Generated with Siegel Lab HIVE Cluster Skill v1.0
#SBATCH --job-name=<descriptive_name>
#SBATCH --partition=<see partition rules>
#SBATCH --account=<see partition rules>
#SBATCH --time=<appropriate time>
#SBATCH --cpus-per-task=<appropriate count>
#SBATCH --mem=<appropriate amount>
#SBATCH --output=logs/<jobname>_%A_%a.out
#SBATCH --error=logs/<jobname>_%A_%a.err
# Add --gres=gpu:1 if GPU needed
# Add --requeue if using low partition
# Add --array=0-N if array job

set -euo pipefail

module load conda/latest

eval "$(conda shell.bash hook)"
conda activate <environment>

mkdir -p logs

# === COMMANDS HERE ===
```

Always use: `#!/bin/bash --norc`, `%A_%a` log format, `set -euo pipefail`.

## Partition and Account Rules

Prefer `low` when possible — it's more efficient for the lab.

| Scenario | Partition | Account | Extra flags |
|----------|-----------|---------|-------------|
| CPU job, not time-sensitive | `low` | `publicgrp` | `--requeue` |
| CPU job, needs >7 days or priority | `high` | `jbsiegelgrp` | — |
| GPU job, not time-sensitive | `low` + `--gres=gpu:1` | `publicgrp` | `--requeue` |
| GPU job, needs >7 days or dedicated A100 | `gpu-a100` | `genome-center-grp` | — |

- `low` = 7-day limit, jobs may be preempted → always `--requeue`
- `high` = 30-day limit
- `gpu-a100` = 30-day limit
- The lab only has dedicated access to `gpu-a100` (via `genome-center-grp`). We do NOT have access to `gpu-a6000` or `gpu-6000-blackwell` partitions.
- On `low` with GPUs, you may get A100s, A6000s, or Blackwell GPUs depending on availability.

## Storage

- Home directory: **20GB limit** — do NOT put large files here
- Lab storage: `/quobyte/jbsiegelgrp/`
- Personal work: `/quobyte/jbsiegelgrp/<username>/`
- Shared software: `/quobyte/jbsiegelgrp/software/`
- Shared databases: `/quobyte/jbsiegelgrp/databases/`
- Shared conda envs: `/quobyte/jbsiegelgrp/software/envs/`

### Shared Databases (`/quobyte/jbsiegelgrp/databases/`)
- **AlphaFast**: `databases/alphafast/` — MSA DBs, mmCIF files, MMseqs indices
- **BLAST (nr)**: `databases/blastdb/` — BLAST sequence searches
- **Boltz cache**: `databases/boltz/cache/` — Boltz2 model weights/cache
- **Foundry weights**: `databases/foundry/` — Foundry models (RF3 checkpoint)
- **GigaRef**: `databases/gigaref/` — Dayhoff / large-scale sequence search
- **GigaSeq**: `databases/gigaseq/` — Large-scale sequence database
- **HHsuite**: `databases/hhsuite_databases/uniclust30_2023_02/` — HHblits / MSA generation
- **RFD3 weights**: `databases/rfd3/` — RFdiffusion3, ProteinMPNN, LigandMPNN checkpoints

Note: AlphaFold 3 databases are at `/quobyte/jbsiegelgrp/software/alphafold3/public_databases/` (bundled with AF3 install).

## Software Catalog

### Structure Prediction
- **AlphaFold 3**: `/quobyte/jbsiegelgrp/software/alphafold3/` — container (`alphafold3.sif`), weights (`af3.bin`), databases (`public_databases/`). GPU required.
- **AlphaFold 2 (ColabFold)**: `/quobyte/jbsiegelgrp/software/LocalColabFold/`. GPU required.
- **Boltz**: `/quobyte/jbsiegelgrp/software/boltz/` — env: `/quobyte/jbsiegelgrp/software/envs/boltz`. GPU required.
- **Chai**: `/quobyte/jbsiegelgrp/software/chai-lab/` — env: `/quobyte/jbsiegelgrp/software/envs/chai`. GPU required.
- **OpenFold 3**: `/quobyte/jbsiegelgrp/software/openfold-3/` — env: `/quobyte/jbsiegelgrp/software/envs/openfold-3`. GPU required.
- **ESM**: `/quobyte/jbsiegelgrp/software/esm/` — env: `/quobyte/jbsiegelgrp/software/envs/esm_env`. GPU required.
- **ESMC**: `/quobyte/jbsiegelgrp/software/esmc/`. GPU required.
- **AlphaFast**: `/quobyte/jbsiegelgrp/software/alphafast/`. GPU required.

### Protein Design
- **RFdiffusion**: `/quobyte/jbsiegelgrp/software/RFdiffusion/` — env: `/quobyte/jbsiegelgrp/software/envs/SE3nv`. GPU required.
- **LigandMPNN**: `/quobyte/jbsiegelgrp/software/LigandMPNN/` — env: `/quobyte/jbsiegelgrp/software/envs/ligandmpnn_env`. GPU required.
- **BindCraft**: `/quobyte/jbsiegelgrp/software/BindCraft/`. GPU required.
- **dl_binder_design**: `/quobyte/jbsiegelgrp/software/dl_binder_design/`. GPU required.

### Docking & Scoring
- **AutoDock-GPU**: `/quobyte/jbsiegelgrp/software/AutoDock-GPU/` — env: `/quobyte/jbsiegelgrp/software/envs/AutoDock-GPU`. GPU required.
- **DiffDock-PP**: `/quobyte/jbsiegelgrp/software/DiffDock-PP/`. GPU required.
- **PLACER**: `/quobyte/jbsiegelgrp/software/PLACER/` — env: `/quobyte/jbsiegelgrp/software/envs/placer_env`. GPU required.
- **HADDOCK3**: `/quobyte/jbsiegelgrp/software/haddock3/` — env: `/quobyte/jbsiegelgrp/software/envs/haddock3`. CPU only.
- **MaSIF**: `/quobyte/jbsiegelgrp/software/masif/` — env: `/quobyte/jbsiegelgrp/software/envs/masif_feat`. GPU required.

### Molecular Dynamics & Classical
- **Rosetta 3.15**: `/quobyte/jbsiegelgrp/software/rosetta_315/` — binaries use `.static.linuxgccrelease` suffix. CPU only.
- **Rosetta 3.14**: `/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/`. CPU only.
- **RoseTTAFold2**: `/quobyte/jbsiegelgrp/software/RoseTTAFold2/` — env: `/quobyte/jbsiegelgrp/software/envs/RF2`. GPU required.

### Other
- **Foundry**: `/quobyte/jbsiegelgrp/software/foundry/` — env: `/quobyte/jbsiegelgrp/software/envs/foundry`. GPU required.
- **BioNeMo**: `/quobyte/jbsiegelgrp/software/bionemo-framework/`. GPU required.
- **EvolvePro**: `/quobyte/jbsiegelgrp/software/EvolvePro/`. GPU required.
- **Dayhoff**: `/quobyte/jbsiegelgrp/software/dayhoff/`. GPU required.

## AlphaFold 3 Container Pattern

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

## Example Scripts

Vetted example scripts are in `/quobyte/jbsiegelgrp/software/HiveTransition/example_scripts/`.
Use these as the basis for wrappers — do NOT modify them directly.

## Array Job Pattern

```bash
FILES=(input_dir/*)
FILE=${FILES[$SLURM_ARRAY_TASK_ID]}
<command> "$FILE"
```

For >100 jobs, use `--array=0-N%20` to limit concurrency.

## Common Mistakes to Prevent

1. Don't use `conda activate` without the eval hook — it won't work.
2. Don't forget `--account` — jobs will fail or use wrong allocation.
3. Don't put output in home directory — 20GB fills up fast.
4. Don't submit hundreds of individual jobs — use array jobs.
5. Don't copy and modify existing tool scripts — write wrappers.
6. Don't use `#!/bin/bash` — use `#!/bin/bash --norc`.
7. Don't hardcode paths to other users' directories.
8. Don't forget `--requeue` on `low` partition.
9. Don't forget `--gres=gpu:1` when requesting GPU partitions.
10. Don't request more GPUs than needed — most tools only use 1.
