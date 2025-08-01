# HIVE Cluster Migration Tools

This repository contains scripts to help migrate from the old HPC cluster to the new HIVE cluster at UC Davis.

## Quick Start

**IMPORTANT**: Run these scripts from your old cluster (cacao/barbera), NOT from HIVE!

1. **Clone this repository on your old cluster:**
   ```bash
   # SSH to cacao or barbera first
   ssh username@cacao.genomecenter.ucdavis.edu
   # OR
   ssh username@barbera.genomecenter.ucdavis.edu
   
   # Then clone the repo
   git clone https://github.com/ianandersonlol/HiveTransition.git
   cd HiveTransition
   ```

2. **Migrate your shell configuration:**
   ```bash
   python bash_profile_migration.py <ssh_username> <quobyte_dir>
   ```

3. **Fix your job scripts:**
   ```bash
   python colab_fix.py my_colabfold_job.sh      # For ColabFold
   python ligandmpnn_fix.py my_ligandmpnn_job.sh # For LigandMPNN
   python rfdiffusion_fix.py my_rfdiff_job.sh    # For RFdiffusion
   python rosetta_fix.py my_rosetta_job.sh       # For Rosetta
   ```

   **Or update all paths at once (no SLURM changes):**
   ```bash
   python pathMigrator.py /path/to/scripts        # Update all software paths
   ```

## Overview

The migration to HIVE involves several key changes:

### Storage Changes
- **Old**: `/share/siegellab/`
- **New**: `/quobyte/jbsiegelgrp/`
- **Home Directory**: Limited to 1GB (use quobyte for everything!)

### Module System
- **Old**: Local conda installations
- **New**: `module load conda/latest` and `module load cuda/12.6.2`

### SLURM Partitions
- **GPU Jobs**: `jbsiegel-gpu` → `gpu-a100` (requires `--account=genome-center-grp`)
- **CPU Jobs**: `production` → `low` or `high`
  - `low`: Max 3 days, auto-requeue, more available
  - `high`: Max 30 days, no requeue, less available

### Software Locations
- **ColabFold**: `/quobyte/jbsiegelgrp/software/LocalColabFold/`
- **LigandMPNN**: `/quobyte/jbsiegelgrp/ligandMPNN/`
- **RFdiffusion**: `/quobyte/jbsiegelgrp/software/RFdiffusion/`
- **Rosetta 3.14**: `/quobyte/jbsiegelgrp/software/Rosetta_314/rosetta/main/`

## Available Scripts

### 1. pathMigrator.py (Comprehensive Path Migration)
Updates ALL software paths in a directory:
- Combines path fixes from all other scripts
- Does NOT modify SLURM settings
- Can process entire directories at once
- Includes all software: ColabFold, LigandMPNN, RFdiffusion, Rosetta

**[Full Documentation](docs/pathMigrator.md)**

### 2. bash_profile_migration.py
Migrates your shell configuration to HIVE:
- Converts `.bash_profile` to `.bashrc`
- Sets up conda in quobyte directory
- Adds interactive session aliases
- Updates paths and modules

**[Full Documentation](docs/bash_profile_migration.md)**

### 3. colab_fix.py
Updates ColabFold scripts:
- Fixes ColabFold installation path
- Updates GPU partition settings
- Migrates storage paths

**[Full Documentation](docs/colab_fix.md)**

### 4. ligandmpnn_fix.py
Updates LigandMPNN scripts:
- Fixes LigandMPNN installation path
- Updates GPU partition settings
- Migrates storage paths

**[Full Documentation](docs/ligandmpnn_fix.md)**

### 5. rfdiffusion_fix.py
Updates RFdiffusion scripts:
- Standardizes RFdiffusion installation path
- Updates conda environment to shared SE3nv
- Updates GPU partition settings

**[Full Documentation](docs/rfdiffusion_fix.md)**

### 6. rosetta_fix.py
Updates Rosetta scripts:
- Migrates to Rosetta 3.14
- Changes binary names (`.default.` → `.static.`)
- Handles CPU partition selection
- Enforces time limits

**[Full Documentation](docs/rosetta_fix.md)**

### 7. broken.py
Reports issues with scripts:
- Generates GitHub issue URL
- Pre-fills script content
- Auto-assigns to maintainer

**[Full Documentation](docs/broken.md)**

## Common Migration Tasks

### Setting Up Your Environment

1. **Run the migration script from old cluster (cacao/barbera):**
   ```bash
   python bash_profile_migration.py myusername mydirectory
   ```

2. **Log into HIVE:**
   ```bash
   ssh myusername@hive.hpc.ucdavis.edu
   ```

3. **Source your configuration:**
   ```bash
   source ~/.bashrc
   ```

### Migrating Job Scripts

1. **Identify script type** (ColabFold, Rosetta, etc.)

2. **Run appropriate fix script:**
   ```bash
   python <tool>_fix.py myscript.sh
   ```

3. **Review changes:**
   ```bash
   diff myscript.sh myscript_fixed.sh
   ```

4. **Test on HIVE:**
   ```bash
   sbatch myscript_fixed.sh
   ```

### Interactive Sessions

Use the aliases added by bash_profile_migration.py:

```bash
sandbox      # 8 CPU, 16GB RAM, high priority
sandboxlow   # 16 CPU, 32GB RAM, low priority
sandboxgpu   # 8 CPU, 16GB RAM, 1 GPU, high priority
sandboxlowgpu # 8 CPU, 16GB RAM, 1 GPU, low priority
```

## Important Notes

### Storage Management
- Home directory: 20GB limit
- Store everything in `/quobyte/jbsiegelgrp/{your_directory}/`
- Conda environments go in `.conda/envs/`
- Package caches go in `.cache/`

### Module Loading
Instead of local conda:
```bash
module load conda/latest
module load cuda/12.6.2  # For GPU jobs Good to have even when you're not using a GPU so you have the drivers up!
```
**IF YOU USED MY BASH MIGRATION TOOL IT WILL PUT IT IN YOUR BASHRC**
### Partition Selection
- Use `low` for most jobs (< 3 days)
- Use `high` for long jobs (> 3 days)
- GPU jobs need `--account=genome-center-grp`

## Troubleshooting

### Common Issues

1. **"Module not found"**
   - Use `module avail <name>` to find the new module name
   - Some modules have different names on HIVE

2. **"Permission denied"**
   - Check you're writing to your quobyte directory
   - Create directories if they don't exist

3. **"Command not found"**
   - Ensure you've sourced `~/.bashrc`
   - Check if software is in a different location

4. **Time limit errors**
   - Use `--high` flag for Rosetta jobs > 3 days
   - Break large jobs into smaller chunks

### Getting Help

1. **Check documentation:**
   - See `docs/` folder for detailed guides
   - Each script has `--help` option

2. **Report issues:**
   ```bash
   python broken.py problematic_script.sh
   ```

3. **GitHub Issues:**
   - https://github.com/ianandersonlol/HiveTransition/issues

## Contributing

If you find issues or have improvements:

1. Use `broken.py` to report script issues
2. Submit pull requests for fixes
3. Share working examples with the community

## File Structure

```
HiveTransition/
├── README.md                    # This file
├── pathMigrator.py             # Comprehensive path migration (all software)
├── bash_profile_migration.py    # Shell config migration
├── colab_fix.py                # ColabFold script fixer (with SLURM)
├── ligandmpnn_fix.py           # LigandMPNN script fixer (with SLURM)
├── rfdiffusion_fix.py          # RFdiffusion script fixer (with SLURM)
├── rosetta_fix.py              # Rosetta script fixer (with SLURM)
├── broken.py                   # Issue reporter
├── docs/                       # Detailed documentation
│   ├── pathMigrator.md
│   ├── bash_profile_migration.md
│   ├── colab_fix.md
│   ├── ligandmpnn_fix.md
│   ├── rfdiffusion_fix.md
│   ├── rosetta_fix.md
│   └── broken.md
└── .github/
    └── ISSUE_TEMPLATE/
        └── script_not_working.md
```

## License

This project is provided as-is 

## Acknowledgments

Created to facilitate the transition to the HIVE cluster for the Siegel Lab and affiliated researchers.
