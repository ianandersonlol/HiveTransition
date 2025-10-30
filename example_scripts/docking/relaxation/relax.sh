#!/bin/bash
#SBATCH --job-name=rosetta_relax
#SBATCH --partition=low
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --output=logs/relax_%A_%a.out
#SBATCH --error=logs/relax_%A_%a.err
#SBATCH --array=1-100


/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/source/bin/relax.static.linuxgccrelease \
  -database /quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/database \
  -overwrite \
  -nstruct 5 \
  -ex1 -ex2 \
  -use_input_sc \
  -flip_HNQ \
  -no_optH false \
  -user_tag ${SLURM_ARRAY_TASK_ID} \
  -out:suffix _${SLURM_ARRAY_TASK_ID} \
  -relax:constrain_relax_to_start_coords \
  -relax:coord_constrain_sidechains \
  -relax:ramp_constraints false \
  -in:file:s hello.pdb \
  -out:path:all relax_results
