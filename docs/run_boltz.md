[View Script: run_boltz.sh](../example_scripts/folding/Boltz2/runners/run_boltz.sh)

# Boltz2 SLURM Submission Script

This document provides a detailed explanation of the `run_boltz.sh` script located in the `example_scripts/folding/Boltz2/runners/` directory.

## Overview

The `run_boltz.sh` script is a bash script designed to submit Boltz2 structure prediction jobs to a SLURM cluster. Boltz2 is a biomolecular structure prediction model that can predict structures for proteins, nucleic acids (DNA/RNA), and small molecule ligands. This script simplifies the process of running Boltz2 by pre-configuring the necessary SLURM directives and environment variables.

## SLURM Directives

The script begins with a series of `#SBATCH` directives that configure the job submission:

-   `--account=genome-center-grp`: Specifies the account to use for the job.
-   `--partition=gpu-a100`: Requests a node from the `gpu-a100` partition.
-   `--cpus-per-task=16`: Requests 16 CPU cores.
-   `--mem=32G`: Requests 32GB of memory.
-   `--gres=gpu:1`: Requests one GPU.
-   `--time=12:00:00`: Sets a maximum runtime of 12 hours.
-   `--output=logs/boltz_%A_%a.out`: Specifies the file for standard output, where `%A` is the job ID and `%a` is the array task ID.
-   `--error=logs/boltz_%A_%a.err`: Specifies the file for standard error.
-   `--job-name=boltz2`: Sets the name of the job.

## Usage

To use the script, you need to provide at least one argument:

1.  The path to the input YAML file.
2.  (Optional) Additional boltz command-line options.

The script should be submitted to SLURM using `sbatch`.

### Examples

```bash
# Basic usage
sbatch run_boltz.sh protein_complex.yaml

# With MSA server
sbatch run_boltz.sh protein_complex.yaml --use_msa_server

# With MSA server and potentials
sbatch run_boltz.sh protein_complex.yaml --use_msa_server --use_potentials

# With custom number of models
sbatch run_boltz.sh protein_complex.yaml --num_models 5
```

## Script Breakdown

1.  **Directory Creation:** The script creates a `logs` directory if it doesn't exist to store SLURM output files.

2.  **Module Loading:** It loads the conda module (note: NOT cuda, as GPU drivers are handled differently).

    ```bash
    module load conda/latest
    ```

3.  **Conda Initialization:** The script initializes conda for bash and activates the boltz environment.

    ```bash
    eval "$(conda shell.bash hook)"
    conda activate /quobyte/jbsiegelgrp/software/envs/boltz
    ```

4.  **Environment Variables:** It sets up required environment variables:
    -   `BOLTZ_PATH`: Path to the Boltz installation
    -   `BOLTZ_CACHE`: Directory for model weights and cache files

    ```bash
    export BOLTZ_PATH=/quobyte/jbsiegelgrp/software/boltz
    export BOLTZ_CACHE=/quobyte/jbsiegelgrp/databases/boltz/cache
    ```

5.  **Job Information:** The script prints detailed job information including job ID, hostname, working directory, and GPU assignment.

6.  **Input Validation:** It validates that an input file was provided and that the file exists.

7.  **Argument Processing:** The first argument is treated as the input YAML file, and all subsequent arguments are passed directly to the boltz predict command.

8.  **Job Execution:** The script executes `boltz predict` with:
    -   The input YAML file
    -   The hardcoded cache directory
    -   Any additional user-specified options

    ```bash
    boltz predict "$INPUT_FILE" --cache "$BOLTZ_CACHE" "$@"
    ```

## Input Format

Boltz2 requires YAML input files specifying the molecular system to predict.

### Basic Examples

**Protein monomer:**
```yaml
version: 1
sequences:
  - protein:
      id: A
      sequence: MKLAVFLALAAGVLGVAVQPQSQFRYESP...
```

**Protein-protein complex:**
```yaml
version: 1
sequences:
  - protein:
      id: A
      sequence: MKLAVFLALAAGVLGVAVQPQSQFRYESP...
  - protein:
      id: B
      sequence: MHHHHHHSSGVDLGTENLYFQSNAMSKGE...
```

**Protein-ligand complex:**
```yaml
version: 1
sequences:
  - protein:
      id: A
      sequence: MKLAVFLALAAGVLGVAVQPQSQFRYESP...
  - ligand:
      id: B
      smiles: 'CC(C)Cc1ccc(cc1)C(C)C(=O)O'
      # Ibuprofen
```

**Protein-DNA complex:**
```yaml
version: 1
sequences:
  - protein:
      id: A
      sequence: MKLAVFLALAAGVLGVAVQPQSQFRYESP...
  - dna:
      id: B
      sequence: ATCGATCGATCG
```

### Supported Entity Types

- **protein**: Amino acid sequences (standard single-letter code)
- **ligand**: Small molecules (SMILES strings)
- **dna**: DNA sequences (A, T, C, G)
- **rna**: RNA sequences (A, U, C, G)

**Note:** If you have input files in Chai FASTA format, use the [chai_to_boltz.py](chai_to_boltz.md) helper script to convert them to Boltz2 YAML format.

## Common Options

Boltz2 supports various command-line options that can be passed after the input file:

**MSA Generation:**
```bash
--use_msa_server    # Use MSA server for sequence alignments (recommended for better accuracy)
```

**Potentials:**
```bash
--use_potentials    # Use additional energy potentials
```

**Number of Models:**
```bash
--num_models 5      # Generate 5 models (default varies)
```

**Device Selection:**
```bash
--device cuda:0     # Specify GPU device (usually auto-detected)
```

**Output Directory:**
```bash
--out_dir results/  # Specify output directory (default: current directory)
```

## Output Structure

Boltz2 predictions generate output files in the working directory:

```
./
├── boltz_results_<timestamp>/
│   ├── predictions/
│   │   ├── model_0.pdb              # Predicted structure
│   │   ├── model_0_confidence.json  # Confidence scores
│   │   └── ...
│   └── metadata.json
└── logs/
    ├── boltz_<jobid>.out            # Job stdout
    └── boltz_<jobid>.err            # Job stderr
```

### Output Files Explained

**Structure Files:**
- `model_*.pdb`: Predicted structures (typically multiple models/seeds)
- Each chain is labeled with the ID specified in the YAML file

**Confidence Scores:**
- `*_confidence.json`: Per-residue/atom confidence metrics
- Similar to pLDDT scores in AlphaFold

**Metadata:**
- `metadata.json`: Prediction settings and run information

## Resource Requirements

### Default Settings

```bash
#SBATCH --cpus-per-task=16        # CPU cores
#SBATCH --mem=32G                 # RAM
#SBATCH --gres=gpu:1              # 1 GPU required
#SBATCH --time=12:00:00           # Max runtime (12 hours)
```

### Typical Resource Usage

**Small proteins (<200 residues):**
- Runtime: 30 minutes - 2 hours
- Peak VRAM: 8-15 GB
- Recommended: Default settings

**Medium proteins/complexes (200-500 residues):**
- Runtime: 2-4 hours
- Peak VRAM: 15-25 GB
- Recommended: Default settings

**Large complexes (>500 residues):**
- Runtime: 4-8 hours
- Peak VRAM: 25-40 GB
- Recommended: Consider increasing memory to 64G

**With ligands/nucleic acids:**
- Add 20-50% to estimated runtime
- Similar VRAM requirements

### Modifying Resource Requests

Edit the `#SBATCH` directives at the top of the script:

**Increase runtime:**
```bash
#SBATCH --time=24:00:00  # 24 hours
```

**Increase memory:**
```bash
#SBATCH --mem=64G  # 64 GB RAM
```

**Request more CPUs:**
```bash
#SBATCH --cpus-per-task=32  # 32 cores
```

## Monitoring Jobs

### Check Job Status
```bash
squeue -u $USER -n boltz2
```

### View Logs in Real-Time
```bash
# View output log
tail -f logs/boltz_<jobid>.out

# View error log
tail -f logs/boltz_<jobid>.err
```

### Cancel Job
```bash
scancel <job_id>
```

## Complete Workflow Example

**Step 1: Create YAML file**
```bash
cat > my_complex.yaml << 'EOF'
version: 1
sequences:
  - protein:
      id: A
      sequence: MKLAVFLALAAGVLGVAVQPQSQFRYESP...
  - protein:
      id: B
      sequence: MHHHHHHSSGVDLGTENLYFQSNAMSKGE...
EOF
```

**Step 2: Submit prediction**
```bash
sbatch example_scripts/folding/Boltz2/runners/run_boltz.sh my_complex.yaml --use_msa_server --use_potentials
```

**Step 3: Monitor progress**
```bash
# Check job status
squeue -u $USER -n boltz2

# Watch logs
tail -f logs/boltz_*.out
```

**Step 4: Analyze results**
```bash
# View output directory
ls -lh boltz_results_*/predictions/

# Check confidence scores
cat boltz_results_*/predictions/model_0_confidence.json
```

## Troubleshooting

### Common Issues

**1. "Error: No input file provided"**
- Ensure you're passing the YAML file as the first argument
- Example: `sbatch run_boltz.sh input.yaml`

**2. "Error: Input file does not exist"**
- Verify the YAML file exists at the specified path
- Use absolute paths or correct relative paths
- Check file permissions

**3. "Conda environment not found"**
- Verify `BOLTZ_ENV` path in the script is correct
- Contact admin if environment needs to be installed
- Check: `ls -la /quobyte/jbsiegelgrp/software/envs/boltz`

**4. CUDA out of memory**
- System is too large for available GPU VRAM
- Try increasing memory allocation
- Reduce system size if possible
- Request A100 with 80GB VRAM if available

**5. "Module conda/latest not found"**
- Check if conda module is available: `module avail conda`
- Update module load command if needed

**6. Cache directory errors**
- Verify `BOLTZ_CACHE` path is accessible
- Check disk space: `df -h /quobyte/jbsiegelgrp/databases/boltz/cache`
- Ensure you have write permissions

### Debugging Tips

1. **Validate YAML syntax:**
```bash
python -c "import yaml; yaml.safe_load(open('your_file.yaml'))"
```

2. **Check SMILES validity (for ligands):**
```bash
# Use RDKit to validate SMILES
python -c "from rdkit import Chem; print(Chem.MolFromSmiles('YOUR_SMILES'))"
```

3. **Test interactively:**
```bash
# Request interactive GPU node
srun --partition=gpu-a100 --account=genome-center-grp --gres=gpu:1 --mem=32G --cpus-per-task=16 --pty bash

# Load conda
module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/software/envs/boltz

# Test boltz command
boltz predict --help
```

4. **Check GPU availability:**
```bash
# On compute node
nvidia-smi
```

5. **Verify cache directory:**
```bash
ls -la /quobyte/jbsiegelgrp/databases/boltz/cache/
```

## Best Practices

1. **Test first**: Run a small test prediction before submitting large jobs
2. **Validate input**: Check YAML format and SMILES strings before submission
3. **Use MSA server**: For better predictions, use `--use_msa_server` when available
4. **Naming**: Use descriptive YAML filenames that indicate the system being predicted
5. **Storage**: Plan for output files (typically 50-200 MB per prediction)
6. **Monitor**: Check logs periodically to catch issues early
7. **Documentation**: Keep notes on prediction settings and purposes

## Comparison with Other Folding Tools

| Feature | Boltz2 | AlphaFold 3 | Chai |
|---------|--------|-------------|------|
| **Input format** | YAML | JSON | FASTA |
| **Supported molecules** | Protein, DNA, RNA, ligands | Protein, DNA, RNA, ligands, ions | Protein, DNA, RNA, ligands |
| **Memory requirements** | Medium (8-40 GB VRAM) | High (30-70 GB VRAM) | Medium (10-30 GB VRAM) |
| **Speed** | Medium (1-8 hours) | Slower (3-24 hours) | Faster (30min-4 hours) |
| **Setup complexity** | Medium | High | Low |

**When to use Boltz2:**
- Need protein-ligand complex predictions
- Want balance between speed and accuracy
- Working with nucleic acids or small molecules
- Prefer YAML input format over JSON or FASTA

## Related Documentation

- [chai_to_boltz.py](chai_to_boltz.md) - Convert Chai FASTA format to Boltz2 YAML
- [Chai Documentation](run_chai.md) - Alternative folding tool
- [AlphaFold 3 Documentation](alphafold3.md) - Most accurate predictions for complex systems
- [ColabFold Documentation](colabfold.md) - Fast protein-only predictions

## Additional Resources

- **Boltz GitHub**: https://github.com/jwohlwend/boltz
- **Model Weights**: Automatically downloaded to cache directory on first use
