#!/bin/bash --norc
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --job-name=af3_single
#SBATCH --output=af3_%j.txt
#SBATCH --error=af3_%j.txt

# Usage: sbatch submit_af3_single.sh <path_to_json_file>

if [ $# -ne 1 ]; then
    echo "Usage: sbatch $0 <path_to_json_file>"
    echo "Example: sbatch $0 /path/to/protein.json"
    exit 1
fi

JSON_PATH="$1"

# Check if file exists
if [ ! -f "$JSON_PATH" ]; then
    echo "Error: JSON file $JSON_PATH does not exist"
    exit 1
fi

# Load required modules
module load apptainer/latest

# Convert to absolute path and extract components
JSON_PATH=$(realpath "$JSON_PATH")
JSON_DIR=$(dirname "$JSON_PATH")
JSON_FILE=$(basename "$JSON_PATH")
BASE_NAME="${JSON_FILE%.json}"
SAFE_NAME=$(echo "$BASE_NAME" | tr ' ' '_' | tr -cd '[:alnum:]._-')

# Set up paths
OUTPUT_DIR="$JSON_DIR/${SAFE_NAME}_output"
LOGS_DIR="$JSON_DIR/logs"
AF3_DIR="/quobyte/jbsiegelgrp/software/alphafold3"

START_TIME=$(date +%s)
echo "Starting AlphaFold 3 prediction for $JSON_FILE at $(date)"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Running on node: ${SLURM_NODELIST}"
echo "Input JSON: $JSON_PATH"
echo "Output directory: $OUTPUT_DIR"

# Create directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$LOGS_DIR"

# Start background GPU monitoring
(
    while true; do
        nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv,noheader >> "${LOGS_DIR}/${SAFE_NAME}_gpu_monitor_${SLURM_JOB_ID}.csv" 2>/dev/null
        sleep 5
    done
) &
MONITOR_PID=$!

# Run AlphaFold 3
singularity exec \
    --bind "$JSON_DIR:/input" \
    --bind "$OUTPUT_DIR:/output" \
    --bind "$AF3_DIR:/models" \
    --bind "$AF3_DIR/public_databases:/databases" \
    --bind "$LOGS_DIR:/logs" \
    --nv \
    "$AF3_DIR/alphafold3.sif" \
    python /app/alphafold/run_alphafold.py \
    --json_path="/input/$JSON_FILE" \
    --model_dir=/models \
    --output_dir=/output \
    --db_dir=/databases

# Stop GPU monitoring
kill $MONITOR_PID 2>/dev/null || true

END_TIME=$(date +%s)
RUNTIME=$((END_TIME - START_TIME))
HOURS=$((RUNTIME / 3600))
MINUTES=$(( (RUNTIME % 3600) / 60 ))
SECONDS=$((RUNTIME % 60))

echo "Prediction completed at $(date)"
echo "Total runtime: ${HOURS}h ${MINUTES}m ${SECONDS}s"

# Analyze GPU usage from monitoring data
if [ -f "${LOGS_DIR}/${SAFE_NAME}_gpu_monitor_${SLURM_JOB_ID}.csv" ]; then
    echo ""
    echo "=== Resource Usage Summary ==="

    # Get peak VRAM usage and average GPU utilization
    PEAK_VRAM=$(awk -F', ' '{gsub(" MiB","",$3); if($3>max) max=$3} END {printf "%.1f", max/1024}' "${LOGS_DIR}/${SAFE_NAME}_gpu_monitor_${SLURM_JOB_ID}.csv" 2>/dev/null || echo "N/A")
    TOTAL_VRAM=$(awk -F', ' 'NR==1 {gsub(" MiB","",$4); printf "%.1f", $4/1024}' "${LOGS_DIR}/${SAFE_NAME}_gpu_monitor_${SLURM_JOB_ID}.csv" 2>/dev/null || echo "N/A")
    AVG_GPU_UTIL=$(awk -F', ' '{gsub(" %","",$5); sum+=$5; count++} END {if(count>0) printf "%.1f", sum/count; else print "N/A"}' "${LOGS_DIR}/${SAFE_NAME}_gpu_monitor_${SLURM_JOB_ID}.csv" 2>/dev/null || echo "N/A")
    GPU_NAME=$(awk -F', ' 'NR==1 {print $2}' "${LOGS_DIR}/${SAFE_NAME}_gpu_monitor_${SLURM_JOB_ID}.csv" 2>/dev/null || echo "Unknown")

    echo "GPU: ${GPU_NAME}"
    echo "Peak VRAM usage: ${PEAK_VRAM} GB / ${TOTAL_VRAM} GB"
    echo "Average GPU utilization: ${AVG_GPU_UTIL}%"

    # Get SLURM job efficiency stats
    echo ""
    echo "CPU/Memory efficiency (from SLURM):"
    seff ${SLURM_JOB_ID} 2>/dev/null | grep -E "(CPU Efficiency|Memory Efficiency|Memory Utilized)" || echo "Unable to retrieve SLURM efficiency data"

    echo "=============================="

    # Clean up monitoring file
    rm -f "${LOGS_DIR}/${SAFE_NAME}_gpu_monitor_${SLURM_JOB_ID}.csv"
fi

echo ""
echo "Output files:"
ls -la "$OUTPUT_DIR/"

echo ""
echo "AlphaFold 3 prediction for $JSON_FILE finished successfully!"