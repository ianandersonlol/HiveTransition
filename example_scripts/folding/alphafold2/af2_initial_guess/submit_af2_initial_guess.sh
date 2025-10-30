#!/bin/bash --norc
#SBATCH --job-name=af2_from_fasta
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --gres=gpu:1
#SBATCH --mem=64G
#SBATCH --time=24:00:00

# Submit AF2 initial guess job on multi-sequence FASTA with reference PDB
#
# Usage:
#   sbatch submit_af2_from_fasta.sh <fasta_file> <reference_pdb> <output_dir> [--recycle N] [--force_monomer]
#
# Arguments:
#   fasta_file    : Path to multi-sequence FASTA file
#   reference_pdb : Path to reference PDB structure
#   output_dir    : Output directory for AF2 predictions
#   --recycle N   : (Optional) Number of AF2 recycles (default: 3)
#   --force_monomer : (Optional) Force monomer prediction
#
# Example:
#   sbatch submit_af2_from_fasta.sh sequences.fasta template.pdb /path/to/output --recycle 3 --force_monomer

# Check for required arguments
if [ "$#" -lt 3 ]; then
    echo "ERROR: Missing required arguments"
    echo ""
    echo "Usage: sbatch submit_af2_from_fasta.sh <fasta_file> <reference_pdb> <output_dir> [options]"
    echo ""
    echo "Required arguments:"
    echo "  fasta_file     : Path to multi-sequence FASTA file"
    echo "  reference_pdb  : Path to reference PDB structure"
    echo "  output_dir     : Output directory for AF2 predictions"
    echo ""
    echo "Optional arguments:"
    echo "  --recycle N      : Number of AF2 recycles (default: 3)"
    echo "  --force_monomer  : Force monomer prediction (no template)"
    echo ""
    echo "Example:"
    echo "  sbatch submit_af2_from_fasta.sh sequences.fasta template.pdb /path/to/output --recycle 3"
    exit 1
fi

# Parse arguments
FASTA_FILE="$1"
REFERENCE_PDB="$2"
OUTPUT_DIR="$3"
shift 3

# Additional arguments (--recycle, --force_monomer, etc.)
EXTRA_ARGS="$@"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/run_AF2IG.py"

# Set up log files based on job ID
if [ -n "${SLURM_JOB_ID}" ]; then
    LOG_DIR="${SLURM_SUBMIT_DIR}/AF2_IG_logs"
    mkdir -p "${LOG_DIR}"
    exec 1>"${LOG_DIR}/af2_from_fasta_${SLURM_JOB_ID}.out"
    exec 2>"${LOG_DIR}/af2_from_fasta_${SLURM_JOB_ID}.err"
fi

echo "========================================================================"
echo "AF2 Initial Guess from Multi-Sequence FASTA"
echo "========================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURMD_NODENAME}"
echo "Started: $(date)"
echo ""
echo "Input Parameters:"
echo "  FASTA file:     ${FASTA_FILE}"
echo "  Reference PDB:  ${REFERENCE_PDB}"
echo "  Output dir:     ${OUTPUT_DIR}"
echo "  Extra args:     ${EXTRA_ARGS}"
echo ""

# Validate input files
if [ ! -f "${FASTA_FILE}" ]; then
    echo "ERROR: FASTA file not found: ${FASTA_FILE}"
    exit 1
fi

if [ ! -f "${REFERENCE_PDB}" ]; then
    echo "ERROR: Reference PDB not found: ${REFERENCE_PDB}"
    exit 1
fi

if [ ! -f "${PYTHON_SCRIPT}" ]; then
    echo "ERROR: Python script not found: ${PYTHON_SCRIPT}"
    exit 1
fi

# Load conda environment
echo "Loading conda environment..."
module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/IG_AF2

# Check GPU availability
echo ""
echo "GPU Information:"
nvidia-smi --query-gpu=index,name,memory.total --format=csv
echo ""

# Run AF2 from FASTA script
echo "========================================================================"
echo "Running AF2 prediction..."
echo "========================================================================"
echo ""

python "${PYTHON_SCRIPT}" \
    -f "${FASTA_FILE}" \
    -r "${REFERENCE_PDB}" \
    -o "${OUTPUT_DIR}" \
    ${EXTRA_ARGS}

EXIT_CODE=$?

echo ""
echo "========================================================================"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "Job completed successfully!"
    echo "========================================================================"
    echo "Output directory: ${OUTPUT_DIR}"
    echo "  - input_pdbs/         : Threaded PDB structures"
    echo "  - runlist.txt         : List of processed sequences"
    echo "  - af2_scores.sc       : AF2 scores"
    echo "  - *_af2pred.pdb       : AF2 predicted structures"
else
    echo "Job failed with exit code: ${EXIT_CODE}"
    echo "========================================================================"
fi

echo ""
echo "Ended: $(date)"
echo ""

exit ${EXIT_CODE}
