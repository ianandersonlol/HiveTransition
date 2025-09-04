[View Script: submit_ligandMPNN.sh](../example_scripts/design/LigandMPNN/submit_ligandMPNN.sh)

# LigandMPNN Submission Script

## Overview
The `submit_ligandMPNN.sh` script is a SLURM submission script designed to run LigandMPNN jobs on the HIVE cluster. It simplifies the process of submitting jobs by providing a user-friendly interface and handling the necessary environment setup.

## What It Does

### 1. SLURM Configuration
The script comes pre-configured with recommended SLURM settings for running LigandMPNN on a GPU node. These settings include:
- **Job Name:** `MPNN`
- **Partition:** `gpu-a100`
- **Account:** `genome-center-grp`
- **Time Limit:** `12:00:00`
- **GPU Request:** `1`
- **CPUs per Task:** `32`
- **Memory:** `128G`
- **Output Log:** `logs/%j.out`

### 2. Environment Setup
- **Conda Environment:** Activates the correct conda environment for LigandMPNN located at `/quobyte/jbsiegelgrp/software/envs/ligandmpnn_env`.
- **PyTorch Home:** Sets the `TORCH_HOME` environment variable to use a shared cache for PyTorch models.

### 3. Input and Output
- **Arguments:** The script accepts two command-line arguments:
    1. `pdb_file`: The path to the input PDB file.
    2. `out_folder`: The path to the directory where the output files will be saved.
- **Path Resolution:** It automatically resolves relative paths to absolute paths based on the submission directory (`$SLURM_SUBMIT_DIR`).

### 4. LigandMPNN Execution
- The script runs the main `run.py` script from the LigandMPNN software directory (`/quobyte/jbsiegelgrp/software/LigandMPNN`).
- It passes the PDB file and output folder to the `run.py` script, along with several other parameters.

## Usage

### Basic Usage
To submit a LigandMPNN job, use `sbatch` with the `submit_ligandMPNN.sh` script, providing the input PDB file and output folder as arguments.

```bash
sbatch example_scripts/submit_ligandMPNN.sh /path/to/your/protein.pdb /path/to/your/output_directory
```

### Arguments
- `<pdb_file>`: Path to the input PDB file.
- `<out_folder>`: Path to the output directory.

### Example
```bash
sbatch example_scripts/submit_ligandMPNN.sh inputs/my_protein.pdb results/mpnn_designs
```

## LigandMPNN Parameters
The script calls `run.py` with several parameters that you can customize within the script itself:

- `--model_type "ligand_mpnn"`: Specifies the model to use.
- `--pdb_path "$pdb_file"`: The input PDB file.
- `--out_folder "$out_folder"`: The output directory.
- `--batch_size 100`: The number of sequences to generate in each batch.
- `--number_of_batches 100`: The number of batches to run.
- `--redesigned_residues "your residues you care about"`:  Specify which residues to redesign.
- `--symmetry_residues "residues you are about ie A1,A2,A3"`: Specify symmetric residues.
- `--symmetry_weights "whatever you care about ie 0.1,0.3,0.5"`: Specify weights for symmetric residues.

To change these parameters, you will need to edit the `submit_ligandMPNN.sh` script directly.

## Troubleshooting

### CondaEnvironmentNotFoundError
If you see an error like `CondaEnvironmentNotFoundError: Could not find environment`, it means the conda environment is not in the expected location. The script is hardcoded to use `/quobyte/jbsiegelgrp/software/envs/ligandmpnn_env`. If this path is incorrect, you will need to update the script.

### FileNotFoundError
If the script fails with a `FileNotFoundError`, make sure that the input PDB file exists and the path is correct. Also, ensure that the output directory path is valid.

### Permission Denied
If you get a `Permission Denied` error, it likely means you are trying to write to a directory where you do not have write permissions. Make sure the output directory is in your user space (e.g., `/quobyte/jbsiegelgrp/your_username/...`).
