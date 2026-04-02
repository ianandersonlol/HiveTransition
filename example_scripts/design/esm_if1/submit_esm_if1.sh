#!/bin/bash --norc
#SBATCH --job-name=esm_if1
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=2:00:00
#SBATCH --output=logs/esm_if1_%A_%a.out
#SBATCH --error=logs/esm_if1_%A_%a.err

set -eo pipefail
mkdir -p logs

###############################################################################
# ESM-IF1 inverse folding (sequence design from structure)
#
# Usage:
#   sbatch submit_esm_if1.sh <structure.pdb> <chain> <num_samples> <output.fasta>
#
# Example:
#   sbatch submit_esm_if1.sh input.pdb A 10 ./designed_sequences.fasta
#
# NOTE: This script requires torch_geometric to be installed in the conda env.
#       If you get an import error, install it with:
#         conda activate /quobyte/jbsiegelgrp/software/envs/esm_env
#         pip install torch_geometric
###############################################################################

# --- Input validation --------------------------------------------------------
if [[ $# -lt 4 ]]; then
    echo "Usage: sbatch submit_esm_if1.sh <structure.pdb> <chain> <num_samples> <output.fasta>"
    echo "  <structure.pdb>  Path to input PDB structure file"
    echo "  <chain>          Chain ID to design (e.g., A)"
    echo "  <num_samples>    Number of sequences to generate"
    echo "  <output.fasta>   Path for output designed sequences"
    exit 1
fi

INPUT_PDB="$1"
CHAIN="${2:-A}"
NUM_SAMPLES="${3:-10}"
OUTPUT_FASTA="$4"

if [[ ! -f "${INPUT_PDB}" ]]; then
    echo "ERROR: Input PDB file not found: ${INPUT_PDB}"
    exit 1
fi

mkdir -p "$(dirname "${OUTPUT_FASTA}")"

# --- Job info ----------------------------------------------------------------
echo "===== ESM-IF1 Inverse Folding Job Info ====="
echo "SLURM_JOB_ID:  ${SLURM_JOB_ID:-local}"
echo "Hostname:      $(hostname)"
echo "GPU:           $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Input PDB:     ${INPUT_PDB}"
echo "Chain:         ${CHAIN}"
echo "Num samples:   ${NUM_SAMPLES}"
echo "Output FASTA:  ${OUTPUT_FASTA}"
echo "Date:          $(date)"
echo "============================================="

# --- Environment setup -------------------------------------------------------
module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/esm_env

# Use the local ESM source installation (not the pip-installed package)
export PYTHONPATH="/quobyte/jbsiegelgrp/software/esm:${PYTHONPATH:-}"

# --- Run ESM-IF1 inverse folding ----------------------------------------------
python /quobyte/jbsiegelgrp/software/esm/examples/inverse_folding/sample_sequences.py \
    "${INPUT_PDB}" \
    --chain "${CHAIN}" \
    --temperature 1 \
    --num-samples "${NUM_SAMPLES}" \
    --outpath "${OUTPUT_FASTA}"

echo "ESM-IF1 inverse folding complete. Output in: ${OUTPUT_FASTA}"
