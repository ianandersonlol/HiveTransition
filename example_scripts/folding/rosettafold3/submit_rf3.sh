#!/bin/bash --norc
#SBATCH --job-name=rf3_fold
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --output=logs/rf3_%A_%a.out
#SBATCH --error=logs/rf3_%A_%a.err

set -eo pipefail
mkdir -p logs

# --- Input validation ---
INPUT_JSON="${1:-}"
OUTPUT_DIR="${2:-}"

if [[ -z "${INPUT_JSON}" || -z "${OUTPUT_DIR}" ]]; then
    echo "Usage: sbatch submit_rf3.sh <input.json> <output_dir>"
    echo ""
    echo "  input.json  - RF3 input specification (see example_input.json)"
    echo "  output_dir  - Directory for prediction output"
    exit 1
fi

if [[ ! -f "${INPUT_JSON}" ]]; then
    echo "ERROR: Input file not found: ${INPUT_JSON}"
    exit 1
fi

# --- Job info ---
echo "=== RoseTTAFold3 Structure Prediction ==="
echo "Job ID:    ${SLURM_JOB_ID}"
echo "Hostname:  $(hostname)"
echo "GPU:       $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Input:     ${INPUT_JSON}"
echo "Output:    ${OUTPUT_DIR}"
echo "Date:      $(date)"
echo "=========================================="

# --- Environment setup ---
export FOUNDRY_CHECKPOINT_DIRS=/quobyte/jbsiegelgrp/databases/foundry

module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/foundry

# Use Foundry source tree so Hydra finds config files correctly
FOUNDRY_DIR="/quobyte/jbsiegelgrp/software/foundry"
export PYTHONPATH="${FOUNDRY_DIR}/models/rf3/src:${FOUNDRY_DIR}/src:${PYTHONPATH:-}"

# --- Run RF3 ---
# Symlink checkpoint to default location if not present
CKPT_SRC="/quobyte/jbsiegelgrp/databases/foundry/rf3_foundry_01_24_latest_remapped.ckpt"
CKPT_DST="${HOME}/.foundry/checkpoints/rf3_foundry_01_24_latest_remapped.ckpt"
mkdir -p "${HOME}/.foundry/checkpoints"
if [[ ! -f "${CKPT_DST}" && -f "${CKPT_SRC}" ]]; then
    ln -sf "${CKPT_SRC}" "${CKPT_DST}"
fi

python -m rf3.cli fold \
    inputs="${INPUT_JSON}" \
    out_dir="${OUTPUT_DIR}"

echo ""
echo "RF3 prediction complete: $(date)"
echo "Results in: ${OUTPUT_DIR}"
