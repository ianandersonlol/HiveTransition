[View Script: ../example_scripts/design/Diffusion/rf_diffusion_aa.sh](../example_scripts/design/Diffusion/rf_diffusion_aa.sh)

# RFdiffusion Amino Acid Design Script

## Overview
The `rf_diffusion_aa.sh` script is designed to run RFdiffusion for *de novo* protein design, specifically focusing on amino acid sequence and backbone generation. It provides a template for submitting RFdiffusion jobs to a SLURM cluster, pre-configured with common parameters for protein design tasks.

## What It Does
This script automates the process of setting up and executing RFdiffusion. Key functionalities include:
- **Environment Setup**: Activates the necessary Conda environment for RFdiffusion.
- **Directory Navigation**: Changes to the RFdiffusion installation directory.
- **Job Submission**: Constructs and executes the `run_inference.py` command with specified parameters.
- **Parameter Configuration**: Allows easy modification of design parameters such as output prefix, number of designs, and contig specifications.

## Usage

### Basic Usage
To use this script, you typically need to modify the parameters within the `.sh` file to suit your specific design needs.

```bash
# Navigate to the directory containing the script
cd /path/to/HiveTransition/example_scripts/design/Diffusion/

# Make the script executable (if not already)
chmod +x rf_diffusion_aa.sh

# Run the script (usually submitted via sbatch on a SLURM cluster)
sbatch rf_diffusion_aa.sh
```

### Key Parameters within `rf_diffusion_aa.sh`

The script contains several configurable parameters for RFdiffusion:

- `--job-name`: SLURM job name (e.g., `rf_diffusion_aa`).
- `--partition`: SLURM partition to use (e.g., `gpu-a100`).
- `--account`: SLURM account for resource allocation (e.g., `genome-center-grp`).
- `--gres`: GPU resources requested (e.g., `gpu:1`).
- `--time`: Maximum job runtime (e.g., `12:00:00`).
- `--mem`: Memory requested (e.g., `32G`).

Within the `python run_inference.py` command:

- `inference.output_prefix`: Defines the base path for output files. **You should change this to your desired output directory.**
- `inference.num_designs`: Number of protein designs to generate.
- `inference.ckpt_path`: Path to the RFdiffusion model checkpoint.
- `contigmap.contigs`: Specifies the desired protein architecture (e.g., `A1-50/0 100-100` for a 50-residue protein with a 100-residue scaffold).

## Examples

### Example 1: Designing a simple monomer
To design a 100-residue monomer, you might set `contigmap.contigs` to `A1-100`.

```bash
# Example snippet from rf_diffusion_aa.sh
python /quobyte/jbsiegelgrp/software/RFdiffusion/scripts/run_inference.py \
    inference.output_prefix=/quobyte/jbsiegelgrp/users/your_username/rf_designs/monomer_design \
    inference.num_designs=10 \
    inference.ckpt_path=/quobyte/jbsiegelgrp/software/RFdiffusion/models/RF_structure_prediction_model.pt \
    'contigmap.contigs=[A1-100]'
```

### Example 2: Designing a protein with a specific length and scaffold
If you want to design a 50-residue protein with a 100-residue scaffold, you could use:

```bash
# Example snippet from rf_diffusion_aa.sh
python /quobyte/jbsiegelgrp/software/RFdiffusion/scripts/run_inference.py \
    inference.output_prefix=/quobyte/jbsiegelgrp/users/your_username/rf_designs/scaffold_design \
    inference.num_designs=5 \
    inference.ckpt_path=/quobyte/jbsiegelgrp/software/RFdiffusion/models/RF_structure_prediction_model.pt \
    'contigmap.contigs=[A1-50/0 100-100]'
```

## Important Notes
- Ensure the RFdiffusion software and its Conda environment are correctly installed and accessible on your system/cluster.
- Adjust the SLURM parameters (`--partition`, `--account`, `--time`, `--mem`) according to your cluster's policies and the computational demands of your design.
- The `inference.output_prefix` should point to a directory where you have write permissions.
