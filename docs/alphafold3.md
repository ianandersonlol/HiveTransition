# AlphaFold 3 Submission Scripts

## Overview

These scripts facilitate running AlphaFold 3 predictions on HPC clusters using SLURM. AlphaFold 3 is the latest version of DeepMind's protein structure prediction system, capable of predicting structures for proteins, nucleic acids, small molecules, ions, and modified residues.

Two submission modes are provided:
- **Single prediction**: Submit one JSON file for structure prediction
- **Bulk predictions**: Submit multiple JSON files as a SLURM array job

## Scripts

### submit_af3_single.sh

Submits a single AlphaFold 3 prediction job.

**Usage:**
```bash
sbatch submit_af3_single.sh <path_to_json_file>
```

**Example:**
```bash
sbatch submit_af3_single.sh /path/to/protein_complex.json
```

**Features:**
- GPU monitoring with detailed resource usage tracking
- Automatic output directory creation
- Real-time GPU VRAM and utilization logging
- Runtime statistics and job efficiency reporting
- Logs cleaned up automatically after summarization

### submit_af3_bulk.py

Submits multiple AlphaFold 3 predictions as a SLURM array job.

**Usage:**
```bash
python submit_af3_bulk.py <directory_path>
```

**Example:**
```bash
python submit_af3_bulk.py /path/to/json_files/
```

**Features:**
- Automatic discovery of all JSON files in directory
- Generates SLURM array job script dynamically
- One array task per JSON file for parallel processing
- Centralized log management
- Same GPU monitoring as single submission
- Automatic job submission with status tracking

## Input Requirements

### JSON Input Format

AlphaFold 3 requires JSON input files specifying the molecular system to predict. Each JSON file defines:
- Protein sequences
- Nucleic acid sequences (if applicable)
- Small molecule ligands (if applicable)
- Ions and cofactors (if applicable)
- Modified residues (if applicable)

**Basic example (protein monomer):**
```json
{
  "name": "my_protein",
  "sequences": [
    {
      "protein": {
        "id": ["A"],
        "sequence": "MKLAVFLALAAGVLGVAVQPQS..."
      }
    }
  ],
  "modelSeeds": [1],
  "dialect": "alphafold3",
  "version": 1
}
```

**Example (protein-ligand complex):**
```json
{
  "name": "protein_ligand_complex",
  "sequences": [
    {
      "protein": {
        "id": ["A"],
        "sequence": "MKLAVFLALAAGVLGVAVQPQS..."
      }
    },
    {
      "ligand": {
        "id": ["B"],
        "ccdCodes": ["ATP"]
      }
    }
  ],
  "modelSeeds": [1],
  "dialect": "alphafold3",
  "version": 1
}
```

For detailed JSON format specifications, see the [AlphaFold 3 documentation](https://github.com/google-deepmind/alphafold3).

### File Naming

- JSON files should have `.json` extension
- Avoid spaces in filenames (use underscores instead)
- Use descriptive names (becomes part of output directory name)

## Output Structure

### Single Job Output

```
<json_directory>/
├── <safe_name>_output/          # Prediction results
│   ├── <name>_model.cif         # Predicted structure (mmCIF)
│   ├── <name>_model.json        # Prediction metadata
│   ├── <name>_confidence.json   # Confidence scores
│   ├── <name>_ranking_scores.json
│   └── ...
└── logs/
    └── <safe_name>_gpu_monitor_*.csv (deleted after summary)
```

### Bulk Job Output

```
<input_directory>/
├── <directory_name>_output/     # Base output directory
│   ├── <file1_safe_name>/       # Individual prediction outputs
│   │   └── [same as single job]
│   ├── <file2_safe_name>/
│   │   └── [same as single job]
│   └── ...
├── logs/                        # Centralized logs
│   ├── json_files_list.txt      # List of JSON files for array
│   ├── af3_<jobid>_<arrayid>.txt  # Combined stdout/stderr per task
│   └── <name>_gpu_monitor_*.csv (deleted after summary)
└── af3_array_job.sbatch         # Generated SLURM script
```

### Output Files Explained

**Structure Files:**
- `*_model.cif`: Predicted structure in mmCIF format (main output)
- `*_model.pdb`: Predicted structure in PDB format (if generated)

**Confidence Scores:**
- `*_confidence.json`: Per-residue confidence scores (pLDDT for proteins, similar for nucleic acids)
- `*_ranking_scores.json`: Overall model quality metrics

**Metadata:**
- `*_model.json`: Prediction settings and parameters
- `*_summary_confidences.json`: Summary statistics

## Resource Requirements

### SLURM Settings (Default)

```bash
#SBATCH --partition=low          # Queue name
#SBATCH --time=24:00:00          # Max runtime (24 hours)
#SBATCH --cpus-per-task=8        # CPU cores
#SBATCH --mem=64G                # RAM
#SBATCH --gres=gpu:1             # GPUs (1 required)
```

### Typical Resource Usage

**Small proteins (<200 residues):**
- Runtime: 1-3 hours
- Peak VRAM: 10-20 GB
- CPU efficiency: 20-40%

**Medium proteins (200-500 residues):**
- Runtime: 3-6 hours
- Peak VRAM: 20-35 GB
- CPU efficiency: 30-50%

**Large proteins/complexes (>500 residues):**
- Runtime: 6-12 hours
- Peak VRAM: 35-60 GB
- CPU efficiency: 40-60%

**Note:** AlphaFold 3 is more memory-intensive than AlphaFold 2. Ensure adequate GPU VRAM is available.

## GPU Monitoring

Both scripts include real-time GPU monitoring that tracks:
- Timestamp
- GPU name
- Memory used (VRAM)
- Memory total
- GPU utilization (%)

Monitoring data is collected every 5 seconds and summarized at job completion:

```
=== Resource Usage Summary ===
GPU: NVIDIA A100-SXM4-80GB
Peak VRAM usage: 42.3 GB / 80.0 GB
Average GPU utilization: 87.5%

CPU/Memory efficiency (from SLURM):
CPU Efficiency: 45.2% of 8 cores
Memory Efficiency: 78.5% of 64.00 GB
Memory Utilized: 50.24 GB
==============================
```

This information helps optimize resource allocation for future jobs.

## Monitoring Jobs

### Check Job Status

**Single job:**
```bash
squeue -u $USER -n af3_single
```

**Array job:**
```bash
# View all array tasks
squeue -j <job_id> -t all

# View specific array task
squeue -j <job_id>_<array_id>
```

### View Logs

**Single job:**
```bash
# View output log
tail -f af3_<job_id>.txt
```

**Array job:**
```bash
# Monitor all tasks
tail -f logs/af3_*_*.txt

# Monitor specific task
tail -f logs/af3_<job_id>_<array_id>.txt
```

### Cancel Jobs

**Single job:**
```bash
scancel <job_id>
```

**Array job:**
```bash
# Cancel entire array
scancel <job_id>

# Cancel specific array task
scancel <job_id>_<array_id>

# Cancel range of tasks
scancel <job_id>_[1-10]
```

## Configuration

### System Paths

Both scripts use the following paths (modify if your installation differs):

```bash
# AlphaFold 3 installation
AF3_DIR="/quobyte/jbsiegelgrp/software/alphafold3"

# Singularity container
CONTAINER="${AF3_DIR}/alphafold3.sif"

# Model parameters
MODEL_DIR="${AF3_DIR}"  # Contains model weights

# Databases
DB_DIR="${AF3_DIR}/public_databases"  # Genetic databases
```

### Modifying Resource Requests

Edit the `#SBATCH` directives at the top of the scripts:

**Increase runtime:**
```bash
#SBATCH --time=48:00:00  # 48 hours
```

**Request specific GPU:**
```bash
#SBATCH --gres=gpu:a100:1  # Request A100 specifically
```

**Increase memory:**
```bash
#SBATCH --mem=128G  # 128 GB RAM
```

**Change partition:**
```bash
#SBATCH --partition=high  # Higher priority queue
```

## Advanced Usage

### Using Different Partitions

The scripts default to `--partition=low`. For faster turnaround:

```bash
# Edit script to use different partition
#SBATCH --partition=gpu-a100
#SBATCH --account=genome-center-grp
```

### Custom AlphaFold 3 Options

To pass additional flags to AlphaFold 3, modify the `singularity exec` command:

**Example - Control number of predictions:**
```bash
singularity exec \
    [bindings] \
    python /app/alphafold/run_alphafold.py \
    --json_path="/input/$JSON_FILE" \
    --model_dir=/models \
    --output_dir=/output \
    --db_dir=/databases \
    --num_predictions=5  # Generate 5 models instead of 1
```

**Example - Use specific model:**
```bash
    --model_preset=multimer  # For protein complexes
```

### Restarting Failed Predictions

If a prediction fails, you can resubmit just that task:

**For array jobs:**
```bash
# Check which tasks failed
sacct -j <job_id> --format=JobID,State,ExitCode

# Resubmit specific failed task
sbatch --array=<task_id> af3_array_job.sbatch
```

### Processing Large Batches

For very large numbers of JSON files, consider:

1. **Split into smaller batches:**
```bash
# Create subdirectories with ~50-100 files each
mkdir batch1 batch2 batch3
mv file_001-100.json batch1/
mv file_101-200.json batch2/
mv file_201-300.json batch3/

# Submit separate array jobs
python submit_af3_bulk.py batch1/
python submit_af3_bulk.py batch2/
python submit_af3_bulk.py batch3/
```

2. **Adjust SLURM array limits:**
```bash
# Edit generated script to limit concurrent tasks
#SBATCH --array=1-200%20  # Max 20 concurrent tasks
```

## Troubleshooting

### Common Issues

**1. "Error: JSON file not found"**
- Check file path is correct
- Ensure file has `.json` extension
- Use absolute paths or proper relative paths

**2. "No JSON files found in directory"**
- Verify directory path is correct
- Ensure JSON files are in the top level (not subdirectories)
- Check file permissions

**3. "Error: Could not get JSON file for array task"**
- File list may be corrupted
- Check `logs/json_files_list.txt` exists and has correct number of lines
- Verify array task ID matches number of files

**4. CUDA out of memory**
- System is too large for available GPU VRAM
- Try using GPU with more memory (A100 80GB vs 40GB)
- Reduce system size if possible

**5. "Module apptainer/latest not found"**
- Check if Singularity/Apptainer is installed
- Load correct module: `module load singularity` or similar
- Update module load command in script

**6. Container not found**
- Verify `AF3_DIR` path is correct
- Check `alphafold3.sif` file exists
- Ensure you have read permissions

### Debugging Tips

1. **Test JSON file validity:**
```bash
# Check JSON syntax
python -m json.tool your_file.json
```

2. **Run interactively:**
```bash
# Request interactive GPU node
srun --partition=low --gres=gpu:1 --mem=64G --cpus-per-task=8 --pty bash

# Load modules
module load apptainer/latest

# Test singularity command manually
singularity exec --nv /path/to/alphafold3.sif python --version
```

3. **Check container contents:**
```bash
singularity exec alphafold3.sif ls -la /app/alphafold/
```

4. **Verify GPU access:**
```bash
# Inside container
singularity exec --nv alphafold3.sif nvidia-smi
```

5. **Check database availability:**
```bash
ls -la /quobyte/jbsiegelgrp/software/alphafold3/public_databases/
```

## Expected Timeline

### Single Predictions

| System Size | Runtime | VRAM Usage | Typical Use Case |
|------------|---------|------------|------------------|
| Small (<200 residues) | 1-3 hours | 10-20 GB | Single domain proteins |
| Medium (200-500 residues) | 3-6 hours | 20-35 GB | Multi-domain proteins |
| Large (500-1000 residues) | 6-12 hours | 35-60 GB | Protein complexes |
| Very Large (>1000 residues) | 12-24 hours | 50-70 GB | Large complexes/assemblies |

### Bulk Predictions

For array jobs, total time depends on:
- Number of concurrent GPUs available
- Queue wait time
- Individual prediction runtime

**Example:**
- 100 JSON files
- Average 3 hours per prediction
- 10 GPUs available simultaneously
- **Total wall time**: ~30-40 hours (including queue time)

## Best Practices

1. **Test first**: Run 1-2 predictions before submitting large array jobs
2. **Validate JSON**: Check JSON format before submission
3. **Monitor resources**: Review GPU usage summary to optimize future jobs
4. **Storage**: Each prediction generates ~100-500 MB of output; plan accordingly
5. **Naming**: Use systematic, descriptive JSON filenames
6. **Backup**: Keep original JSON files after predictions complete
7. **Document**: Record prediction settings and parameters in filenames or logs

## Comparison with AlphaFold 2

**Key Differences:**

| Feature | AlphaFold 2 | AlphaFold 3 |
|---------|-------------|-------------|
| **Input format** | FASTA | JSON |
| **Supported molecules** | Proteins only | Proteins, DNA, RNA, ligands, ions, modified residues |
| **Memory requirements** | Lower (~20-40 GB VRAM) | Higher (~30-70 GB VRAM) |
| **Runtime** | Faster | Slower (more complex) |
| **Database search** | Required (MSA generation) | Optional/built-in |
| **Output format** | PDB | mmCIF (CIF) |

**When to use which:**
- **AlphaFold 2**: Pure protein structure prediction, faster results
- **AlphaFold 3**: Protein-ligand complexes, nucleic acids, modified residues, higher accuracy

## Related Documentation

- [ColabFold Documentation](../../colabfold.md) - Alternative/complementary folding pipeline
- [AlphaFold 2 Scripts](../alphafold2/) - Previous version scripts (if available)
- [MPNNP Pipeline](../../../docs/mpnnp_pipeline.md) - Includes structure prediction as part of design pipeline

## Citation

If you use AlphaFold 3 in your research, please cite:

```
Abramson, J., Adler, J., Dunger, J., Evans, R., Green, T., Pritzel, A., ... & Jumper, J. M. (2024).
Accurate structure prediction of biomolecular interactions with AlphaFold 3.
Nature. https://doi.org/10.1038/s41586-024-07487-w
```

## Additional Resources

- **AlphaFold 3 GitHub**: https://github.com/google-deepmind/alphafold3
- **AlphaFold Server**: https://alphafoldserver.com/ (web interface)
- **JSON Format Documentation**: https://github.com/google-deepmind/alphafold3/blob/main/docs/input.md

## Contact

For questions or issues with these scripts, please contact the Siegel Lab.
