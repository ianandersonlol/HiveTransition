# Changelog

All notable changes to this project will be documented in this file.

## [2026-04-08] - Major Example Script Expansion & Documentation Overhaul

### New Example Scripts

**Structure Prediction:**
- AlphaFast (`folding/alphafast/`) — GPU-accelerated prediction with Apptainer container, 4-GPU multi-node support
- ESMFold (`folding/esmfold/`) — Single-sequence prediction with CUDA attention patching
- OpenFold 3 (`folding/openfold3/`) — Diffusion-based prediction with MSA server and template support
- RoseTTAFold 3 (`folding/rosettafold3/`) — Foundry-based prediction with multi-seed ranking
- Chai-to-AF3 converter (`folding/alphafold3/chai_to_af3_converter.py`) — FASTA to AF3 JSON format conversion

**Protein Design:**
- RFdiffusion3 (`design/rfdiffusion3/`) — Next-gen design via Foundry framework
- BindCraft (`design/bindcraft/`) — Binder protein design with multi-stage pipeline
- ESM-IF1 (`design/esm_if1/`) — Inverse folding sequence design
- DISCO (`design/disco/`) — Discrete diffusion design with ligand/DNA/RNA conditioning

**Docking:**
- HADDOCK3 (`docking/haddock3/`) — CPU-based protein-protein docking
- PLACER (`docking/placer/`) — GPU-accelerated ligand placement and docking

**Analysis:**
- ESM-2 Embeddings (`analysis/esm2_embeddings/`) — Protein embedding extraction for downstream ML

### Documentation Improvements
- Expanded README with comprehensive software location tables (structure prediction, design, docking/analysis)
- Added shared databases reference table (AF3, AlphaFast, BLAST, Boltz, Foundry, HHsuite, RFD3)
- Updated file structure tree to reflect all new directories and scripts
- Reorganized example scripts section with category headers (Folding, Design, Docking, Analysis)
- Added resource allocation details (partition, CPU, memory, time, GPU) to every script entry
- Added conda environment paths to all script entries

### AI Assistant Integration
- Added AGENTS.md at repository root for Codex CLI compatibility
- Updated HIVE cluster skill (SKILL.md) with GPU efficiency best practices and constraint patterns

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

### Shell Configuration Standardization
All SLURM submission scripts now use `#!/bin/bash --norc` shebang:
- Ensures clean shell environment without ~/.bashrc interference
- Prevents unexpected behavior from user-specific bash configurations
- Improves reproducibility and reliability of jobs
- Updated 11 scripts across all example_scripts subdirectories
