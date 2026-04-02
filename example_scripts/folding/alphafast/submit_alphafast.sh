#!/bin/bash --norc
#SBATCH --partition=low
#SBATCH --account=publicgrp
#SBATCH --constraint="gpu:a100|gpu:6000_blackwell"
#SBATCH --gres=gpu:4
#SBATCH --requeue
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --job-name=alphafast
#SBATCH --output=logs/alphafast_%A_%a.out
#SBATCH --error=logs/alphafast_%A_%a.err

# ============================================================================
# AlphaFast structure prediction on HIVE (Singularity/Apptainer container)
#
# NOTE: Requires >=80GB GPU VRAM for MMseqs2 GPU-accelerated database search.
#       A6000 (48GB) will OOM on large databases (uniprot, mgnify).
#       The constraint flag ensures we get A100 or Blackwell GPUs.
#
# Usage:
#   sbatch submit_alphafast.sh <input_dir> <output_dir>
#
# Arguments:
#   input_dir   - Directory containing AlphaFold 3 dialect JSON input files
#   output_dir  - Directory where prediction results will be written
#
# Example:
#   sbatch submit_alphafast.sh ./example_inputs ./test_output
# ============================================================================

set -eo pipefail
mkdir -p logs

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
if [ $# -ne 2 ]; then
    echo "Usage: sbatch $0 <input_dir> <output_dir>"
    echo ""
    echo "  input_dir   Directory containing .json input files (AF3 dialect)"
    echo "  output_dir  Directory for prediction output"
    echo ""
    echo "Example:"
    echo "  sbatch $0 ./example_inputs ./test_output"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"

if [ ! -d "$INPUT_DIR" ]; then
    echo "ERROR: Input directory does not exist: $INPUT_DIR"
    exit 1
fi

JSON_COUNT=$(find "$INPUT_DIR" -maxdepth 1 -name "*.json" -type f | wc -l)
if [ "$JSON_COUNT" -eq 0 ]; then
    echo "ERROR: No .json files found in $INPUT_DIR"
    exit 1
fi

# Convert to absolute paths
INPUT_DIR="$(cd "$INPUT_DIR" && pwd)"
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ALPHAFAST_DIR="/quobyte/jbsiegelgrp/software/alphafast"
DB_DIR="/quobyte/jbsiegelgrp/databases/alphafast"
WEIGHTS_DIR="/quobyte/jbsiegelgrp/software/alphafold3"
CONTAINER="${ALPHAFAST_DIR}/alphafast.sif"
ORCHESTRATION_SCRIPT="${ALPHAFAST_DIR}/scripts/run_alphafast.sh"

# ---------------------------------------------------------------------------
# Verify critical paths exist
# ---------------------------------------------------------------------------
for CHECK_PATH in "$CONTAINER" "$DB_DIR" "$DB_DIR/mmseqs" "$WEIGHTS_DIR"; do
    if [ ! -e "$CHECK_PATH" ]; then
        echo "ERROR: Required path not found: $CHECK_PATH"
        exit 1
    fi
done

if [ ! -f "${WEIGHTS_DIR}/af3.bin.zst" ] && [ ! -f "${WEIGHTS_DIR}/af3.bin" ]; then
    echo "ERROR: Model weights (af3.bin.zst or af3.bin) not found in $WEIGHTS_DIR"
    exit 1
fi

# ---------------------------------------------------------------------------
# Job info
# ---------------------------------------------------------------------------
echo "=========================================="
echo "AlphaFast Structure Prediction"
echo "=========================================="
echo "SLURM Job ID:  ${SLURM_JOB_ID:-N/A}"
echo "Hostname:      $(hostname)"
echo "GPU:           $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'unavailable')"
echo "Input dir:     $INPUT_DIR"
echo "Output dir:    $OUTPUT_DIR"
echo "JSON files:    $JSON_COUNT"
echo "Container:     $CONTAINER"
echo "Weights dir:   $WEIGHTS_DIR"
echo "Database dir:  $DB_DIR"
echo "Start time:    $(date)"
echo "=========================================="
echo ""

# ---------------------------------------------------------------------------
# Load modules
# ---------------------------------------------------------------------------
module load apptainer/latest

# ---------------------------------------------------------------------------
# Run AlphaFast via orchestration script
# ---------------------------------------------------------------------------
# The orchestration script handles the two-stage pipeline:
#   Stage 1: Data pipeline (MSA search via MMseqs2)
#   Stage 2: Structure inference (AlphaFold model)

if [ -x "$ORCHESTRATION_SCRIPT" ]; then
    echo "Using orchestration script: $ORCHESTRATION_SCRIPT"
    echo ""

    "$ORCHESTRATION_SCRIPT" \
        --input_dir "$INPUT_DIR" \
        --output_dir "$OUTPUT_DIR" \
        --db_dir "$DB_DIR" \
        --weights_dir "$WEIGHTS_DIR" \
        --container "$CONTAINER" \
        --backend singularity \
        --num_gpus 4 \
        --gpu_devices 0,1,2,3
else
    echo "WARNING: Orchestration script not found or not executable."
    echo "Falling back to direct apptainer invocation."
    echo ""

    # Process each JSON file individually
    for json_file in "$INPUT_DIR"/*.json; do
        JSON_NAME=$(basename "$json_file")
        BASE_NAME="${JSON_NAME%.json}"

        echo "Processing: $JSON_NAME"

        PROTEIN_OUTPUT_DIR="${OUTPUT_DIR}/${BASE_NAME}"
        mkdir -p "$PROTEIN_OUTPUT_DIR"

        apptainer exec --nv \
            --bind /quobyte:/quobyte \
            "$CONTAINER" \
            python "${ALPHAFAST_DIR}/run_alphafold.py" \
            --json_path="$json_file" \
            --output_dir="$PROTEIN_OUTPUT_DIR" \
            --mmseqs_db_dir="${DB_DIR}/mmseqs" \
            --mmseqs_sequential

        echo "Completed: $JSON_NAME"
        echo ""
    done
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "AlphaFast Run Complete"
echo "=========================================="
echo "End time:   $(date)"
echo "Output dir: $OUTPUT_DIR"
echo ""
echo "Output files:"
find "$OUTPUT_DIR" -type f -name "*.cif" -o -name "*.pdb" -o -name "*.json" 2>/dev/null | head -20 || true
echo "=========================================="
