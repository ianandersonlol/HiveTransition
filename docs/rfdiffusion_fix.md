# RFdiffusion Script Migration

## Overview
The `rfdiffusion_fix.py` script updates RFdiffusion job scripts to work on the new HIVE cluster. It handles diverse installation locations, conda environment updates, and ensures all scripts point to the standardized RFdiffusion installation.

## What It Does

### 1. RFdiffusion Installation Path Updates
Detects and updates various RFdiffusion locations:
- `/home/username/RFdiffusion`
- `/share/*/RFdiffusion`
- `/toolbox/RFdiffusion`
- `~/RFdiffusion`
- `./RFdiffusion`
- `$HOME/RFdiffusion`

All paths are updated to: `/quobyte/jbsiegelgrp/software/RFdiffusion`

### 2. Conda Environment Updates
- Detects RFdiffusion-related conda environments:
  - Names containing: `se3`, `rfdiff`, `rf-diff`, `diffusion`
- Updates all to: `conda activate /quobyte/jbsiegelgrp/software/envs/SE3nv`

### 3. SLURM Configuration Updates
- **Partition changes:**
  - `jbsiegel-gpu` → `gpu-a100`
- **Account addition:**
  - Adds `--account=genome-center-grp` for GPU jobs if not present

### 4. General Path Updates
- Replaces base paths: `/share/siegellab/` → `/quobyte/jbsiegelgrp/`

## Usage

### Basic Usage
```bash
python rfdiffusion_fix.py <script_filename>
```

### Output
- Creates a new file with `_fixed` suffix
- Original file remains unchanged
- Example: `rfdiffusion_job.sh` → `rfdiffusion_job_fixed.sh`

### Examples

1. **Fix a single script:**
   ```bash
   python rfdiffusion_fix.py generate_backbone.sh
   ```

2. **Fix all RFdiffusion scripts:**
   ```bash
   for script in rf_*.sh; do
       python rfdiffusion_fix.py "$script"
   done
   ```

## Common RFdiffusion Script Patterns

### Before Migration
```bash
#!/bin/bash
#SBATCH --job-name=rfdiffusion
#SBATCH --partition=jbsiegel-gpu
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00

# Setup environment
conda activate ~/miniconda3/envs/SE3nv
cd ~/RFdiffusion

# Run RFdiffusion
python ./scripts/run_inference.py \
    inference.output_prefix=/share/siegellab/outputs/design \
    inference.num_designs=100 \
    'contigmap.contigs=[A1-50/0 100-100]' \
    inference.ckpt_path=./models/RF_structure_prediction_model.pt
```

### After Migration
```bash
#!/bin/bash
#SBATCH --job-name=rfdiffusion
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
#SBATCH --gres=gpu:1
#SBATCH --time=12:00:00

# Setup environment
conda activate /quobyte/jbsiegelgrp/software/envs/SE3nv
cd /quobyte/jbsiegelgrp/software/RFdiffusion

# Run RFdiffusion
python ./scripts/run_inference.py \
    inference.output_prefix=/quobyte/jbsiegelgrp/outputs/design \
    inference.num_designs=100 \
    'contigmap.contigs=[A1-50/0 100-100]' \
    inference.ckpt_path=./models/RF_structure_prediction_model.pt
```

## What Gets Changed

### Script Locations
- `run_inference.py` paths
- Model checkpoint paths
- Helper script locations

### Environment Activation
- Various conda environment names → `/quobyte/jbsiegelgrp/software/envs/SE3nv`
- Handles different activation patterns

### Output Paths
- Design output directories
- Log file locations
- Temporary file paths

## RFdiffusion-Specific Parameters

The script preserves all RFdiffusion parameters:

### Inference Parameters
- `inference.output_prefix`: Where designs are saved
- `inference.num_designs`: Number of designs to generate
- `inference.ckpt_path`: Model checkpoint location
- `inference.seed`: Random seed for reproducibility

### Contig Map Specifications
- `contigmap.contigs`: Structure specification
- `contigmap.inpaint_seq`: Sequence constraints
- `contigmap.provide_seq`: Fixed sequence regions

### Diffusion Parameters
- `denoiser.noise_scale_ca`: CA noise scaling
- `denoiser.noise_scale_frame`: Frame noise scaling
- `diffuser.T`: Number of diffusion steps

### Potentials (if used)
- `potentials.guide_scale`: Guidance strength
- `potentials.guiding_potentials`: List of potentials
- `potentials.olig_inter_all`: Oligomer interface

## Advanced Usage Examples

### Motif Scaffolding
```bash
'contigmap.contigs=[A1-10/0 15-25/A11-25/15-25/0 A26-40/0 10-20]'
```

### Binder Design
```bash
inference.input_pdb=target.pdb
'contigmap.contigs=[B1-100/0 A1-50]'
```

### Symmetric Oligomers
```bash
inference.sym="C3"
'contigmap.contigs=[A1-150]'
```

## Verification Steps

1. **Check the changes:**
   ```bash
   diff backbone_design.sh backbone_design_fixed.sh
   ```

2. **Verify RFdiffusion installation:**
   ```bash
   ssh username@hive.hpc.ucdavis.edu
   ls /quobyte/jbsiegelgrp/software/RFdiffusion/
   ```

3. **Check environment:**
   ```bash
   conda activate /quobyte/jbsiegelgrp/software/envs/SE3nv
   python -c "import torch; print(torch.cuda.is_available())"
   ```

## Troubleshooting

### Environment Not Found
```
CondaEnvironmentNotFoundError: Could not find environment
```
- Use the full path: `/quobyte/jbsiegelgrp/software/envs/SE3nv`
- Don't create your own SE3nv environment

### Model Checkpoint Issues
```
FileNotFoundError: Model checkpoint not found
```
- Models are in: `/quobyte/jbsiegelgrp/software/RFdiffusion/models/`
- Use relative paths from RFdiffusion directory

### GPU Memory Errors
```
RuntimeError: CUDA out of memory
```
- A100 GPUs have 40GB memory (more than most)
- Can increase batch size or number of designs
- For very large proteins, may still need to reduce batch

### Import Errors
```
ModuleNotFoundError: No module named 'rf_diffusion'
```
- Ensure you're in the RFdiffusion directory
- Environment must be activated first

## Performance Optimization

1. **Batch Processing**: Generate multiple designs per job
2. **GPU Utilization**: A100s can handle larger proteins
3. **Inference Speed**: Use fewer diffusion steps for faster results
4. **Memory Management**: Clear cache between designs if needed

## Important Notes

1. **GPU Required**: RFdiffusion requires GPU
2. **Model Files**: Large model files are shared in the software directory
3. **Output Organization**: Create project-specific output directories
4. **Contig Syntax**: Must be properly quoted in bash scripts

## Common Issues and Solutions

### Issue: Slow Performance
- Ensure using A100 GPU (check with `nvidia-smi`)
- Reduce number of diffusion steps
- Use appropriate batch size

### Issue: Designs Don't Fold
- Check contig map syntax
- Verify input PDB (if using)
- Consider adjusting noise scales

### Issue: Permission Denied
- Output directories must be in your quobyte space
- Cannot write to software directory

## Related Scripts
- Use `colab_fix.py` for ColabFold scripts
- Use `ligandmpnn_fix.py` for LigandMPNN scripts
- Use `rosetta_fix.py` for Rosetta scripts
- Use `broken.py` to report issues