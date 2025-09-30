# MPNNP Pipeline Documentation

## Overview

The MPNNP (MSA-Protein-MPNN-Prediction) Pipeline is a unified, automated protein design workflow that takes a protein sequence and produces structurally-validated designed variants. The pipeline integrates sequence conservation analysis, structure prediction, and rational protein design using state-of-the-art tools.

**Based on the methodology described in:**
King et al., "Computational Stabilization of a Non-Heme Iron Enzyme Enables Efficient Evolution of New Function"
Brianne R. King, Kiera H. Sumida, Jessica L. Caruso, David Baker, Jesse G. Zalatan
*Angewandte Chemie International Edition* (2024)
https://doi.org/10.1002/anie.202414705

## Pipeline Stages

The pipeline consists of four major stages:

### 1. MSA Generation & Conservation Analysis
- **HHblits**: Generates multiple sequence alignments with progressive E-value thresholds (1e-50, 1e-30, 1e-10, 1e-4)
- **HHfilter**: Filters MSA by identity (90%), coverage (50%), and query identity (30%)
- **Conservation Analysis**: Identifies conserved residues at 80% threshold using frequency analysis

### 2. Reference Structure Prediction
- **ColabFold**: Predicts the reference structure from the input sequence
- Runs in parallel with conservation analysis for efficiency
- Uses model order 3, 1 model, 6 recycles

### 3. Protein Design with LigandMPNN
- **Design Generation**: Creates sequence variants using LigandMPNN
- Fixes conserved residues identified from MSA analysis
- Generates designs at multiple temperatures (0.1, 0.2, 0.3)
- Produces 64 sequences per temperature (4 batches × 16 sequences)
- Omits cysteine residues by default

### 4. Structure Prediction & Validation
- **ColabFold Monomer**: Predicts structures for all designed sequences
- **PyMOL RMSD Analysis**: Compares designed structures to reference
- Ranks designs by structural similarity (Cα RMSD)

## Usage

### Basic Usage

```bash
python run_pipeline.py input.fasta
```

### Specify Design Chain

```bash
python run_pipeline.py input.fasta --chain A
```

### Dry Run (Generate Scripts Only)

```bash
python run_pipeline.py input.fasta --dry-run
```

## Input Requirements

- **FASTA file**: Single protein sequence in FASTA format
- **File extensions**: `.fa`, `.fasta`, or `.faa`
- **Format**: Standard FASTA with header line starting with `>`

Example:
```
>my_protein
MKLAVFLALAAGVLGVAVQPQS...
```

## Output Structure

```
jobs/JOBNAME/
├── logs/                    # All SLURM job logs
├── input.fa                 # Copied input FASTA
├── hhblits/                 # MSA files and conservation data
│   ├── {name}_4.a3m        # Final MSA (E=1e-4)
│   ├── {name}_id90cov50qid30.a3m  # Filtered MSA
│   └── {name}_conserved_residues.xlsx  # Conservation analysis
├── reference/               # Reference structure
│   └── colabfold_output/   # ColabFold predictions
├── ligandmpnn/              # Design sequences
│   ├── T0.1/               # Temperature 0.1 designs
│   ├── T0.2/               # Temperature 0.2 designs
│   ├── T0.3/               # Temperature 0.3 designs
│   └── cf_tasks.txt        # List of sequences for prediction
├── colabfold/               # Predicted structures for designs
│   └── colabfold_output/
├── pymol_analysis/          # RMSD comparison results
│   └── {name}_rmsd_results.csv
└── cache/                   # Temporary cache files
```

## Key Output Files

### Conservation Analysis
- **Location**: `jobs/JOBNAME/hhblits/{name}_conserved_residues.xlsx`
- **Content**: Excel file with:
  - `fraction_conserved`: Threshold used (80%)
  - `residue_list`: Comma-separated 1-based residue indices

### Reference Structure
- **Location**: `jobs/JOBNAME/reference/colabfold_output/`
- **Files**: `*_unrelaxed_rank_001*.pdb` - Best predicted structure

### Design Sequences
- **Location**: `jobs/JOBNAME/ligandmpnn/T{temp}/seqs/*.fa`
- **Format**: Multi-FASTA with all designs at each temperature

### RMSD Results
- **Location**: `jobs/JOBNAME/pymol_analysis/{name}_rmsd_results.csv`
- **Content**: CSV with columns:
  - `structure`: PDB filename
  - `temperature`: LigandMPNN temperature used
  - `sequence_id`: Design sequence ID
  - `chain`: Design chain
  - `rmsd_angstroms`: Cα RMSD to reference (Å)
  - `path`: Full path to structure file

## Configuration

All parameters are hardcoded at the top of `run_pipeline.py`:

### System Paths
```python
HHBLITS_DATABASE = "/quobyte/jbsiegelgrp/databases/hhsuite_databases/..."
LIGANDMPNN_ROOT = "/quobyte/jbsiegelgrp/software/LigandMPNN"
LIGANDMPNN_CHECKPOINT = "/quobyte/jbsiegelgrp/software/LigandMPNN/model_params/..."
LIGANDMPNN_CONDA_ENV = "/quobyte/jbsiegelgrp/software/envs/ligandmpnn_env"
COLABFOLD_BIN_PATH = "/quobyte/jbsiegelgrp/software/LocalColabFold/..."
BASE_CONDA_ENV = "/quobyte/jbsiegelgrp/aian/scripts/.conda/envs/ian_base"
```

### Pipeline Parameters
```python
HHBLITS_E_VALUES = ["1e-50", "1e-30", "1e-10", "1e-4"]
HHFILTER_PARAMS = {"id": 90, "cov": 50, "qid": 30}
CONSERVATION_THRESHOLD = 0.8  # 80%
LIGANDMPNN_TEMPERATURES = [0.1, 0.2, 0.3]
LIGANDMPNN_BATCH_SIZE = 16
LIGANDMPNN_NUM_BATCHES = 4
LIGANDMPNN_OMIT_AA = "C"  # Omit cysteine
```

### SLURM Settings
```python
SLURM_PARTITION_CPU = "low"
SLURM_PARTITION_GPU = "gpu-a100"
SLURM_ACCOUNT_GPU = "genome-center-grp"
```

## Job Dependencies

The pipeline uses SLURM job dependencies to chain stages:

```
HHblits (1e-50) → HHblits (1e-30) → HHblits (1e-10) → HHblits (1e-4)
                                                           ↓
                                                       HHfilter
                                                           ↓
                    Reference ColabFold ────┬───────> Conservation
                         (parallel)         │             ↓
                                            └──────> LigandMPNN (T0.1)
                                                        LigandMPNN (T0.2)
                                                        LigandMPNN (T0.3)
                                                           ↓
                                                    Post-processing
                                                           ↓
                                                  ColabFold Monomer (array)
                                                           ↓
                                                    PyMOL Comparison
```

## Monitoring Jobs

### Check Job Status
```bash
squeue -u $USER
```

### View Logs
```bash
# Real-time monitoring
tail -f jobs/JOBNAME/logs/*.out

# Check for errors
grep -i error jobs/JOBNAME/logs/*.err
```

### Cancel Jobs
```bash
# Cancel all jobs for this pipeline
scancel -u $USER -n "job_name_pattern"
```

## Resource Requirements

### CPU Jobs
- **HHblits**: 4 CPUs, 32GB RAM, 2 hours
- **HHfilter**: 2 CPUs, 8GB RAM, 30 minutes
- **Conservation**: 1 CPU, 8GB RAM, 10 minutes
- **Post-processing**: 1 CPU, 8GB RAM, 30 minutes
- **PyMOL**: 4 CPUs, 16GB RAM, 2 hours

### GPU Jobs
- **Reference ColabFold**: 1 GPU, 16 CPUs, 32GB RAM, 17 hours
- **LigandMPNN**: 1 GPU, 32GB RAM, 10 hours (per temperature)
- **ColabFold Monomer**: 1 GPU, 16 CPUs, 32GB RAM, 17 hours (per task)

## Expected Timeline

For a typical protein (~200 residues):

1. **HHblits + Conservation**: ~3-5 hours (sequential)
2. **Reference Structure**: ~2-4 hours (parallel with above)
3. **LigandMPNN**: ~10-12 hours (3 temperatures in parallel)
4. **ColabFold Monomer**: ~30-60 minutes per design (192 designs = ~6-12 days wall time if run sequentially)
5. **PyMOL Analysis**: ~1-2 hours

**Total wall time**: ~7-10 hours to design generation, then dependent on ColabFold array throughput.

## Troubleshooting

### Common Issues

**1. Reference PDB not found**
- Check ColabFold logs in `jobs/JOBNAME/logs/colabfold_reference_*.err`
- Verify ColabFold installation and GPU availability

**2. Conserved residues file missing**
- Check conservation analysis logs
- Ensure HHfilter completed successfully
- Verify MSA contains sufficient sequences

**3. ColabFold array job size mismatch**
- After post-processing completes, manually check:
  ```bash
  wc -l < jobs/JOBNAME/ligandmpnn/cf_tasks.txt
  ```
- Resubmit with correct array size if needed

**4. PyMOL comparison fails**
- Ensure PyMOL is installed in the conda environment
- Check that ColabFold predictions completed
- Verify chain specification matches design chain

### Debugging Tips

1. **Check SLURM logs**: All stdout/stderr in `jobs/JOBNAME/logs/`
2. **Validate intermediate files**:
   - MSAs should contain >50 sequences
   - Reference PDB should exist and be valid
   - LigandMPNN should produce FASTA files
3. **Test individual stages**: Run scripts manually with `sbatch` to isolate issues
4. **Dry run first**: Use `--dry-run` to validate script generation

## Advanced Usage

### Modifying Conservation Threshold

Edit `CONSERVATION_THRESHOLD` in the script:
```python
CONSERVATION_THRESHOLD = 0.9  # 90% conservation
```

### Adding More Temperatures

Edit `LIGANDMPNN_TEMPERATURES`:
```python
LIGANDMPNN_TEMPERATURES = [0.1, 0.2, 0.3, 0.4, 0.5]
```

### Changing Design Parameters

```python
LIGANDMPNN_BATCH_SIZE = 32  # More sequences per batch
LIGANDMPNN_NUM_BATCHES = 8  # More batches
LIGANDMPNN_OMIT_AA = "CM"   # Omit cysteine and methionine
```

### Using Different Chains

For multi-chain proteins:
```bash
python run_pipeline.py complex.fasta --chain D
```

## Best Practices

1. **Sequence Quality**: Ensure input sequence is correct and properly formatted
2. **Resource Planning**: Consider GPU availability for ColabFold array jobs
3. **Storage**: Each run can generate 10-50GB of data
4. **Naming**: Use descriptive, unique FASTA filenames (becomes job name)
5. **Monitoring**: Check early stages (HHblits, reference) before later stages start
6. **Validation**: Review conserved residues before designs complete

## Output Analysis

### Selecting Best Designs

1. **Sort by RMSD**: Lowest RMSD designs are most structurally similar to reference
2. **Consider temperature**: Lower temperatures (0.1) = more conservative designs
3. **Check conservation**: Verify conserved residues are maintained
4. **Review pLDDT scores**: ColabFold confidence scores in PDB files

### Example Analysis Workflow

```bash
# View top 10 designs
head -11 jobs/JOBNAME/pymol_analysis/{name}_rmsd_results.csv | column -t -s,

# Extract best design FASTA
best_id=$(awk -F, 'NR==2 {print $3}' jobs/JOBNAME/pymol_analysis/{name}_rmsd_results.csv)
grep -A1 "id_${best_id}" jobs/JOBNAME/ligandmpnn/T*/temp_fastas/*.fasta | head -2

# Load best structure in PyMOL
pymol jobs/JOBNAME/colabfold/colabfold_output/*id_${best_id}*_unrelaxed_rank_001*.pdb
```

## Related Documentation

- [ColabFold Documentation](colabfold.md)
- [LigandMPNN Documentation](ligandmpnn.md)
- [RF Diffusion Documentation](rf_diffusion_aa.md)

## Citation

If you use this pipeline, please cite:

- **This Pipeline Methodology**: King, B. R., Sumida, K. H., Caruso, J. L., Baker, D., & Zalatan, J. G. (2024). Computational Stabilization of a Non-Heme Iron Enzyme Enables Efficient Evolution of New Function. *Angewandte Chemie International Edition*. https://doi.org/10.1002/anie.202414705
- **HHsuite**: Steinegger M, et al. (2019) Nat Biotechnol
- **ColabFold**: Mirdita M, et al. (2022) Nat Methods
- **LigandMPNN**: Dauparas J, et al. (2023) bioRxiv
- **PyMOL**: Schrödinger, LLC

## Contact

For questions or issues with this pipeline, please contact the Siegel Lab.
