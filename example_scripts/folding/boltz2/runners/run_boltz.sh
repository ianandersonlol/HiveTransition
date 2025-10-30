#!/bin/bash --norc
#SBATCH --account=genome-center-grp
#SBATCH --partition=gpu-a100
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00
#SBATCH --output=logs/boltz_%A_%a.out
#SBATCH --error=logs/boltz_%A_%a.err
#SBATCH --job-name=boltz2

# Create logs directory if it doesn't exist
mkdir -p logs

# Load conda module (not cuda)
module load conda/latest

# Initialize conda for bash
eval "$(conda shell.bash hook)"

# Activate boltz environment
conda activate /quobyte/jbsiegelgrp/software/envs/boltz

# Set boltz path and cache directory
export BOLTZ_PATH=/quobyte/jbsiegelgrp/software/boltz
export BOLTZ_CACHE=/quobyte/jbsiegelgrp/databases/boltz/cache

# Print job information
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Running on: $(hostname)"
echo "Working directory: $(pwd)"
echo "GPU: $CUDA_VISIBLE_DEVICES"

# Run boltz predict
# Usage: sbatch run_boltz.sh <input_yaml_file> [additional_boltz_options]
# Example: sbatch run_boltz.sh my_protein_ligand.yaml --use_msa_server --use_potentials

INPUT_FILE=$1
shift  # Remove first argument, rest are additional boltz options

if [ -z "$INPUT_FILE" ]; then
    echo "Error: No input file provided"
    echo "Usage: sbatch run_boltz.sh <input_yaml_file> [additional_boltz_options]"
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file $INPUT_FILE does not exist"
    exit 1
fi

echo "Input file: $INPUT_FILE"
echo "Additional options: $@"
echo "Cache directory: $BOLTZ_CACHE"
echo "Starting boltz prediction..."

# Run boltz predict with hardcoded cache directory
boltz predict "$INPUT_FILE" --cache "$BOLTZ_CACHE" "$@"

