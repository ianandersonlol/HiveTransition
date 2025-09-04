[View Script: rosetta_fix.py](../rosetta_fix.py)

# Rosetta Script Migration

## Overview
The `rosetta_fix.py` script updates Rosetta job scripts for the new HIVE cluster. It handles the upgrade to Rosetta 3.14, changes binary naming conventions, updates SLURM configurations for CPU-only jobs, and manages partition selection based on job duration.

## What It Does

### 1. Rosetta Version and Path Updates
- **Old path**: `/share/siegellab/software/kschu/Rosetta/main/`
- **New path**: `/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/`
- Updates to Rosetta 3.14 (newer version)

### 2. Binary Name Updates
- **Old format**: `rosetta_scripts.default.linuxgccrelease`
- **New format**: `rosetta_scripts.static.linuxgccrelease`
- Works for ALL Rosetta executables:
  - `relax.default.linuxgccrelease` → `relax.static.linuxgccrelease`
  - `AbinitioRelax.default.linuxgccrelease` → `AbinitioRelax.static.linuxgccrelease`
  - `InterfaceAnalyzer.default.linuxgccrelease` → `InterfaceAnalyzer.static.linuxgccrelease`
  - etc.

### 3. SLURM Partition Management (CPU-only)
- Changes `production` → `low` (default) or `high` (with `--high` flag)
- Removes GPU partitions (Rosetta doesn't use GPUs)
- **Low partition**:
  - Maximum runtime: 3 days
  - Adds `--requeue` flag (auto-requeue if preempted)
  - Lower priority but more available
- **High partition**:
  - Maximum runtime: 30 days
  - No requeue
  - Higher priority but less available

### 4. General Path Updates
- Replaces base paths: `/share/siegellab/` → `/quobyte/jbsiegelgrp/`

## Usage

### Basic Usage (Low Partition)
```bash
python rosetta_fix.py <script_filename>
```

### High Partition Usage
```bash
python rosetta_fix.py <script_filename> --high
```

### Output
- Creates a new file with `_fixed` suffix
- Original file remains unchanged
- Example: `rosetta_job.sh` → `rosetta_job_fixed.sh`

### Examples

1. **Quick job (< 3 days):**
   ```bash
   python rosetta_fix.py relax_structure.sh
   ```

2. **Long job (> 3 days):**
   ```bash
   python rosetta_fix.py large_design_job.sh --high
   ```

## Common Rosetta Script Patterns

### Before Migration
```bash
#!/bin/bash
#SBATCH --job-name=rosetta_relax
#SBATCH --partition=production
#SBATCH --time=7-00:00:00
#SBATCH --array=1-100

# Rosetta paths
ROSETTA=/share/siegellab/software/kschu/Rosetta/main
DATABASE=$ROSETTA/database

# Input/output
INPUT=/share/siegellab/structures/protein.pdb
OUTPUT=/share/siegellab/results/

# Run Rosetta
$ROSETTA/source/bin/relax.default.linuxgccrelease \
    -s $INPUT \
    -out:prefix ${SLURM_ARRAY_TASK_ID}_ \
    -out:path:all $OUTPUT \
    -relax:constrain_relax_to_start_coords
```

### After Migration (Low Partition)
```bash
#!/bin/bash
#SBATCH --job-name=rosetta_relax
#SBATCH --partition=low
#SBATCH --requeue
#SBATCH --time=3-00:00:00
#SBATCH --array=1-100

# Rosetta paths
ROSETTA=/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main
DATABASE=$ROSETTA/database

# Input/output
INPUT=/quobyte/jbsiegelgrp/structures/protein.pdb
OUTPUT=/quobyte/jbsiegelgrp/results/

# Run Rosetta
$ROSETTA/source/bin/relax.static.linuxgccrelease \
    -s $INPUT \
    -out:prefix ${SLURM_ARRAY_TASK_ID}_ \
    -out:path:all $OUTPUT \
    -relax:constrain_relax_to_start_coords
```

## Partition Selection Guide

### Use Low Partition (default) for:
- Jobs under 3 days
- High-throughput screening
- Initial testing
- Jobs that can be requeued

### Use High Partition (`--high`) for:
- Jobs over 3 days
- Critical calculations
- Final production runs
- Jobs that shouldn't be interrupted

## Time Limit Handling

If your script specifies more than 3 days and you use the default (low) partition:

```
WARNING: Time limit was adjusted to 3 days (maximum for low partition).
         Consider using --high flag for longer jobs (up to 30 days).
```

The script automatically adjusts:
- `--time=7-00:00:00` → `--time=3-00:00:00`

## Common Rosetta Applications

### Structure Relaxation
```bash
relax.static.linuxgccrelease \
    -relax:constrain_relax_to_start_coords \
    -relax:coord_constrain_sidechains
```

### Protein Design
```bash
rosetta_scripts.static.linuxgccrelease \
    -parser:protocol design.xml \
    -packing:resfile resfile.txt
```

### Docking
```bash
docking_protocol.static.linuxgccrelease \
    -partners A_B \
    -dock_pert 3 8
```

### Loop Modeling
```bash
loopmodel.static.linuxgccrelease \
    -loops:loop_file loops.txt \
    -loops:remodel perturb_kic
```

## Verification Steps

1. **Check the changes:**
   ```bash
   diff my_rosetta_job.sh my_rosetta_job_fixed.sh
   ```

2. **Verify Rosetta installation:**
   ```bash
   ssh username@hive.hpc.ucdavis.edu
   ls /quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/source/bin/
   ```

3. **Test with a small job:**
   ```bash
   # Quick test with single structure
   sbatch --time=00:10:00 test_job_fixed.sh
   ```

## Troubleshooting

### Binary Not Found
```
/path/to/rosetta_scripts.static.linuxgccrelease: No such file or directory
```
- Check exact binary name in the Rosetta bin directory
- Ensure path is correct
- Some specialized apps might have different names

### Time Limit Exceeded
```
TIMEOUT: Job exceeded time limit
```
- Use `--high` flag for jobs over 3 days
- Break large jobs into smaller chunks
- Use job arrays for parallel processing

### Requeue Issues
```
Job was requeued but didn't restart
```
- Check if output files prevent restart
- Ensure Rosetta can resume from checkpoints
- Consider using `-restore_from_checkpoint`

### Permission Denied
```
Permission denied: /quobyte/jbsiegelgrp/...
```
- Ensure output directory exists
- Check write permissions
- Create project directories in your space

## Performance Tips

1. **Job Arrays**: Use for embarrassingly parallel tasks
2. **Checkpoint Files**: Enable for long runs
3. **Memory Usage**: Rosetta can be memory intensive
4. **Output Management**: Use appropriate file prefixes

## Rosetta-Specific Flags

Common flags that work with both versions:
- `-database`: Path to Rosetta database
- `-out:prefix`: Output file prefix
- `-out:path:all`: Output directory
- `-nstruct`: Number of structures
- `-restore_from_checkpoint`: Resume interrupted jobs

## Important Notes

1. **No GPU Support**: Rosetta is CPU-only
2. **Version Change**: Now using Rosetta 3.14
3. **Binary Format**: Static binaries for better compatibility
4. **Database Path**: Automatically set relative to main directory

## Common Issues and Solutions

### Issue: Old Scripts Reference Rosetta3
Some scripts might use:
```bash
ROSETTA3=/some/path
```
Update to:
```bash
ROSETTA=/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main
```

### Issue: Custom Executables
If you compiled custom Rosetta apps:
- These need to be recompiled with Rosetta 3.14
- Contact system admin for compilation requests

### Issue: Protocol Changes
Some protocols may have changed between versions:
- Check Rosetta 3.14 documentation
- Test with small examples first

## Related Scripts
- Use `colab_fix.py` for ColabFold scripts
- Use `ligandmpnn_fix.py` for LigandMPNN scripts
- Use `rfdiffusion_fix.py` for RFdiffusion scripts
- Use `broken.py` to report issues