
[View relax.sh](../example_scripts/docking/relaxation/relax.sh)

# Rosetta Relaxation Script

This document provides a detailed explanation of the `relax.sh` script located in the `example_scripts/docking/relaxation` directory.

## Overview

The `relax.sh` script is a bash script designed to submit a Rosetta relaxation job to a SLURM cluster. It is configured to run an array job, which allows you to relax the same structure multiple times in parallel.

## SLURM Directives

The script begins with a series of `#SBATCH` directives that configure the job submission:

-   `--job-name=hello.pdb`: Sets the name of the job.
-   `--time=3000`: Sets a maximum runtime of 3000 minutes.
-   `--ntasks=1`: Requests one task.
-   `--mem=4GB`: Requests 4GB of memory.
-   `--partition=low`: Requests a node from the `low` partition.
-   `--output=logs/relax_hello_%A_%a.out`: Specifies the file for standard output, where `%A` is the job ID and `%a` is the array task ID.
-   `--error=logs/relax_hello_%A_%a.err`: Specifies the file for standard error.
-   `--array=1-100`: Specifies that this is an array job with 100 tasks.

## Rosetta Flags

The script then calls the Rosetta `relax.static.linuxgccrelease` executable with a number of flags:

-   `-database`: Specifies the path to the Rosetta database.
-   `-overwrite`: Allows Rosetta to overwrite existing files.
-   `-nstruct 5`: Generates 5 structures per task.
-   `-ex1 -ex2`: Enables extra rotamer sampling for chi 1 and chi 2.
-   `-use_input_sc`: Uses the sidechain conformations from the input PDB file.
-   `-flip_HNQ`: Allows flipping of Histidine, Asparagine, and Glutamine sidechains.
-   `-no_optH false`: Disables optimization of hydrogen atoms.
-   `-user_tag ${SLURM_ARRAY_TASK_ID}`: Adds a user-defined tag to the output files.
-   `-out:suffix _${SLURM_ARRAY_TASK_ID}`: Adds a suffix to the output file names.
-   `-relax:constrain_relax_to_start_coords`: Constrains the relaxation to the starting coordinates.
-   `-relax:coord_constrain_sidechains`: Constrains the sidechain coordinates.
-   `-relax:ramp_constraints false`: Disables ramping of constraints.
-   `-in:file:s hello.pdb`: Specifies the input PDB file.
-   `-out:path:all relax_results`: Specifies the output directory for the relaxed structures.

## Usage

To use the script, you need to replace `hello.pdb` with the path to your own PDB file. You can then submit the script to SLURM using `sbatch`.

```bash
sbatch example_scripts/docking/relaxation/relax.sh
```
