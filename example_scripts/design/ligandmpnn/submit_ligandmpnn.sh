#!/bin/bash
#SBATCH --job-name=LigandMPNN
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --time=12:00:00
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=16
#SBATCH --mem=128G
#SBATCH --output=logs/ligandMPNN_%A_%a.out


export TORCH_HOME=/quobyte/jbsiegelgrp/software/LigandMPNN/.cache

module load conda/latest

eval "$(conda shell.bash hook)"

conda activate /quobyte/jbsiegelgrp/software/envs/ligandmpnn_env

LIGAND_MPNN_DIR="/quobyte/jbsiegelgrp/software/LigandMPNN"

if [[ "$1" == /* ]]; then
  pdb_file="$1"
else
  pdb_file="$SLURM_SUBMIT_DIR/$1"
fi

if [[ "$2" == /* ]]; then
  out_folder="$2"
else
  out_folder="$SLURM_SUBMIT_DIR/$2"
fi

(cd "$LIGAND_MPNN_DIR" && python run.py --model_type "ligand_mpnn" --pdb_path "$pdb_file" --out_folder "$out_folder" --batch_size 100 --number_of_batches 100 --redesigned_residues "your residues you care about" --symmetry_residues "residues you are about ie A1,A2,A3" --symmetry_weights "whatever you care about ie 0.1,0.3,0.5")
