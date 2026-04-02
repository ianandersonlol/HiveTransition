#!/bin/bash --norc
#SBATCH --job-name=rfd3_design
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=logs/rfd3_%A_%a.out
#SBATCH --error=logs/rfd3_%A_%a.err

set -eo pipefail
mkdir -p logs

# --- Input validation ---
DESIGN_JSON="${1:-}"
OUTPUT_DIR="${2:-}"

if [[ -z "${DESIGN_JSON}" || -z "${OUTPUT_DIR}" ]]; then
    echo "Usage: sbatch submit_rfd3.sh <design_spec.json> <output_dir>"
    echo ""
    echo "  design_spec.json - RFD3 design specification (see example_design.json)"
    echo "  output_dir       - Directory for design output"
    exit 1
fi

if [[ ! -f "${DESIGN_JSON}" ]]; then
    echo "ERROR: Design spec file not found: ${DESIGN_JSON}"
    exit 1
fi

# --- Job info ---
echo "=== RFdiffusion3 Protein Design ==="
echo "Job ID:    ${SLURM_JOB_ID}"
echo "Hostname:  $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Input:     ${DESIGN_JSON}"
echo "Output:    ${OUTPUT_DIR}"
echo "Date:      $(date)"
echo "===================================="

# --- Environment setup ---
# NOTE: The RFD3 checkpoint must be installed before running. As of 2026-03-31,
# only the RF3 checkpoint is downloaded. To install the RFD3 checkpoint, run:
#   export FOUNDRY_CHECKPOINT_DIRS=/quobyte/jbsiegelgrp/databases/foundry
#   foundry install rfd3
export FOUNDRY_CHECKPOINT_DIRS=/quobyte/jbsiegelgrp/databases/foundry

module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/foundry

# Use Foundry source tree so Hydra finds config files correctly
FOUNDRY_DIR="/quobyte/jbsiegelgrp/software/foundry"
export PYTHONPATH="${FOUNDRY_DIR}/models/rfd3/src:${FOUNDRY_DIR}/src:${PYTHONPATH:-}"

# --- Run RFD3 ---
rfd3 design \
    out_dir="${OUTPUT_DIR}" \
    inputs="${DESIGN_JSON}"

echo ""
echo "RFD3 design complete: $(date)"
echo "Results in: ${OUTPUT_DIR}"
