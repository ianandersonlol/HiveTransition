# Changelog

All notable changes to this project will be documented in this file.

## [2025-11-05] - Resource Standardization & Naming Improvements

### Resource Standardization
All structure prediction scripts have been standardized for consistency and reliability:

**GPU Structure Prediction Standard: 16 CPU, 64G**
- ✅ ColabFold: 16 CPU, 64G (baseline)
- ✅ Boltz2: 16 CPU, 64G (increased from 32G)
- ✅ AlphaFold3: 16 CPU, 64G, **gpu-a100 partition** (fixed from low partition)
- ✅ AF2 Initial Guess: 16 CPU, 64G (increased from 4 CPU, 16G)
- ℹ️ Chai: 16 CPU, 128G (appropriate for large complexes)

**CPU Jobs Standard:**
- ✅ Rosetta Relax: 4 CPU, 8G, low partition with --requeue

**Benefits:**
- Prevents resource-related failures (OOM errors, timeout)
- Consistent baseline for all GPU workloads
- Improved cluster utilization
- Clear standards for users

### Naming Standardization
All files and directories now use consistent `snake_case` naming:
- Directories: `alphafold2/`, `boltz2/`, `chai/`, `diffusion/`, `ligandmpnn/`, `mpnnp_pipeline/`
- Scripts: `submit_ligandmpnn.sh`, `run_af2_initial_guess.py`, `path_migrator.py`

### New Unified Migration Tool
The new `migrate.py` script consolidates all migration functionality:
- Replaces 4 separate fix scripts (colab, ligandmpnn, rfdiffusion, rosetta)
- Eliminates ~70% code duplication
- Adds --dry-run, --in-place, and --verbose modes
- See [migrate.md](docs/migrate.md) for details
