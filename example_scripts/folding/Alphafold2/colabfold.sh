#!/bin/bash
#SBATCH --job-name=colabfold_job
#SBATCH --account=genome-center-grp
#SBATCH --partition=gpu-a100
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --time=12:00:00
#SBATCH --output=logs/colabfold_%A_%a.out
#SBATCH --error=logs/colabfold_%A_%a.err


if [ $# -ne 2 ]; then
    echo "Usage: $0 <input_fasta> <output_directory>"
    echo "Example: sbatch $0 sequences/P28329.fasta colabfold_results/P28329"
    exit 1
fi

INPUT_FASTA="$1"
OUTPUT_DIR="$2"

if [ ! -f "$INPUT_FASTA" ]; then
    echo "Error: Input FASTA file '$INPUT_FASTA' does not exist"
    exit 1
fi

mkdir -p logs
mkdir -p "$OUTPUT_DIR"

export PATH="/quobyte/jbsiegelgrp/software/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH"

echo "Running ColabFold on $(hostname)"
echo "Job ID: $SLURM_JOB_ID"
echo "Input: $INPUT_FASTA"
echo "Output directory: $OUTPUT_DIR"
echo "Start time: $(date)"

colabfold_batch --num-models 1 --amber --use-gpu-relax "$INPUT_FASTA" "$OUTPUT_DIR"

echo "End time: $(date)"
echo "ColabFold completed for $INPUT_FASTA"