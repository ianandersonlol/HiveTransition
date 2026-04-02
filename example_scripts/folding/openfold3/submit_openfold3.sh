#!/bin/bash --norc
#SBATCH --job-name=openfold3
#SBATCH --account=genome-center-grp
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --output=logs/openfold3_%A_%a.out
#SBATCH --error=logs/openfold3_%A_%a.err

set -eo pipefail
mkdir -p logs

# ── Usage ──
if [[ $# -lt 2 ]]; then
    echo "Usage: sbatch submit_openfold3.sh <query.json> <output_dir>"
    echo ""
    echo "Arguments:"
    echo "  query.json   Path to OpenFold 3 JSON query file"
    echo "  output_dir   Directory to write prediction results"
    echo ""
    echo "Example:"
    echo "  sbatch submit_openfold3.sh example_input.json ./test_output"
    exit 1
fi

QUERY_JSON="$1"
OUTPUT_DIR="$2"

# ── Input validation ──
if [[ ! -f "$QUERY_JSON" ]]; then
    echo "ERROR: Query JSON file not found: $QUERY_JSON"
    exit 1
fi

# ── Job info ──
echo "============================================"
echo "OpenFold 3 Prediction"
echo "============================================"
echo "Job ID:    ${SLURM_JOB_ID:-local}"
echo "Host:      $(hostname)"
echo "GPU:       ${CUDA_VISIBLE_DEVICES:-not set}"
echo "Input:     $QUERY_JSON"
echo "Output:    $OUTPUT_DIR"
echo "Date:      $(date)"
echo "============================================"

# ── Environment setup ──
module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/openfold-3

export OPENFOLD_CACHE=/quobyte/jbsiegelgrp/software/.openfold3
export TRITON_CACHE_DIR=/tmp/${USER}/triton_cache
mkdir -p "$TRITON_CACHE_DIR"
mkdir -p "$OUTPUT_DIR"

# ── Run inference ──
echo "Starting OpenFold 3 prediction at $(date)"
run_openfold predict \
    --query-json "$QUERY_JSON" \
    --output-dir "$OUTPUT_DIR" \
    --use-msa-server true \
    --use-templates true \
    --num-diffusion-samples 5

echo "============================================"
echo "Done. Results saved to: $OUTPUT_DIR"
echo "Finished at $(date)"
echo "============================================"
