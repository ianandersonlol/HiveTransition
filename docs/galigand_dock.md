[View docking.xml](../example_scripts/docking/galigand_dock/docking.xml)
[View flags](../example_scripts/docking/galigand_dock/flags)
[View submit.sh](../example_scripts/docking/galigand_dock/submit.sh)

# GALigand Docking

This document provides a detailed explanation of the GALigand docking protocol located in the `example_scripts/docking/galigand_dock` directory.

## Overview

The GALigand docking protocol is a Rosetta-based workflow for docking a small molecule ligand into a protein. It uses a combination of RosettaScripts, command-line flags, and a submission script to run the docking simulation.

## Files

### 1. `docking.xml`
This is a RosettaScripts XML file that defines the docking protocol. It specifies the movers and filters to be used in the simulation, such as `LigandArea`, `DockingGrid`, `DockMCM`, and `InterfaceScore`.

### 2. `flags`
This file contains the command-line flags for the Rosetta executable. It specifies the input PDB file, the params file for the ligand, the constraint file, and other settings for the docking run.

### 3. `submit.sh`
This is a SLURM submission script that runs the GALigand docking protocol. It sets up the environment, and then executes the Rosetta executable with the specified flags and XML script.

### 4. `4Epimv7.cst`
This is a constraint file for Rosetta. It defines constraints that are used to guide the docking simulation.

### 5. `DF6.params`
This is a params file for the ligand. It contains the parameters for the small molecule that is being docked.

### 6. `GatZ_F6P.pdb`
This is the PDB file for the protein that the ligand is being docked into.

## Usage

To run the GALigand docking protocol, you need to submit the `submit.sh` script to a SLURM cluster.

```bash
sbatch example_scripts/docking/galigand_dock/submit.sh
```

The `submit.sh` script will then execute the Rosetta executable with the specified flags and XML script, and the results will be saved in the `output` directory.