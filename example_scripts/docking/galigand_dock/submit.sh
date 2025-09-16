#!/bin/bash
#SBATCH --job-name=galiganddock
#SBATCH --partition=low
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=48:00:00
#SBATCH --output=logs/galiganddock_%j.out
#SBATCH --error=logs/galiganddock_%j.err
#SBATCH --requeue
/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/source/bin/rosetta_scripts.static.linuxgccrelease -database /quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/database \
  @flags \
  -parser:protocol docking.xml \
  -s GatZ_F6P.pdb \
  -enzdes::cstfile 4Epimv7.cst \
  -nstruct 1 \
  -suffix _$SLURM_ARRAY_TASK_ID \
  -out:path:all results/
