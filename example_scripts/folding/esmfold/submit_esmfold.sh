#!/bin/bash --norc
#SBATCH --job-name=esmfold
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=4:00:00
#SBATCH --output=logs/esmfold_%A_%a.out
#SBATCH --error=logs/esmfold_%A_%a.err

set -eo pipefail
mkdir -p logs

###############################################################################
# ESMFold structure prediction
#
# Usage:
#   sbatch submit_esmfold.sh <input.fasta> <output_dir>
#
# Example:
#   sbatch submit_esmfold.sh example_input.fasta ./test_output
###############################################################################

# --- Input validation --------------------------------------------------------
if [[ $# -lt 2 ]]; then
    echo "Usage: sbatch submit_esmfold.sh <input.fasta> <output_dir>"
    echo "  <input.fasta>  Path to a FASTA file with protein sequences"
    echo "  <output_dir>   Directory for output PDB files"
    exit 1
fi

INPUT_FASTA="$1"
OUTPUT_DIR="$2"

if [[ ! -f "${INPUT_FASTA}" ]]; then
    echo "ERROR: Input file not found: ${INPUT_FASTA}"
    exit 1
fi

mkdir -p "${OUTPUT_DIR}"

# --- Job info ----------------------------------------------------------------
echo "===== ESMFold Job Info ====="
echo "SLURM_JOB_ID:  ${SLURM_JOB_ID:-local}"
echo "Hostname:      $(hostname)"
echo "GPU:           $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Input FASTA:   ${INPUT_FASTA}"
echo "Output dir:    ${OUTPUT_DIR}"
echo "Date:          $(date)"
echo "==========================="

# --- Environment setup -------------------------------------------------------
module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/esmfold

# Use local ESM source + openfold-v1 (compatible model weights)
ESM_DIR="/quobyte/jbsiegelgrp/software/esm"
OPENFOLD_DIR="/quobyte/jbsiegelgrp/software/openfold-v1"
export PYTHONPATH="${ESM_DIR}:${OPENFOLD_DIR}:${PYTHONPATH:-}"

# --- Run ESMFold --------------------------------------------------------------
# Patch openfold's CUDA attention kernel, then run fold.py
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python -c "
import sys, os
sys.path.insert(0, '${SCRIPT_DIR}')
import patch_attention  # patches openfold before esm imports it
sys.argv = ['fold.py', '-i', '${INPUT_FASTA}', '-o', '${OUTPUT_DIR}', '--num-recycles', '4']
exec(open('${ESM_DIR}/scripts/fold.py').read())
"

echo "ESMFold complete. Output in: ${OUTPUT_DIR}"
