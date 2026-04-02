#!/bin/bash --norc
#SBATCH --job-name=placer
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH --output=logs/placer_%A_%a.out
#SBATCH --error=logs/placer_%A_%a.err

set -eo pipefail
mkdir -p logs

# --- Usage ---
# sbatch submit_placer.sh <protein.pdb|cif> <output_dir> [n_samples]
#
# Arguments:
#   protein.pdb|cif  - Input protein structure (PDB or CIF format)
#   output_dir       - Directory for PLACER output
#   n_samples        - Number of conformational samples (default: 50)
#
# Example:
#   sbatch submit_placer.sh /quobyte/jbsiegelgrp/software/PLACER/examples/inputs/3rgk.pdb ./test_output 10

# --- Input validation ---
if [[ $# -lt 2 ]]; then
    echo "Usage: sbatch submit_placer.sh <protein.pdb|cif> <output_dir> [n_samples]"
    echo ""
    echo "  protein.pdb|cif  Input protein structure file"
    echo "  output_dir       Output directory for results"
    echo "  n_samples        Number of samples (default: 50)"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_DIR="$2"
N_SAMPLES="${3:-50}"

if [[ ! -f "${INPUT_FILE}" ]]; then
    echo "ERROR: Input file not found: ${INPUT_FILE}"
    exit 1
fi

# --- Job info ---
echo "=== PLACER Job Info ==="
echo "Job ID:      ${SLURM_JOB_ID}"
echo "Hostname:    $(hostname)"
echo "GPU:         $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Input:       ${INPUT_FILE}"
echo "Output dir:  ${OUTPUT_DIR}"
echo "N samples:   ${N_SAMPLES}"
echo "Start time:  $(date)"
echo "======================"

# --- Setup conda ---
module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/placer_env

# Ensure scipy can find openblas shared library
export LD_LIBRARY_PATH="${CONDA_PREFIX}/lib:${LD_LIBRARY_PATH:-}"

# --- Create output directory ---
mkdir -p "${OUTPUT_DIR}"

# --- Run PLACER ---
python /quobyte/jbsiegelgrp/software/PLACER/run_PLACER.py \
    --ifile "${INPUT_FILE}" \
    --odir "${OUTPUT_DIR}" \
    -n "${N_SAMPLES}" \
    --rerank prmsd

echo ""
echo "=== PLACER Complete ==="
echo "End time: $(date)"
echo "Output:   ${OUTPUT_DIR}"
ls -lh "${OUTPUT_DIR}/"
