#!/bin/bash --norc
#SBATCH --job-name=disco_design
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=logs/disco_%A_%a.out
#SBATCH --error=logs/disco_%A_%a.err

# Usage: sbatch submit_disco.sh <input_json> <output_dir> [experiment] [num_seeds]
#
# Arguments:
#   input_json  - Path to DISCO input JSON (see examples in DISCO/input_jsons/)
#   output_dir  - Directory for generated PDBs and sequences
#   experiment  - Preset: "designable" (default) or "diverse"
#   num_seeds   - Number of samples per job (default: 5)
#
# Examples:
#   # Unconditional protein generation (5 samples per length)
#   sbatch submit_disco.sh input_jsons/unconditional_config.json ./output
#
#   # Ligand-conditioned design with diverse preset and 10 seeds
#   sbatch submit_disco.sh input_jsons/heme_b.json ./heme_output diverse 10
#
#   # DNA-conditioned design
#   sbatch submit_disco.sh input_jsons/7S03_dna.json ./dna_output diverse
#
# Notes:
#   - For unconditional generation, experiment=designable + effort=fast (default) is fine.
#   - For conditional generation (ligand/DNA/RNA), use experiment=diverse and the
#     script automatically sets effort=max for best quality.
#   - First run may be slow due to JIT kernel compilation and model download from HuggingFace.
#   - To enable DeepSpeed EvoformerAttention (lower VRAM), set up CUTLASS:
#       git clone https://github.com/NVIDIA/cutlass.git /quobyte/jbsiegelgrp/software/cutlass
#     and uncomment the CUTLASS_PATH export below.

set -eo pipefail
mkdir -p logs

# --- Input validation ---
INPUT_JSON="${1:-}"
OUTPUT_DIR="${2:-}"
EXPERIMENT="${3:-designable}"
NUM_SEEDS="${4:-5}"

if [[ -z "${INPUT_JSON}" || -z "${OUTPUT_DIR}" ]]; then
    echo "Usage: sbatch submit_disco.sh <input_json> <output_dir> [experiment] [num_seeds]"
    echo ""
    echo "  input_json  - DISCO input JSON file"
    echo "  output_dir  - Output directory for PDBs and sequences"
    echo "  experiment  - 'designable' (default) or 'diverse'"
    echo "  num_seeds   - Number of samples per job (default: 5)"
    exit 1
fi

if [[ ! -f "${INPUT_JSON}" ]]; then
    echo "ERROR: Input JSON not found: ${INPUT_JSON}"
    exit 1
fi

# --- Job info ---
echo "=== DISCO Protein Design ==="
echo "Job ID:      ${SLURM_JOB_ID}"
echo "Hostname:    $(hostname)"
echo "GPU:         $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'N/A')"
echo "Input JSON:  ${INPUT_JSON}"
echo "Output dir:  ${OUTPUT_DIR}"
echo "Experiment:  ${EXPERIMENT}"
echo "Num seeds:   ${NUM_SEEDS}"
echo "Date:        $(date)"
echo "============================="

# --- Environment setup ---
DISCO_DIR="/quobyte/jbsiegelgrp/software/DISCO"
export CUDA_HOME=/quobyte/jbsiegelgrp/software/envs/DISCO

# Uncomment if CUTLASS is installed (enables memory-efficient attention):
# export CUTLASS_PATH=/quobyte/jbsiegelgrp/software/cutlass

module load conda/latest
eval "$(conda shell.bash hook)"
source "${DISCO_DIR}/.venv/bin/activate"

# --- Build seed list ---
SEEDS=$(seq -s "," 0 $((NUM_SEEDS - 1)))

# --- Determine effort level ---
# Use effort=max for conditional generation, effort=fast for unconditional
if [[ "${EXPERIMENT}" == "diverse" ]]; then
    EFFORT="max"
else
    EFFORT="fast"
fi

# --- Determine whether to use DeepSpeed EvoformerAttention ---
DS_EVO_FLAG=""
if [[ -z "${CUTLASS_PATH:-}" ]]; then
    DS_EVO_FLAG="use_deepspeed_evo_attention=false"
fi

# --- Create output directory ---
mkdir -p "${OUTPUT_DIR}"

# --- Start background GPU monitoring ---
LOGS_DIR="$(dirname "${OUTPUT_DIR}")/logs"
mkdir -p "${LOGS_DIR}"
(
    while true; do
        nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv,noheader >> "${LOGS_DIR}/disco_gpu_monitor_${SLURM_JOB_ID}.csv" 2>/dev/null
        sleep 5
    done
) &
MONITOR_PID=$!

START_TIME=$(date +%s)

# --- Run DISCO ---
cd "${DISCO_DIR}"
python runner/inference.py \
    experiment="${EXPERIMENT}" \
    effort="${EFFORT}" \
    input_json_path="${INPUT_JSON}" \
    dump_dir="${OUTPUT_DIR}" \
    seeds=\[${SEEDS}\] \
    ${DS_EVO_FLAG}

# --- Cleanup and reporting ---
kill $MONITOR_PID 2>/dev/null || true

END_TIME=$(date +%s)
RUNTIME=$((END_TIME - START_TIME))
HOURS=$((RUNTIME / 3600))
MINUTES=$(( (RUNTIME % 3600) / 60 ))
SECONDS_LEFT=$((RUNTIME % 60))

echo ""
echo "DISCO design completed at $(date)"
echo "Total runtime: ${HOURS}h ${MINUTES}m ${SECONDS_LEFT}s"

# Analyze GPU usage from monitoring data
if [ -f "${LOGS_DIR}/disco_gpu_monitor_${SLURM_JOB_ID}.csv" ]; then
    echo ""
    echo "=== Resource Usage Summary ==="

    PEAK_VRAM=$(awk -F', ' '{gsub(" MiB","",$3); if($3>max) max=$3} END {printf "%.1f", max/1024}' "${LOGS_DIR}/disco_gpu_monitor_${SLURM_JOB_ID}.csv" 2>/dev/null || echo "N/A")
    TOTAL_VRAM=$(awk -F', ' 'NR==1 {gsub(" MiB","",$4); printf "%.1f", $4/1024}' "${LOGS_DIR}/disco_gpu_monitor_${SLURM_JOB_ID}.csv" 2>/dev/null || echo "N/A")
    AVG_GPU_UTIL=$(awk -F', ' '{gsub(" %","",$5); sum+=$5; count++} END {if(count>0) printf "%.1f", sum/count; else print "N/A"}' "${LOGS_DIR}/disco_gpu_monitor_${SLURM_JOB_ID}.csv" 2>/dev/null || echo "N/A")
    GPU_NAME=$(awk -F', ' 'NR==1 {print $2}' "${LOGS_DIR}/disco_gpu_monitor_${SLURM_JOB_ID}.csv" 2>/dev/null || echo "Unknown")

    echo "GPU: ${GPU_NAME}"
    echo "Peak VRAM usage: ${PEAK_VRAM} GB / ${TOTAL_VRAM} GB"
    echo "Average GPU utilization: ${AVG_GPU_UTIL}%"

    echo ""
    echo "CPU/Memory efficiency (from SLURM):"
    seff ${SLURM_JOB_ID} 2>/dev/null | grep -E "(CPU Efficiency|Memory Efficiency|Memory Utilized)" || echo "Unable to retrieve SLURM efficiency data"

    echo "=============================="

    rm -f "${LOGS_DIR}/disco_gpu_monitor_${SLURM_JOB_ID}.csv"
fi

echo ""
echo "Output files:"
ls -la "${OUTPUT_DIR}/pdbs/" 2>/dev/null || echo "No PDBs generated"
echo ""
ls -la "${OUTPUT_DIR}/sequences/" 2>/dev/null || echo "No sequences generated"

echo ""
echo "DISCO design for $(basename ${INPUT_JSON}) finished successfully!"
