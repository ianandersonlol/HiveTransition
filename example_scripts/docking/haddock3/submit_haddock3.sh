#!/bin/bash --norc
#SBATCH --job-name=haddock3
#SBATCH --partition=high
#SBATCH --account=jbsiegelgrp
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=logs/haddock3_%A_%a.out
#SBATCH --error=logs/haddock3_%A_%a.err

set -eo pipefail
mkdir -p logs

# ---------------------------------------------------------------------------
# Usage: sbatch submit_haddock3.sh <config.cfg>
# ---------------------------------------------------------------------------
CONFIG="${1:-}"

if [[ -z "${CONFIG}" ]]; then
    echo "Usage: sbatch submit_haddock3.sh <config.cfg>"
    echo "  config.cfg  Path to a HADDOCK3 configuration file"
    exit 1
fi

if [[ ! -f "${CONFIG}" ]]; then
    echo "ERROR: Config file not found: ${CONFIG}"
    exit 1
fi

# Print job info
echo "============================================"
echo "HADDOCK3 docking job"
echo "============================================"
echo "SLURM_JOB_ID  : ${SLURM_JOB_ID}"
echo "Hostname      : $(hostname)"
echo "Date          : $(date)"
echo "Config file   : ${CONFIG}"
echo "Working dir   : $(pwd)"
echo "CPUs per task : ${SLURM_CPUS_PER_TASK}"
echo "============================================"

# Activate HADDOCK3 conda environment
module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/haddock3

echo "Python: $(which python)"
echo "haddock3: $(which haddock3)"
echo ""

# Run HADDOCK3
haddock3 "${CONFIG}"

echo ""
echo "HADDOCK3 finished successfully at $(date)"
