# ColabFold Script Migration

## Overview
The `colab_fix.py` script updates ColabFold job scripts to work on the new HIVE cluster. It handles path migrations, SLURM configuration updates, and ensures scripts point to the correct ColabFold installation.

## What It Does

### 1. ColabFold PATH Updates
- Changes old path: `/toolbox/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH`
- To new path: `/quobyte/jbsiegelgrp/software/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH`
- Preserves any export statements or other context

### 2. SLURM Configuration Updates
- **Partition changes:**
  - `jbsiegel-gpu` → `gpu-a100`
- **Account addition:**
  - Adds `--account=genome-center-grp` for GPU jobs if not present
- Handles both long form (`--partition=`) and short form (`-p`) flags

### 3. General Path Updates
- Replaces base paths: `/share/siegellab/` → `/quobyte/jbsiegelgrp/`
- Preserves subdirectory structure (e.g., `/share/siegellab/data/proteins/` becomes `/quobyte/jbsiegelgrp/data/proteins/`)

## Usage

### Basic Usage
```bash
python colab_fix.py <script_filename>
```

### Output
- Creates a new file with `_fixed` suffix
- Original file remains unchanged
- Example: `colabfold_job.sh` → `colabfold_job_fixed.sh`

### Examples

1. **Fix a single script:**
   ```bash
   python colab_fix.py my_colabfold_job.sh
   ```

2. **Fix multiple scripts:**
   ```bash
   for script in *.sh; do
       python colab_fix.py "$script"
   done
   ```

## Common ColabFold Script Patterns

### Before Migration
```bash
#!/bin/bash
#SBATCH --job-name=colabfold
#SBATCH --partition=jbsiegel-gpu
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00

# Setup ColabFold
export PATH=/toolbox/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH

# Input/output paths
INPUT=/share/siegellab/projects/protein.fasta
OUTPUT=/share/siegellab/results/

# Run ColabFold
colabfold_batch $INPUT $OUTPUT
```

### After Migration
```bash
#!/bin/bash
#SBATCH --job-name=colabfold
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --time=24:00:00

# Setup ColabFold
export PATH=/quobyte/jbsiegelgrp/software/LocalColabFold/localcolabfold/colabfold-conda/bin:$PATH

# Input/output paths
INPUT=/quobyte/jbsiegelgrp/projects/protein.fasta
OUTPUT=/quobyte/jbsiegelgrp/results/

# Run ColabFold
colabfold_batch $INPUT $OUTPUT
```

## What Gets Changed

### PATH Variables
- Any occurrence of the old ColabFold path is updated
- Works with various export formats:
  - `export PATH=/toolbox/LocalColabFold/...`
  - `PATH=/toolbox/LocalColabFold/...`
  - `export PATH="/toolbox/LocalColabFold/..."`

### SLURM Headers
- Partition updates for GPU access
- Account addition for proper billing
- Preserves all other SLURM options

### File Paths
- Data paths from old storage to new
- Log file paths
- Output directories

## Verification Steps

After running the script:

1. **Check the changes:**
   ```bash
   diff my_script.sh my_script_fixed.sh
   ```

2. **Verify ColabFold path exists:**
   ```bash
   ssh username@hive.hpc.ucdavis.edu
   ls /quobyte/jbsiegelgrp/software/LocalColabFold/
   ```

3. **Test with a small job:**
   - Use a single sequence first
   - Verify GPU allocation works
   - Check output paths are accessible

## Troubleshooting

### Script Not Found
```
Error: File 'script.sh' not found.
```
- Verify the script name and path
- Use full path if needed

### No Changes Made
```
Changes made:
  No changes were needed.
```
- Script might already be updated
- Check if paths are different than expected

### GPU Access Issues
- Verify account is set: `--account=genome-center-grp`
- Check GPU availability: `sinfo -p gpu-a100`
- Ensure you have GPU access permissions

## Important Notes

1. **GPU Requirements**: ColabFold requires GPU access for optimal performance
2. **Time Limits**: Adjust based on number of sequences and their length
3. **Output Directories**: Ensure output paths exist and are writable
4. **Module Loading**: May need to load CUDA modules on HIVE

## Related Scripts
- Use `ligandmpnn_fix.py` for LigandMPNN scripts
- Use `rfdiffusion_fix.py` for RFdiffusion scripts
- Use `broken.py` to report issues