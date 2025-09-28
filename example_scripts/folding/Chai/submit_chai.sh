#!/bin/bash
#SBATCH --job-name=chai_single
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --gres=gpu:1
#SBATCH --time=48:00:00
#SBATCH --output=logs/chai_%A_%a.out
#SBATCH --error=logs/chai_%A_%a.err



###########################################
# Args: INPUT_FASTA  OUTPUT_DIR
###########################################
if [[ $# -ne 2 ]]; then
  echo "Usage: sbatch $0 <input.fasta> <output_dir>"
  exit 1
fi
INPUT_FASTA="$1"
OUTPUT_DIR="$2"

module load conda/latest
module load cuda/12.6.2

eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/chai

mkdir -p "$OUTPUT_DIR"

echo "=== Running ChAI ==="
echo "Job ID:           ${SLURM_JOB_ID:-local}"
echo "Node:             $(hostname)"
echo "GPU:              ${CUDA_VISIBLE_DEVICES:-unset}"
echo "Input FASTA:      $INPUT_FASTA"
echo "Output directory: $OUTPUT_DIR"
echo "===================="

# Run ChAI directly
python run_chai.py "$INPUT_FASTA" "$OUTPUT_DIR"

echo "Done. Results in $OUTPUT_DIR"
echo "===================="