#!/bin/bash --norc
#SBATCH --job-name=bindcraft
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=48:00:00
#SBATCH --output=logs/bindcraft_%A_%a.out
#SBATCH --error=logs/bindcraft_%A_%a.err

set -eo pipefail
mkdir -p logs

###############################################################################
# BindCraft binder design on HIVE
#
# Usage:
#   sbatch submit_bindcraft.sh <target_settings.json> [filter_settings.json] [advanced_settings.json]
#
# Arguments:
#   target_settings.json   - Required. Path to target settings JSON.
#   filter_settings.json   - Optional. Defaults to BindCraft's default_filters.json.
#   advanced_settings.json - Optional. Defaults to BindCraft's default_4stage_multimer.json.
#
# Example:
#   sbatch submit_bindcraft.sh example_target.json
###############################################################################

BINDCRAFT_DIR="/quobyte/jbsiegelgrp/software/BindCraft"

# --- Input validation ---
TARGET_SETTINGS="${1:-}"
FILTER_SETTINGS="${2:-${BINDCRAFT_DIR}/settings_filters/default_filters.json}"
ADVANCED_SETTINGS="${3:-${BINDCRAFT_DIR}/settings_advanced/default_4stage_multimer.json}"

if [[ -z "${TARGET_SETTINGS}" ]]; then
    echo "ERROR: target settings JSON is required."
    echo ""
    echo "Usage: sbatch submit_bindcraft.sh <target_settings.json> [filter_settings.json] [advanced_settings.json]"
    exit 1
fi

if [[ ! -f "${TARGET_SETTINGS}" ]]; then
    echo "ERROR: target settings file not found: ${TARGET_SETTINGS}"
    exit 1
fi

if [[ ! -f "${FILTER_SETTINGS}" ]]; then
    echo "ERROR: filter settings file not found: ${FILTER_SETTINGS}"
    exit 1
fi

if [[ ! -f "${ADVANCED_SETTINGS}" ]]; then
    echo "ERROR: advanced settings file not found: ${ADVANCED_SETTINGS}"
    exit 1
fi

# --- Job info ---
echo "========================================"
echo "BindCraft Binder Design"
echo "========================================"
echo "SLURM_JOB_ID:    ${SLURM_JOB_ID}"
echo "Hostname:        $(hostname)"
echo "GPU:             $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Date:            $(date)"
echo ""
echo "Target settings:   ${TARGET_SETTINGS}"
echo "Filter settings:   ${FILTER_SETTINGS}"
echo "Advanced settings: ${ADVANCED_SETTINGS}"
echo "========================================"

# --- Activate conda environment ---
module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/BindCraft

# Export LD_LIBRARY_PATH for JAX/CUDA
export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${LD_LIBRARY_PATH:-}"

# NOTE: If JAX falls back to CPU, the CUDA JAX plugin may need to be installed:
#   conda activate /quobyte/jbsiegelgrp/software/envs/BindCraft
#   pip install jax[cuda12]

# --- Run BindCraft ---
cd "${BINDCRAFT_DIR}"

python -u "${BINDCRAFT_DIR}/bindcraft.py" \
    --settings "${TARGET_SETTINGS}" \
    --filters "${FILTER_SETTINGS}" \
    --advanced "${ADVANCED_SETTINGS}"

echo ""
echo "BindCraft finished at $(date)"
