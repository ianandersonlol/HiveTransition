[View Script: colabfold.sh](../example_scripts/folding/alphafold2/colabfold.sh)

# ColabFold SLURM Submission Script

This document provides a detailed explanation of the `colabfold.sh` script located in the `example_scripts` directory.

## Overview

The `colabfold.sh` script is a bash script designed to submit a ColabFold job to a SLURM cluster. It simplifies the process of running ColabFold by pre-configuring the necessary SLURM directives and environment variables.

## SLURM Directives

The script begins with a series of `#SBATCH` directives that configure the job submission:

-   `--job-name=colabfold_job`: Sets the name of the job.
-   `--account=genome-center-grp`: Specifies the account to use for the job.
-   `--partition=gpu-a100`: Requests a node from the `gpu-a100` partition.
-   `--gres=gpu:1`: Requests one GPU.
-   `--cpus-per-task=16`: Requests 16 CPU cores.
-   `--mem=64G`: Requests 64GB of memory.
-   `--time=12:00:00`: Sets a maximum runtime of 12 hours.
-   `--output=logs/colabfold_%A_%a.out`: Specifies the file for standard output, where `%A` is the job ID and `%a` is the array task ID.
-   `--error=logs/colabfold_%A_%a.err`: Specifies the file for standard error.

## Usage

To use the script, you need to provide two arguments:

1.  The path to the input FASTA file.
2.  The path to the output directory where the results will be stored.

The script should be submitted to SLURM using `sbatch`.

### Example

```bash
sbatch example_scripts/colabfold.sh sequences/P28329.fasta colabfold_results/P28329
```

## Script Breakdown

1.  **Argument Check:** The script first checks if exactly two arguments are provided. If not, it prints a usage message and exits.

2.  **Variable Assignment:** The input FASTA file and output directory are assigned to the `INPUT_FASTA` and `OUTPUT_DIR` variables, respectively.

3.  **Input File Check:** It verifies that the input FASTA file exists.

4.  **Directory Creation:** The script creates the `logs` directory (for SLURM output) and the specified output directory if they don't already exist.

5.  **Environment Setup:** It prepends the path to the `colabfold-conda` environment to the system's `PATH`. This ensures that the `colabfold_batch` command is found.

    ```bash
    export PATH="/quobyte/jbsiegelgrp/software/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH"
    ```

6.  **Job Execution:** The script then prints some information about the job and executes `colabfold_batch` with the following options:
    -   `--num-models 1`: Predicts the structure for one model.
    -   `--amber`: Uses AMBER for structure relaxation.
    -   `--use-gpu-relax`: Uses the GPU for the relaxation step.
    -   `"$INPUT_FASTA"`: The input FASTA file.
    -   `"$OUTPUT_DIR"`: The output directory.

7.  **Completion Message:** Finally, it prints the end time and a completion message.
