[View Scripts: run_AF2IG.py](../example_scripts/folding/Alphafold2/AF2_InitialGuess/run_AF2IG.py) | [submit_AF2IG.sh](../example_scripts/folding/Alphafold2/AF2_InitialGuess/submit_AF2IG.sh)

# AlphaFold 2 Initial Guess Scripts

This document provides a detailed explanation of the AF2 Initial Guess scripts located in `example_scripts/folding/Alphafold2/AF2_InitialGuess/`.

## Overview

The AF2 Initial Guess workflow allows you to run AlphaFold 2 predictions on multiple sequences using a reference PDB structure as a template. The workflow threads each sequence from a multi-sequence FASTA file onto a reference structure, then runs AF2 predictions with the threaded structures as initial guesses.

This approach is particularly useful for:
- Predicting structures of protein variants based on a known reference structure
- Generating structural models for homologous sequences
- Running AF2 with structural constraints from a template

## Components

### 1. run_AF2IG.py

A Python script that orchestrates the entire AF2 Initial Guess workflow. It performs three main steps:

1. **Threading**: Uses PyRosetta to thread each sequence from the FASTA file onto the reference PDB structure
2. **Runlist Creation**: Generates a runlist file containing all sequence tags to be processed
3. **AF2 Prediction**: Runs the AF2 initial guess prediction script on all threaded structures

### 2. submit_AF2IG.sh

A SLURM submission script that wraps `run_AF2IG.py` with proper resource allocation and environment setup.

## SLURM Directives (submit_AF2IG.sh)

The submission script includes the following SLURM directives:

-   `--job-name=af2_from_fasta`: Sets the name of the job
-   `--partition=gpu-a100`: Requests a node from the GPU partition
-   `--account=jbsiegelgrp`: Specifies the account for GPU access
-   `--ntasks=1`: Runs as a single task
-   `--cpus-per-task=4`: Requests 4 CPU cores
-   `--gres=gpu:1`: Requests 1 GPU
-   `--mem=16G`: Requests 16GB of memory
-   `--time=24:00:00`: Sets a maximum runtime of 24 hours

## Usage

### Basic Usage

To submit an AF2 Initial Guess job, provide three required arguments:

```bash
sbatch submit_AF2IG.sh <fasta_file> <reference_pdb> <output_dir>
```

**Arguments:**
- `fasta_file`: Path to multi-sequence FASTA file containing sequences to predict
- `reference_pdb`: Path to reference PDB structure (used as threading template)
- `output_dir`: Output directory where results will be stored

### Example

```bash
sbatch submit_AF2IG.sh sequences.fasta template.pdb /path/to/output
```

### Advanced Options

You can specify additional options to customize the AF2 prediction:

```bash
sbatch submit_AF2IG.sh sequences.fasta template.pdb /path/to/output --recycle 3 --force_monomer
```

**Optional Arguments:**
- `--recycle N`: Number of AF2 recycles (default: 3)
- `--force_monomer`: Force monomer prediction without template information

## Requirements

### Python Dependencies

The `run_AF2IG.py` script requires:
- `biopython`: For parsing FASTA files
- `pyrosetta`: For threading sequences onto the reference structure

These are provided in the conda environment `/quobyte/jbsiegelgrp/software/envs/IG_AF2`.

### Input Requirements

1. **FASTA File Format**: Multi-sequence FASTA file with one or more sequences
   ```
   >sequence_1
   MVKVGVNGFGRIGRLVTRAAFNSGKVDIVAINDPFIDLNYMVYMFQYDSTHGKFHGTVKA
   >sequence_2
   MVKVGVNGFGRIGRLVTRAAFNSGKVDIVAINDPFIDLHYMVYMFQYDSTHGKFHGTVKA
   ```

2. **Reference PDB**: A valid PDB file with the same length as the sequences in the FASTA file
   - All sequences in the FASTA must have the same length as the reference PDB
   - The reference structure is used as a template for threading

## Workflow Breakdown

The workflow proceeds in three main steps:

### Step 1: Threading Sequences onto Reference Structure

The script reads each sequence from the FASTA file and threads it onto the reference PDB structure using PyRosetta:

1. Loads the reference PDB structure
2. Validates that the sequence length matches the PDB residue count
3. Mutates each residue in the PDB to match the target sequence
4. Saves the threaded structure to `output_dir/input_pdbs/`

Each sequence is assigned a tag based on its FASTA ID, creating files like `sequence_1.pdb`, `sequence_2.pdb`, etc.

### Step 2: Creating Runlist

A runlist file (`runlist.txt`) is generated containing one tag per line. This file tells AF2 which structures to process:

```
sequence_1
sequence_2
sequence_3
```

### Step 3: Running AF2 Prediction

The AF2 initial guess prediction script is executed with the following parameters:

- **Input directory**: `output_dir/input_pdbs/` (containing threaded PDB files)
- **Output directory**: `output_dir/` (for AF2 predictions)
- **Runlist**: `output_dir/runlist.txt` (list of tags to process)
- **Checkpoint**: `output_dir/checkpoint.txt` (for resuming interrupted jobs)
- **Score file**: `output_dir/af2_scores.sc` (AF2 prediction scores)
- **Recycles**: Number of recycles (default: 3)

## Output Files

After successful completion, the output directory will contain:

```
output_dir/
├── input_pdbs/              # Threaded PDB structures
│   ├── sequence_1.pdb
│   ├── sequence_2.pdb
│   └── ...
├── runlist.txt              # List of processed sequences
├── checkpoint.txt           # Checkpoint file for resuming jobs
├── af2_scores.sc            # AF2 scores for all predictions
├── sequence_1_af2pred.pdb   # AF2 predicted structure for sequence_1
├── sequence_2_af2pred.pdb   # AF2 predicted structure for sequence_2
└── ...
```

### Understanding the Output

- **input_pdbs/**: Contains the threaded structures used as initial guesses
- **runlist.txt**: Lists all sequences that were successfully processed
- **checkpoint.txt**: Allows resuming from the last completed prediction if the job is interrupted
- **af2_scores.sc**: Contains AF2 metrics including pLDDT scores and other confidence measures
- **\*_af2pred.pdb**: Final predicted structures from AF2, one per input sequence

## Log Files

The submission script creates organized log files in the `AF2_IG_logs/` directory:

- `af2_from_fasta_<JOB_ID>.out`: Standard output
- `af2_from_fasta_<JOB_ID>.err`: Standard error

These logs include:
- Job metadata (ID, node, timing)
- Input parameters
- GPU information
- Threading progress for each sequence
- AF2 prediction output
- Final summary of results

## Troubleshooting

### Common Issues

1. **Sequence length mismatch**
   - Error: "Sequence length (X) doesn't match PDB residue count (Y)"
   - Solution: Ensure all sequences in the FASTA file have the same length as the reference PDB

2. **No valid sequences processed**
   - Error: "ERROR: No valid sequences could be processed!"
   - Solution: Check the error messages for individual sequences. Common causes include:
     - Invalid amino acid characters in the sequence
     - Sequence length mismatch
     - Issues with the reference PDB structure

3. **PyRosetta initialization failure**
   - Solution: Ensure the conda environment is properly activated and PyRosetta is installed

4. **GPU not available**
   - Solution: Check that you're on a GPU partition with `--gres=gpu:1` in your SLURM directives

### Performance Optimization

- **Recycle count**: Increasing `--recycle` can improve prediction quality but increases runtime
- **Memory**: For large proteins, you may need to increase `--mem` in the SLURM directives
- **Runtime**: Adjust `--time` based on the number of sequences and their lengths

## Environment Details

The script uses the conda environment located at:
```
/quobyte/jbsiegelgrp/software/envs/IG_AF2
```

This environment includes:
- AlphaFold 2 dependencies
- PyRosetta
- BioPython
- CUDA libraries for GPU acceleration

The AF2 prediction script is located at:
```
/quobyte/jbsiegelgrp/software/dl_binder_design/af2_initial_guess/predict.py
```

## Notes

- The script automatically creates the output directory structure if it doesn't exist
- GPU information is logged at the start of each job for debugging
- The checkpoint system allows resuming interrupted jobs without re-running completed predictions
- Tags are automatically sanitized to remove special characters that might cause filesystem issues
