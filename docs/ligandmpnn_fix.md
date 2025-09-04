[View Script: ligandmpnn_fix.py](../../ligandmpnn_fix.py)

# LigandMPNN Script Migration

## Overview
The `ligandmpnn_fix.py` script updates LigandMPNN job scripts to work on the new HIVE cluster. It handles installation path updates, SLURM configuration changes, and general path migrations.

## What It Does

### 1. LigandMPNN Installation Path Updates
- Detects various LigandMPNN installation locations:
  - `/toolbox/ligandMPNN`
  - `/toolbox/LigandMPNN`
  - Other case variations
- Updates all to: `/quobyte/jbsiegelgrp/ligandMPNN`

### 2. SLURM Configuration Updates
- **Partition changes:**
  - `jbsiegel-gpu` → `gpu-a100`
- **Account addition:**
  - Adds `--account=genome-center-grp` for GPU jobs if not present
- Handles both long form (`--partition=`) and short form (`-p`) flags

### 3. General Path Updates
- Replaces base paths: `/share/siegellab/` → `/quobyte/jbsiegelgrp/`
- Preserves subdirectory structure

## Usage

### Basic Usage
```bash
python ligandmpnn_fix.py <script_filename>
```

### Output
- Creates a new file with `_fixed` suffix
- Original file remains unchanged
- Example: `ligandmpnn_job.sh` → `ligandmpnn_job_fixed.sh`

### Examples

1. **Fix a single script:**
   ```bash
   python ligandmpnn_fix.py design_protein.sh
   ```

2. **Fix all LigandMPNN scripts:**
   ```bash
   for script in ligandmpnn_*.sh; do
       python ligandmpnn_fix.py "$script"
   done
   ```

## Common LigandMPNN Script Patterns

### Before Migration
```bash
#!/bin/bash
#SBATCH --job-name=ligandmpnn
#SBATCH --partition=jbsiegel-gpu
#SBATCH --gres=gpu:1
#SBATCH --time=4:00:00

# Setup paths
LIGANDMPNN_DIR=/toolbox/ligandMPNN
PDB_PATH=/share/siegellab/designs/protein.pdb

# Activate environment and run
cd $LIGANDMPNN_DIR
python run.py \
    --pdb_path $PDB_PATH \
    --out_folder /share/siegellab/results/
```

### After Migration
```bash
#!/bin/bash
#SBATCH --job-name=ligandmpnn
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --time=4:00:00

# Setup paths
LIGANDMPNN_DIR=/quobyte/jbsiegelgrp/ligandMPNN
PDB_PATH=/quobyte/jbsiegelgrp/designs/protein.pdb

# Activate environment and run
cd $LIGANDMPNN_DIR
python run.py \
    --pdb_path $PDB_PATH \
    --out_folder /quobyte/jbsiegelgrp/results/
```

## What Gets Changed

### Installation Paths
- `/toolbox/ligandMPNN` → `/quobyte/jbsiegelgrp/ligandMPNN`
- `/toolbox/LigandMPNN` → `/quobyte/jbsiegelgrp/LigandMPNN`
- Case variations are preserved in the destination

### Python Script Paths
- Updates paths to LigandMPNN Python scripts
- Maintains relative paths within LigandMPNN directory

### Data Paths
- Input PDB file paths
- Output directories
- Chain specification files
- Fixed position files

## LigandMPNN-Specific Considerations

### Environment Setup
LigandMPNN typically requires:
```bash
# Load required modules
module load conda/latest
module load cuda/12.6.2

# Activate the environment (if using conda)
conda activate ligandmpnn_env
```

### Common Parameters
The script preserves all LigandMPNN parameters:
- `--pdb_path`: Input structure
- `--out_folder`: Output directory
- `--num_seq_per_target`: Number of sequences
- `--sampling_temp`: Sampling temperature
- `--seed`: Random seed
- `--batch_size`: GPU batch size

### GPU Memory Considerations
- A100 GPUs have more memory than older GPUs
- Can increase batch size for better performance
- Typical batch sizes: 8-32 depending on protein size

## Verification Steps

1. **Check the migration:**
   ```bash
   diff design_script.sh design_script_fixed.sh
   ```

2. **Verify LigandMPNN installation:**
   ```bash
   ssh username@hive.hpc.ucdavis.edu
   ls /quobyte/jbsiegelgrp/ligandMPNN/
   ```

3. **Test run:**
   ```bash
   # Submit a test job with a small protein
   sbatch design_script_fixed.sh
   ```

## Troubleshooting

### Import Errors
```
ModuleNotFoundError: No module named 'torch'
```
- Ensure conda environment is activated
- Check if PyTorch is installed with CUDA support

### GPU Not Found
```
RuntimeError: No CUDA GPUs are available
```
- Verify `--gres=gpu:1` is in SBATCH headers
- Check partition is `gpu-a100`
- Ensure account is set correctly

### Path Not Found
```
FileNotFoundError: [Errno 2] No such file or directory
```
- Verify all paths have been updated
- Check that input files exist in new locations
- Ensure output directories are created

## Performance Tips

1. **Batch Size**: Increase for A100 GPUs (try 16-32)
2. **Multiple Sequences**: Generate more sequences per job
3. **Chain Specifications**: Use JSON files for complex designs
4. **Fixed Positions**: Specify key residues to maintain

## Important Notes

1. **GPU Required**: LigandMPNN requires GPU for reasonable performance
2. **Memory Usage**: Larger proteins need more GPU memory
3. **Output Organization**: Create structured output directories
4. **Version Compatibility**: Ensure PDB files are properly formatted

## Related Scripts
- Use `colab_fix.py` for ColabFold scripts
- Use `rfdiffusion_fix.py` for RFdiffusion scripts
- Use `broken.py` to report issues