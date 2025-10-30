[View Script: ../example_scripts/design/diffusion/rf_diffusion_aa.sh](../example_scripts/design/diffusion/rf_diffusion_aa.sh)

# RFdiffusion Amino Acid Design Script

## Overview
The `rf_diffusion_aa.sh` script is designed to run RFdiffusion All-Atom for *de novo* protein design, specifically focusing on amino acid sequence and backbone generation. It uses Apptainer (Singularity) to run RFdiffusion in a containerized environment. The script provides a template for submitting RFdiffusion jobs to a SLURM cluster, pre-configured with common parameters for protein design tasks.

## What It Does
This script automates the process of setting up and executing RFdiffusion All-Atom. Key functionalities include:
- **Module Loading**: Loads the Apptainer module for containerized execution.
- **Container Execution**: Runs RFdiffusion using the Singularity container at `/quobyte/jbsiegelgrp/software/rf_diffusion_all_atom/rf_se3_diffusion.sif`.
- **Job Submission**: Constructs and executes the `run_inference.py` command with specified parameters.
- **Parameter Configuration**: Accepts command-line arguments for output prefix and input PDB, with customizable contig specifications.

## Usage

### Basic Usage
The script accepts two command-line arguments and requires modification of the contig map within the script.

```bash
# Usage: sbatch rf_diffusion_aa.sh <output_prefix> <input_pdb>
sbatch rf_diffusion_aa.sh /path/to/output/prefix /path/to/input.pdb

# Example:
sbatch example_scripts/design/diffusion/rf_diffusion_aa.sh \
    /quobyte/jbsiegelgrp/yourname/designs/linker_design \
    /quobyte/jbsiegelgrp/yourname/inputs/protein.pdb
```

**Important:** You must edit the script to set your contig map on line 29:
```bash
contigmap.contigs=your contigmap \
```

### Key Parameters within `rf_diffusion_aa.sh`

The script contains several configurable parameters for RFdiffusion:

- `--job-name`: SLURM job name (e.g., `AD2-linker-v1`).
- `--partition`: SLURM partition to use (e.g., `gpu-a100`).
- `--account`: SLURM account for resource allocation (e.g., `genome-center-grp`).
- `--gres`: GPU resources requested (e.g., `gpu:1`).
- `--time`: Maximum job runtime (e.g., `24:00:00`).
- `--mem`: Memory requested (e.g., `16G`).
- `--cpus-per-task`: CPUs per task (e.g., `4`).

Within the `apptainer run` command:

- `$1` (first argument): `inference.output_prefix` - Defines the base path for output files.
- `$2` (second argument): `inference.input_pdb` - Path to the input PDB structure.
- `contigmap.contigs`: Specifies the desired protein architecture. **This must be edited in the script before submission.**

## Examples

### Example 1: Designing a linker between protein domains
Before submitting, edit line 29 in the script to specify your contig map:

```bash
contigmap.contigs=[A1-150/0 10-40/A151-300] \
```

Then submit the job:

```bash
sbatch rf_diffusion_aa.sh \
    /quobyte/jbsiegelgrp/yourname/designs/linker_v1 \
    /quobyte/jbsiegelgrp/yourname/inputs/two_domain_protein.pdb
```

### Example 2: Designing with specific architecture
Edit the contig map in the script:

```bash
contigmap.contigs=[A1-50/0 20-30/A51-100] \
```

This designs a 20-30 residue linker between residues 1-50 and 51-100 of chain A.

## Important Notes
- This script uses **RFdiffusion All-Atom** via Apptainer/Singularity container, not the standard RFdiffusion conda environment.
- The Apptainer module must be available on your cluster (`module load apptainer/latest`).
- The container is located at `/quobyte/jbsiegelgrp/software/rf_diffusion_all_atom/rf_se3_diffusion.sif`.
- You **must edit the script** to set your contig map on line 29 before submitting.
- The script requires two command-line arguments: output prefix and input PDB file.
- Adjust the SLURM parameters (`--time`, `--mem`, `--cpus-per-task`) according to your design's computational demands.
- Ensure the output prefix points to a directory where you have write permissions.
