#!/bin/bash --norc
#SBATCH --job-name=esm2_embed
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=2:00:00
#SBATCH --output=logs/esm2_embed_%A_%a.out
#SBATCH --error=logs/esm2_embed_%A_%a.err

set -eo pipefail
mkdir -p logs

###############################################################################
# ESM-2 embedding extraction
#
# Usage:
#   sbatch submit_esm2_embeddings.sh <input.fasta> <output_dir>
#
# Example:
#   sbatch submit_esm2_embeddings.sh input.fasta ./embeddings_output
###############################################################################

# --- Input validation --------------------------------------------------------
if [[ $# -lt 2 ]]; then
    echo "Usage: sbatch submit_esm2_embeddings.sh <input.fasta> <output_dir>"
    echo "  <input.fasta>  Path to a FASTA file with protein sequences"
    echo "  <output_dir>   Directory for output .pt tensor files"
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
echo "===== ESM-2 Embeddings Job Info ====="
echo "SLURM_JOB_ID:  ${SLURM_JOB_ID:-local}"
echo "Hostname:      $(hostname)"
echo "GPU:           $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Input FASTA:   ${INPUT_FASTA}"
echo "Output dir:    ${OUTPUT_DIR}"
echo "Date:          $(date)"
echo "======================================"

# --- Environment setup -------------------------------------------------------
module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/esm_env

# Use the local ESM source installation (not the pip-installed package)
export PYTHONPATH="/quobyte/jbsiegelgrp/software/esm:${PYTHONPATH:-}"

# --- Run ESM-2 extraction ----------------------------------------------------
python /quobyte/jbsiegelgrp/software/esm/scripts/extract.py \
    esm2_t33_650M_UR50D \
    "${INPUT_FASTA}" \
    "${OUTPUT_DIR}" \
    --repr_layers 0 32 33 \
    --include mean per_tok

echo "ESM-2 embedding extraction complete. Output in: ${OUTPUT_DIR}"
