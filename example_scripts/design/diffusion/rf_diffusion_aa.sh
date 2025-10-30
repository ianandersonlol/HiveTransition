#!/bin/bash
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --time=24:00:00
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --ntasks=1
#SBATCH --job-name=AD2-linker-v1
#SBATCH --output=AD2-12_%A_%a.out
#SBATCH --error=AD2-12_%A_%a.err


module load apptainer/latest



SCRIPT_DIR=/quobyte/jbsiegelgrp/software/rf_diffusion_all_atom
CONTAINER=${SCRIPT_DIR}/rf_se3_diffusion.sif

# Change to the rf_diffusion_all_atom directory
cd ${SCRIPT_DIR}

# Run inference using apptainer with rf_diffusion_all_atom
apptainer run --bind /quobyte:/quobyte \
    --nv ${CONTAINER} -u run_inference.py \
    inference.output_prefix=$1 \
    inference.input_pdb=$2 \
    contigmap.contigs=your contigmap \
