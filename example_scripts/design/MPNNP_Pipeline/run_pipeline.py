#!/usr/bin/env python3
"""
Unified Protein Design Pipeline
================================

Complete automated pipeline from sequence to structure:
1. HHblits MSA generation and conservation analysis
2. Reference structure prediction (ColabFold)
3. LigandMPNN design with conserved residues
4. ColabFold structure prediction of designs (monomer)

Usage:
    python run_pipeline.py input.fasta
    python run_pipeline.py input.fasta --chain A
    python run_pipeline.py input.fasta --dry-run

Output Structure:
    jobs/JOBNAME/
    ├── logs/              # All SLURM logs
    ├── input.fa           # Input FASTA
    ├── hhblits/           # HHblits MSAs and conservation
    ├── reference/         # Reference structure (ColabFold)
    ├── ligandmpnn/        # LigandMPNN designs
    ├── colabfold/         # Structure predictions
    ├── pymol_analysis/    # RMSD comparison results
    └── cache/             # Temporary cache files

The pipeline automatically chains all jobs with SLURM dependencies.
"""

import os
import sys
import subprocess
import argparse
import shutil
import string
import re
import json
from pathlib import Path
import numpy as np
import pandas as pd

# ================================
# HARDCODED CONFIGURATION
# ================================

# System paths
HHBLITS_DATABASE = "/quobyte/jbsiegelgrp/databases/hhsuite_databases/uniclust30_2023_02/UniRef30_2023_02"
LIGANDMPNN_ROOT = "/quobyte/jbsiegelgrp/software/LigandMPNN"
LIGANDMPNN_CHECKPOINT = "/quobyte/jbsiegelgrp/software/LigandMPNN/model_params/ligandmpnn_v_32_020_25.pt"
LIGANDMPNN_CONDA_ENV = "/quobyte/jbsiegelgrp/software/envs/ligandmpnn_env"
COLABFOLD_BIN_PATH = "/quobyte/jbsiegelgrp/software/LocalColabFold/localcolabfold/colabfold-conda/bin"
BASE_CONDA_ENV = "/quobyte/jbsiegelgrp/aian/scripts/.conda/envs/ian_base"

# Pipeline parameters
HHBLITS_E_VALUES = ["1e-50", "1e-30", "1e-10", "1e-4"]
HHFILTER_PARAMS = {"id": 90, "cov": 50, "qid": 30}
CONSERVATION_THRESHOLD = 0.8  # Use 80% conservation
LIGANDMPNN_TEMPERATURES = [0.1, 0.2, 0.3]
LIGANDMPNN_BATCH_SIZE = 16
LIGANDMPNN_NUM_BATCHES = 4
LIGANDMPNN_OMIT_AA = "C"

# ColabFold parameters
COLABFOLD_MODEL_ORDER = 3
COLABFOLD_NUM_MODELS = 1
COLABFOLD_NUM_RECYCLE = 6

# SLURM settings
SLURM_PARTITION_CPU = "low"
SLURM_PARTITION_GPU = "gpu-a100"
SLURM_ACCOUNT_GPU = "genome-center-grp"

# ================================
# UTILITY FUNCTIONS
# ================================

def validate_fasta(fasta_path):
    """Validate that the input FASTA file exists and is valid."""
    if not os.path.isfile(fasta_path):
        print(f"❌ ERROR: FASTA file not found: {fasta_path}")
        return False

    # Basic FASTA validation
    with open(fasta_path, 'r') as f:
        content = f.read()
        if not content.startswith('>'):
            print(f"❌ ERROR: Invalid FASTA format (missing header)")
            return False

    return True

def get_job_name(fasta_path):
    """Extract job name from FASTA filename."""
    basename = os.path.basename(fasta_path)
    # Remove extension (.fa, .fasta, .faa)
    job_name = re.sub(r'\.(fa|fasta|faa)$', '', basename, flags=re.IGNORECASE)
    return job_name

def setup_job_directory(base_dir, job_name):
    """Create the job directory structure."""
    job_dir = os.path.join(base_dir, "jobs", job_name)

    subdirs = [
        "logs",
        "hhblits",
        "reference",
        "ligandmpnn",
        "colabfold",
        "cache"
    ]

    for subdir in subdirs:
        os.makedirs(os.path.join(job_dir, subdir), exist_ok=True)

    print(f"✅ Created job directory: {job_dir}")
    return job_dir

def copy_input_fasta(source_fasta, job_dir, job_name):
    """Copy input FASTA to job directory."""
    dest_fasta = os.path.join(job_dir, "input.fa")

    # Read source and write with proper header
    with open(source_fasta, 'r') as infile:
        lines = infile.readlines()

    with open(dest_fasta, 'w') as outfile:
        # Ensure header is properly formatted
        if lines[0].startswith('>'):
            outfile.write(f">{job_name}\n")
        else:
            outfile.write(f">{job_name}\n")

        # Write sequence lines
        for line in lines[1:] if lines[0].startswith('>') else lines:
            outfile.write(line)

    print(f"✅ Copied input FASTA to: {dest_fasta}")
    return dest_fasta

# ================================
# HHBLITS MSA GENERATION
# ================================

def create_hhblits_scripts(job_dir, job_name, input_fasta):
    """Generate HHblits search scripts with chained E-values."""
    hhblits_dir = os.path.join(job_dir, "hhblits")
    logs_dir = os.path.join(job_dir, "logs")

    scripts = []
    current_input = input_fasta

    for e_value in HHBLITS_E_VALUES:
        # Clean e-value label
        if e_value.startswith("1e-"):
            e_label = e_value.split("-")[1]
        else:
            e_label = e_value.replace(".", "p")

        # Output files
        a3m_file = os.path.join(hhblits_dir, f"{job_name}_{e_label}.a3m")
        script_file = os.path.join(hhblits_dir, f"hhblits_{e_label}.sh")

        script_content = f"""#!/bin/bash
#SBATCH --job-name=hhb_{job_name}_{e_label}
#SBATCH --output={logs_dir}/hhblits_{e_label}_%j.out
#SBATCH --error={logs_dir}/hhblits_{e_label}_%j.err
#SBATCH --partition={SLURM_PARTITION_CPU}
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=2:00:00
#SBATCH --requeue

module load conda/latest
module load hhsuite/3.3.0

eval "$(conda shell.bash hook)"
conda activate {BASE_CONDA_ENV}

hhblits -cpu 4 -i {current_input} \\
    -d {HHBLITS_DATABASE} \\
    -oa3m {a3m_file} \\
    -n 1 \\
    -e {e_value} \\
    -maxseqs 60000 \\
    -mact 0.35 \\
    -maxfilt 20000 \\
    -neffmax 20 \\
    -all \\
    -realign_max 20000
"""

        with open(script_file, 'w') as f:
            f.write(script_content)

        scripts.append(script_file)
        current_input = a3m_file  # Chain outputs

    print(f"✅ Generated {len(scripts)} HHblits scripts")
    return scripts

def create_hhfilter_script(job_dir, job_name):
    """Generate HHfilter script for MSA filtering."""
    hhblits_dir = os.path.join(job_dir, "hhblits")
    logs_dir = os.path.join(job_dir, "logs")

    final_e_label = HHBLITS_E_VALUES[-1].split("-")[1]
    input_a3m = os.path.join(hhblits_dir, f"{job_name}_{final_e_label}.a3m")
    output_a3m = os.path.join(
        hhblits_dir,
        f"{job_name}_id{HHFILTER_PARAMS['id']}cov{HHFILTER_PARAMS['cov']}qid{HHFILTER_PARAMS['qid']}.a3m"
    )
    script_file = os.path.join(hhblits_dir, "hhfilter.sh")

    script_content = f"""#!/bin/bash
#SBATCH --job-name=hhf_{job_name}
#SBATCH --output={logs_dir}/hhfilter_%j.out
#SBATCH --error={logs_dir}/hhfilter_%j.err
#SBATCH --partition={SLURM_PARTITION_CPU}
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=0:30:00
#SBATCH --requeue

module load conda/latest
module load hhsuite/3.3.0

eval "$(conda shell.bash hook)"
conda activate {BASE_CONDA_ENV}

hhfilter \\
    -id {HHFILTER_PARAMS['id']} \\
    -cov {HHFILTER_PARAMS['cov']} \\
    -qid {HHFILTER_PARAMS['qid']} \\
    -i {input_a3m} \\
    -o {output_a3m}
"""

    with open(script_file, 'w') as f:
        f.write(script_content)

    print(f"✅ Generated HHfilter script")
    return script_file

def create_conservation_script(job_dir, job_name):
    """Generate conservation analysis script."""
    hhblits_dir = os.path.join(job_dir, "hhblits")
    logs_dir = os.path.join(job_dir, "logs")
    script_file = os.path.join(hhblits_dir, "conservation.sh")

    script_content = f"""#!/bin/bash
#SBATCH --job-name=cons_{job_name}
#SBATCH --output={logs_dir}/conservation_%j.out
#SBATCH --error={logs_dir}/conservation_%j.err
#SBATCH --partition={SLURM_PARTITION_CPU}
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=0:10:00
#SBATCH --requeue

module load conda/latest
eval "$(conda shell.bash hook)"
conda activate {BASE_CONDA_ENV}

cd {job_dir}

python3 <<'PYTHON_SCRIPT'
import os
import sys
import numpy as np
import pandas as pd
import string

def parse_a3m(filename):
    \"\"\"Parse A3M file and convert to numeric format.\"\"\"
    lab, seq = [], []

    with open(filename, "r") as f:
        for line in f:
            if line[0] == '>':
                lab.append(line.split()[0][1:])
                seq.append("")
            else:
                seq[-1] += line.rstrip()

    msa, ins = [], []
    table = str.maketrans(dict.fromkeys(string.ascii_lowercase))
    nrow, ncol = len(seq), len(seq[0])

    for seqi in seq:
        msa.append(seqi.translate(table))
        a = np.array([0 if c.isupper() or c == '-' else 1 for c in seqi])
        i = np.zeros((ncol))

        if np.sum(a) > 0:
            pos = np.where(a == 1)[0]
            a = pos - np.arange(pos.shape[0])
            pos, num = np.unique(a, return_counts=True)
            i[pos[pos < ncol]] = num[pos < ncol]

        ins.append(i)

    alphabet = np.array(list("ARNDCQEGHILKMFPSTWYV-"), dtype='|S1').view(np.uint8)
    msa_arr = np.array([list(s) for s in msa], dtype='|U1')
    msa_num = msa_arr.copy().astype('|S1').view(np.uint8)

    for idx in range(alphabet.shape[0]):
        msa_num[msa_num == alphabet[idx]] = idx

    msa_arr[msa_num > 20] = '-'
    msa_num[msa_num > 20] = 20
    ins = np.array(ins, dtype=np.uint8)

    return {{"msa": msa_arr, "msa_num": msa_num, "labels": lab, "insertions": ins}}

# Find filtered MSA
msa_file = "{hhblits_dir}/{job_name}_id{HHFILTER_PARAMS['id']}cov{HHFILTER_PARAMS['cov']}qid{HHFILTER_PARAMS['qid']}.a3m"

if not os.path.isfile(msa_file):
    print(f"❌ ERROR: Filtered MSA not found: {{msa_file}}")
    sys.exit(1)

print(f"🔍 Analyzing conserved residues from: {{msa_file}}")

aln = parse_a3m(msa_file)
msa_num = aln["msa_num"]
L = msa_num.shape[1]

counts = np.stack([np.bincount(col, minlength=21) for col in msa_num.T]).T
max_count = np.max(counts, axis=0)

# Calculate conservation at 80% threshold
frac = {CONSERVATION_THRESHOLD}
freq = counts / msa_num.shape[0]
freq_norm = freq[:20] / freq[:20].sum(axis=0)
max_freq_norm = np.max(freq_norm, axis=0)
max_freq_norm[max_count < 10] = 0

n_keep = int(L * frac)
conserved = np.argsort(max_freq_norm)[::-1][:n_keep] + 1  # 1-based indexing

results = {{
    "fraction_conserved": [f"{{int(frac*100)}}%"],
    "residue_list": [",".join(map(str, np.sort(conserved).tolist()))]
}}

df = pd.DataFrame(results)
output_path = "{hhblits_dir}/{job_name}_conserved_residues.xlsx"
df.to_excel(output_path, index=False)

print(f"✅ Conserved residues saved to: {{output_path}}")
print(f"📊 Found {{len(conserved)}} conserved residues at {{int(frac*100)}}% threshold")
PYTHON_SCRIPT
"""

    with open(script_file, 'w') as f:
        f.write(script_content)

    print(f"✅ Generated conservation analysis script")
    return script_file

# ================================
# REFERENCE STRUCTURE GENERATION
# ================================

def create_reference_colabfold_script(job_dir, job_name, input_fasta):
    """Generate reference structure ColabFold script."""
    ref_dir = os.path.join(job_dir, "reference")
    ref_output = os.path.join(ref_dir, "colabfold_output")
    logs_dir = os.path.join(job_dir, "logs")

    os.makedirs(ref_output, exist_ok=True)

    script_file = os.path.join(ref_dir, "colabfold_reference.sh")

    script_content = f"""#!/bin/bash
#SBATCH --job-name=cfref_{job_name}
#SBATCH --output={logs_dir}/colabfold_reference_%j.out
#SBATCH --error={logs_dir}/colabfold_reference_%j.err
#SBATCH --partition={SLURM_PARTITION_GPU}
#SBATCH --account={SLURM_ACCOUNT_GPU}
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=17:00:00

module unload cuda 2>/dev/null || true

export MPLBACKEND=Agg
unset DISPLAY
export QT_QPA_PLATFORM=offscreen
export PATH="{COLABFOLD_BIN_PATH}:$PATH"

colabfold_batch --model-order {COLABFOLD_MODEL_ORDER} --num-models {COLABFOLD_NUM_MODELS} --num-recycle {COLABFOLD_NUM_RECYCLE} {input_fasta} {ref_output}
"""

    with open(script_file, 'w') as f:
        f.write(script_content)

    print(f"✅ Generated reference ColabFold script")
    return script_file

# ================================
# LIGANDMPNN DESIGN
# ================================

def create_ligandmpnn_scripts(job_dir, job_name, design_chain):
    """Generate LigandMPNN design scripts for all temperatures."""
    ligandmpnn_dir = os.path.join(job_dir, "ligandmpnn")
    logs_dir = os.path.join(job_dir, "logs")
    cache_dir = os.path.join(job_dir, "cache")
    ref_dir = os.path.join(job_dir, "reference")

    # Reference PDB will be from ColabFold output
    # We'll use a glob pattern since the exact name depends on ColabFold
    ref_pdb_pattern = f"{ref_dir}/colabfold_output/*_unrelaxed_rank_001*.pdb"

    scripts = []

    for temp in LIGANDMPNN_TEMPERATURES:
        temp_dir = os.path.join(ligandmpnn_dir, f"T{temp}")
        os.makedirs(temp_dir, exist_ok=True)

        script_file = os.path.join(ligandmpnn_dir, f"ligandmpnn_T{temp}.sh")

        script_content = f"""#!/bin/bash
#SBATCH --job-name=lmpnn_{job_name}_T{temp}
#SBATCH --output={logs_dir}/ligandmpnn_T{temp}_%j.out
#SBATCH --error={logs_dir}/ligandmpnn_T{temp}_%j.err
#SBATCH --partition={SLURM_PARTITION_GPU}
#SBATCH --account={SLURM_ACCOUNT_GPU}
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --mem=32G
#SBATCH --time=10:00:00

export TORCH_HOME={cache_dir}

module load conda/latest
eval "$(conda shell.bash hook)"
conda activate {LIGANDMPNN_CONDA_ENV}

cd {LIGANDMPNN_ROOT}

# Find reference PDB
REF_PDB=$(ls {ref_pdb_pattern} 2>/dev/null | head -1)

if [ -z "$REF_PDB" ]; then
    echo "❌ ERROR: Reference PDB not found"
    exit 1
fi

# Load conserved residues
CONSERVED_FILE="{job_dir}/hhblits/{job_name}_conserved_residues.xlsx"

if [ ! -f "$CONSERVED_FILE" ]; then
    echo "❌ ERROR: Conserved residues file not found"
    exit 1
fi

# Extract conserved residues and format for LigandMPNN
FIXED_RESIDUES=$(python3 <<PYTHON_EOF
import pandas as pd
df = pd.read_excel("$CONSERVED_FILE")
row = df[df['fraction_conserved'] == '{int(CONSERVATION_THRESHOLD*100)}%']
if row.empty:
    print("")
else:
    residues = row['residue_list'].iloc[0]
    formatted = " ".join([f"{design_chain}{{r}}" for r in residues.split(',')])
    print(formatted)
PYTHON_EOF
)

if [ -z "$FIXED_RESIDUES" ]; then
    echo "⚠️ WARNING: No conserved residues found, proceeding without fixed residues"
    FIXED_ARG=""
else
    echo "✅ Using fixed residues: $FIXED_RESIDUES"
    FIXED_ARG="--fixed_residues \\"$FIXED_RESIDUES\\""
fi

# Run LigandMPNN
eval python run.py \\
    --model_type ligand_mpnn \\
    --checkpoint_ligand_mpnn {LIGANDMPNN_CHECKPOINT} \\
    --pdb_path "$REF_PDB" \\
    --out_folder {temp_dir} \\
    --chains_to_design {design_chain} \\
    $FIXED_ARG \\
    --temperature {temp} \\
    --batch_size {LIGANDMPNN_BATCH_SIZE} \\
    --omit_AA "{LIGANDMPNN_OMIT_AA}" \\
    --number_of_batches {LIGANDMPNN_NUM_BATCHES}
"""

        with open(script_file, 'w') as f:
            f.write(script_content)

        scripts.append(script_file)

    print(f"✅ Generated {len(scripts)} LigandMPNN scripts")
    return scripts

def create_ligandmpnn_postprocess_script(job_dir, job_name, design_chain):
    """Generate post-processing script to split LigandMPNN outputs."""
    ligandmpnn_dir = os.path.join(job_dir, "ligandmpnn")
    logs_dir = os.path.join(job_dir, "logs")

    script_file = os.path.join(ligandmpnn_dir, "postprocess.sh")

    script_content = f"""#!/bin/bash
#SBATCH --job-name=pp_{job_name}
#SBATCH --output={logs_dir}/postprocess_%j.out
#SBATCH --error={logs_dir}/postprocess_%j.err
#SBATCH --partition={SLURM_PARTITION_CPU}
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=0:30:00

module load conda/latest
eval "$(conda shell.bash hook)"
conda activate {BASE_CONDA_ENV}

cd {job_dir}

python3 <<'PYTHON_SCRIPT'
import os
import re
from pathlib import Path

ligandmpnn_dir = "{ligandmpnn_dir}"
job_name = "{job_name}"
design_chain = "{design_chain}"
temperatures = {LIGANDMPNN_TEMPERATURES}

# Determine chain index for extraction
chain_idx = 0 if design_chain == "A" else 3 if design_chain == "D" else 0

# Create cf_tasks.txt
cf_tasks_path = os.path.join(ligandmpnn_dir, "cf_tasks.txt")
total_written = 0

with open(cf_tasks_path, "w") as cf_tasks_file:
    for temp in temperatures:
        temp_dir = os.path.join(ligandmpnn_dir, f"T{{temp}}")
        seqs_dir = os.path.join(temp_dir, "seqs")

        # Find the multi-FASTA file (name depends on reference PDB)
        if not os.path.isdir(seqs_dir):
            print(f"⚠️ Skipping T{{temp}}: seqs directory not found")
            continue

        # Find .fa file
        fa_files = list(Path(seqs_dir).glob("*.fa"))
        if not fa_files:
            print(f"⚠️ Skipping T{{temp}}: no .fa files found")
            continue

        multi_fasta_path = fa_files[0]

        # Create temp_fastas directory
        temp_fastas_dir = os.path.join(temp_dir, "temp_fastas")
        os.makedirs(temp_fastas_dir, exist_ok=True)

        with open(multi_fasta_path, "r") as infile:
            sequence_index = 0
            while True:
                header = infile.readline()
                sequence = infile.readline()
                if not header or not sequence:
                    break

                sequence_index += 1
                if sequence_index == 1:
                    continue  # Skip first (unmodified) sequence

                # Extract chain sequence
                parts = sequence.strip().split(":")
                if chain_idx >= len(parts):
                    continue
                chain_seq = parts[chain_idx]

                # Extract sequence ID
                match = re.search(r'id=(\\d+)', header)
                if not match:
                    continue
                seq_id = match.group(1)

                # Create individual FASTA
                new_header = f">{{job_name}}_T{{temp}}_id_{{seq_id}}"
                fasta_filename = f"{{job_name}}_T{{temp}}_id_{{seq_id}}.fasta"
                fasta_path = os.path.join(temp_fastas_dir, fasta_filename)

                with open(fasta_path, "w") as fasta_file:
                    fasta_file.write(new_header + "\\n")
                    fasta_file.write(chain_seq + "\\n")

                cf_tasks_file.write(str(fasta_path) + "\\n")
                total_written += 1

print(f"✅ Created {{total_written}} FASTA files for ColabFold")
print(f"✅ cf_tasks.txt written to: {{cf_tasks_path}}")
PYTHON_SCRIPT
"""

    with open(script_file, 'w') as f:
        f.write(script_content)

    print(f"✅ Generated post-processing script")
    return script_file

# ================================
# COLABFOLD MONOMER PREDICTION
# ================================

def create_colabfold_monomer_script(job_dir, job_name):
    """Generate ColabFold monomer prediction script."""
    colabfold_dir = os.path.join(job_dir, "colabfold")
    colabfold_output = os.path.join(colabfold_dir, "colabfold_output")
    ligandmpnn_dir = os.path.join(job_dir, "ligandmpnn")
    logs_dir = os.path.join(job_dir, "logs")

    os.makedirs(colabfold_output, exist_ok=True)

    cf_tasks_path = os.path.join(ligandmpnn_dir, "cf_tasks.txt")
    script_file = os.path.join(colabfold_dir, "colabfold_monomer.sh")

    script_content = f"""#!/bin/bash
#SBATCH --job-name=cfmono_{job_name}
#SBATCH --output={logs_dir}/colabfold_monomer_%A_%a.out
#SBATCH --error={logs_dir}/colabfold_monomer_%A_%a.err
#SBATCH --partition={SLURM_PARTITION_GPU}
#SBATCH --account={SLURM_ACCOUNT_GPU}
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=17:00:00

module unload cuda 2>/dev/null || true

export MPLBACKEND=Agg
unset DISPLAY
export QT_QPA_PLATFORM=offscreen
export PATH="{COLABFOLD_BIN_PATH}:$PATH"

CF_PATHS=$(sed -n ${{SLURM_ARRAY_TASK_ID}}p {cf_tasks_path})

colabfold_batch --model-order {COLABFOLD_MODEL_ORDER} --num-models {COLABFOLD_NUM_MODELS} --num-recycle {COLABFOLD_NUM_RECYCLE} "$CF_PATHS" {colabfold_output}
"""

    with open(script_file, 'w') as f:
        f.write(script_content)

    print(f"✅ Generated ColabFold monomer script")
    return script_file

# ================================
# PYMOL COMPARISON
# ================================

def create_pymol_comparison_script(job_dir, job_name, design_chain):
    """Generate PyMOL RMSD comparison script."""
    pymol_dir = os.path.join(job_dir, "pymol_analysis")
    colabfold_dir = os.path.join(job_dir, "colabfold", "colabfold_output")
    ref_dir = os.path.join(job_dir, "reference", "colabfold_output")
    logs_dir = os.path.join(job_dir, "logs")

    os.makedirs(pymol_dir, exist_ok=True)

    # Output CSV path
    output_csv = os.path.join(pymol_dir, f"{job_name}_rmsd_results.csv")

    script_file = os.path.join(pymol_dir, "pymol_comparison.sh")

    script_content = f"""#!/bin/bash
#SBATCH --job-name=pymol_{job_name}
#SBATCH --output={logs_dir}/pymol_comparison_%j.out
#SBATCH --error={logs_dir}/pymol_comparison_%j.err
#SBATCH --partition={SLURM_PARTITION_CPU}
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=2:00:00

module load conda/latest
eval "$(conda shell.bash hook)"
conda activate /quobyte/jbsiegelgrp/aian/scripts/.conda/envs/ai_docking

cd {job_dir}

python3 <<'PYTHON_SCRIPT'
import os
import sys
import csv
from pathlib import Path

# PyMOL import
try:
    from pymol import cmd
except ImportError:
    print("❌ ERROR: PyMOL not available!")
    print("Please ensure PyMOL is installed: conda install -c conda-forge pymol-open-source")
    sys.exit(1)

def initialize_pymol():
    \"\"\"Initialize PyMOL for scripting.\"\"\"
    cmd.reinitialize()
    print("✅ PyMOL initialized")

def calculate_ca_rmsd(ref_pdb, pred_pdb, chain="{design_chain}"):
    \"\"\"Calculate untrimmed CA RMSD between structures.\"\"\"

    # Clear and load structures
    cmd.delete("all")
    cmd.load(ref_pdb, "reference")
    cmd.load(pred_pdb, "predicted")

    # Align on CA atoms only (cycles=0 for no trimming)
    ref_sel = f"reference and name CA and chain {{chain}}"
    pred_sel = f"predicted and name CA and chain {{chain}}"

    alignment_result = cmd.align(pred_sel, ref_sel, cycles=0)
    rmsd = alignment_result[0]

    return rmsd

# Find reference PDB
ref_dir = "{ref_dir}"
ref_pdbs = list(Path(ref_dir).glob("*_unrelaxed_rank_001*.pdb"))

if not ref_pdbs:
    print(f"❌ ERROR: No reference PDB found in {{ref_dir}}")
    sys.exit(1)

ref_pdb = str(ref_pdbs[0])
print(f"🔍 Reference: {{os.path.basename(ref_pdb)}}")

# Find all predicted structures
colabfold_dir = "{colabfold_dir}"
pred_pdbs = sorted(Path(colabfold_dir).glob("*_unrelaxed_rank_001*.pdb"))

if not pred_pdbs:
    print(f"❌ ERROR: No predicted structures found in {{colabfold_dir}}")
    sys.exit(1)

print(f"📊 Found {{len(pred_pdbs)}} predicted structures to analyze")

# Initialize PyMOL
initialize_pymol()

# Perform batch comparison
results = []

for i, pred_pdb in enumerate(pred_pdbs, 1):
    pred_pdb_str = str(pred_pdb)
    basename = os.path.basename(pred_pdb_str)

    if i % 10 == 0:
        print(f"  Processing {{i}}/{{len(pred_pdbs)}}...")

    try:
        rmsd = calculate_ca_rmsd(ref_pdb, pred_pdb_str)

        # Parse temperature and ID from filename
        # Format: jobname_T0.1_id_10_unrelaxed...
        parts = basename.split("_")
        temp = None
        seq_id = None

        for j, part in enumerate(parts):
            if part.startswith("T") and j+1 < len(parts):
                temp = part[1:]  # Remove 'T' prefix
            if part == "id" and j+1 < len(parts):
                seq_id = parts[j+1]

        results.append({{
            "structure": basename,
            "temperature": temp,
            "sequence_id": seq_id,
            "chain": "{design_chain}",
            "rmsd_angstroms": round(rmsd, 3),
            "path": pred_pdb_str
        }})

    except Exception as e:
        print(f"⚠️  Error processing {{basename}}: {{e}}")
        continue

# Sort by RMSD
results.sort(key=lambda x: x["rmsd_angstroms"])

# Save to CSV
output_csv = "{output_csv}"
with open(output_csv, 'w', newline='') as csvfile:
    fieldnames = ["structure", "temperature", "sequence_id", "chain", "rmsd_angstroms", "path"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"\\n✅ RMSD analysis complete!")
print(f"✅ Results saved to: {{output_csv}}")
print(f"\\n🏆 Top 10 designs by RMSD:")
print(f"{{'='*60}}")

for i, result in enumerate(results[:10], 1):
    temp = result['temperature'] if result['temperature'] else 'N/A'
    seq_id = result['sequence_id'] if result['sequence_id'] else 'N/A'
    print(f"  {{i:2d}}. T={{temp:<4s}} ID={{seq_id:<4s}} RMSD={{result['rmsd_angstroms']:.3f}} Å")

print(f"{{'='*60}}")
print(f"📈 Total structures analyzed: {{len(results)}}")

if results:
    best = results[0]
    worst = results[-1]
    avg = sum(r['rmsd_angstroms'] for r in results) / len(results)
    print(f"📊 Best RMSD:    {{best['rmsd_angstroms']:.3f}} Å ({{best['structure']}})")
    print(f"📊 Worst RMSD:   {{worst['rmsd_angstroms']:.3f}} Å")
    print(f"📊 Average RMSD: {{avg:.3f}} Å")

PYTHON_SCRIPT
"""

    with open(script_file, 'w') as f:
        f.write(script_content)

    print(f"✅ Generated PyMOL comparison script")
    return script_file

# ================================
# JOB SUBMISSION
# ================================

def submit_job(script_path, dependency=None):
    """Submit a single SLURM job and return job ID."""
    cmd = ["sbatch"]

    if dependency:
        cmd += ["--dependency", f"afterok:{dependency}"]

    cmd.append(script_path)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Failed to submit {script_path}")
        print(f"Error: {result.stderr}")
        return None

    output = result.stdout.strip()
    job_id = int(output.split()[-1])
    print(f"✅ Submitted job {job_id}: {os.path.basename(script_path)}")

    return job_id

def submit_array_job(script_path, num_tasks, dependency=None):
    """Submit a SLURM array job and return job ID."""
    cmd = ["sbatch", f"--array=1-{num_tasks}"]

    if dependency:
        cmd += ["--dependency", f"afterok:{dependency}"]

    cmd.append(script_path)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Failed to submit {script_path}")
        print(f"Error: {result.stderr}")
        return None

    output = result.stdout.strip()
    job_id = int(output.split()[-1])
    print(f"✅ Submitted array job {job_id} ({num_tasks} tasks): {os.path.basename(script_path)}")

    return job_id

def count_fasta_tasks(cf_tasks_file):
    """Count number of tasks in cf_tasks.txt."""
    if not os.path.isfile(cf_tasks_file):
        return 0

    with open(cf_tasks_file, 'r') as f:
        return len(f.readlines())

# ================================
# MAIN PIPELINE
# ================================

def main():
    """Main pipeline execution."""

    parser = argparse.ArgumentParser(
        description="Unified Protein Design Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py input.fasta
  python run_pipeline.py input.fasta --chain A
  python run_pipeline.py input.fasta --dry-run

The pipeline will:
1. Generate HHblits MSAs and identify conserved residues
2. Predict reference structure with ColabFold (in parallel)
3. Design sequences with LigandMPNN using conserved residues
4. Predict structures of designed sequences with ColabFold

All outputs will be organized in: jobs/JOBNAME/
        """
    )

    parser.add_argument("fasta", help="Input FASTA file")
    parser.add_argument("--chain", default="A", help="Design chain (default: A)")
    parser.add_argument("--dry-run", action="store_true", help="Generate scripts but don't submit jobs")

    args = parser.parse_args()

    # Validate input
    if not validate_fasta(args.fasta):
        sys.exit(1)

    # Get job name and setup directories
    job_name = get_job_name(args.fasta)
    base_dir = os.getcwd()
    job_dir = setup_job_directory(base_dir, job_name)

    # Copy input FASTA
    input_fasta = copy_input_fasta(args.fasta, job_dir, job_name)

    print("\n" + "=" * 60)
    print(f"UNIFIED PROTEIN DESIGN PIPELINE")
    print("=" * 60)
    print(f"Job Name: {job_name}")
    print(f"Design Chain: {args.chain}")
    print(f"Job Directory: {job_dir}")
    print(f"Temperatures: {LIGANDMPNN_TEMPERATURES}")
    print(f"Conservation Threshold: {int(CONSERVATION_THRESHOLD*100)}%")
    print("=" * 60)

    # ================================
    # STAGE 1: GENERATE ALL SCRIPTS
    # ================================

    print("\n📝 STAGE 1: Generating all pipeline scripts...")

    # HHblits scripts
    hhblits_scripts = create_hhblits_scripts(job_dir, job_name, input_fasta)
    hhfilter_script = create_hhfilter_script(job_dir, job_name)
    conservation_script = create_conservation_script(job_dir, job_name)

    # Reference structure script
    reference_script = create_reference_colabfold_script(job_dir, job_name, input_fasta)

    # LigandMPNN scripts
    ligandmpnn_scripts = create_ligandmpnn_scripts(job_dir, job_name, args.chain)
    postprocess_script = create_ligandmpnn_postprocess_script(job_dir, job_name, args.chain)

    # ColabFold monomer script (will need task count after post-processing)
    colabfold_script = create_colabfold_monomer_script(job_dir, job_name)

    # PyMOL comparison script
    pymol_script = create_pymol_comparison_script(job_dir, job_name, args.chain)

    print("✅ All scripts generated!")

    if args.dry_run:
        print("\n🏁 Dry run complete. Scripts generated but not submitted.")
        print(f"\nTo submit manually, use the scripts in: {job_dir}")
        return

    # ================================
    # STAGE 2: SUBMIT JOBS WITH DEPENDENCIES
    # ================================

    print("\n🚀 STAGE 2: Submitting jobs with dependencies...")

    job_ids = {}

    # Submit HHblits chain
    print("\n--- HHblits Chain ---")
    prev_job_id = None
    for script in hhblits_scripts:
        job_id = submit_job(script, dependency=prev_job_id)
        if not job_id:
            print("❌ Failed to submit HHblits chain")
            sys.exit(1)
        prev_job_id = job_id
    job_ids['hhblits_final'] = prev_job_id

    # Submit HHfilter (depends on final HHblits)
    print("\n--- HHfilter ---")
    job_id = submit_job(hhfilter_script, dependency=job_ids['hhblits_final'])
    if not job_id:
        print("❌ Failed to submit HHfilter")
        sys.exit(1)
    job_ids['hhfilter'] = job_id

    # Submit conservation analysis (depends on HHfilter)
    print("\n--- Conservation Analysis ---")
    job_id = submit_job(conservation_script, dependency=job_ids['hhfilter'])
    if not job_id:
        print("❌ Failed to submit conservation analysis")
        sys.exit(1)
    job_ids['conservation'] = job_id

    # Submit reference ColabFold (in parallel, no dependency)
    print("\n--- Reference Structure (ColabFold) ---")
    job_id = submit_job(reference_script)
    if not job_id:
        print("❌ Failed to submit reference ColabFold")
        sys.exit(1)
    job_ids['reference'] = job_id

    # Submit LigandMPNN jobs (depend on both conservation AND reference)
    print("\n--- LigandMPNN Designs ---")
    dependency_str = f"{job_ids['conservation']}:{job_ids['reference']}"
    ligandmpnn_job_ids = []
    for script in ligandmpnn_scripts:
        cmd = ["sbatch", "--dependency", f"afterok:{dependency_str}", script]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to submit {script}")
            continue
        job_id = int(result.stdout.strip().split()[-1])
        ligandmpnn_job_ids.append(job_id)
        print(f"✅ Submitted job {job_id}: {os.path.basename(script)}")

    if not ligandmpnn_job_ids:
        print("❌ Failed to submit LigandMPNN jobs")
        sys.exit(1)
    job_ids['ligandmpnn'] = ligandmpnn_job_ids

    # Submit post-processing (depends on all LigandMPNN jobs)
    print("\n--- Post-Processing ---")
    lmpnn_dependency = ":".join(str(jid) for jid in ligandmpnn_job_ids)
    cmd = ["sbatch", "--dependency", f"afterok:{lmpnn_dependency}", postprocess_script]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to submit post-processing")
        sys.exit(1)
    job_id = int(result.stdout.strip().split()[-1])
    job_ids['postprocess'] = job_id
    print(f"✅ Submitted job {job_id}: {os.path.basename(postprocess_script)}")

    # Submit ColabFold monomer (depends on post-processing)
    # We need to estimate the number of tasks (will be finalized after post-processing)
    print("\n--- ColabFold Monomer Predictions ---")
    # Estimate: temperatures * batches * batch_size - 1 (skip first seq)
    estimated_tasks = len(LIGANDMPNN_TEMPERATURES) * LIGANDMPNN_NUM_BATCHES * LIGANDMPNN_BATCH_SIZE
    estimated_tasks = estimated_tasks - len(LIGANDMPNN_TEMPERATURES)  # Subtract first seqs

    print(f"📊 Estimated ~{estimated_tasks} sequences to predict")
    print(f"⚠️  Note: Actual number determined after post-processing completes")
    print(f"💡 To submit ColabFold after post-processing finishes:")
    print(f"   NUM_TASKS=$(wc -l < {job_dir}/ligandmpnn/cf_tasks.txt)")
    print(f"   sbatch --array=1-$NUM_TASKS --dependency=afterok:{job_ids['postprocess']} {colabfold_script}")

    # For now, we'll use the estimated number
    cmd = ["sbatch", f"--array=1-{estimated_tasks}", "--dependency", f"afterok:{job_ids['postprocess']}", colabfold_script]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  ColabFold submission may have failed (task count estimation)")
        print(f"Error: {result.stderr}")
    else:
        job_id = int(result.stdout.strip().split()[-1])
        job_ids['colabfold'] = job_id
        print(f"✅ Submitted array job {job_id}: {os.path.basename(colabfold_script)}")

    # Submit PyMOL comparison (depends on ColabFold)
    print("\n--- PyMOL RMSD Comparison ---")
    if 'colabfold' in job_ids:
        job_id = submit_job(pymol_script, dependency=job_ids['colabfold'])
        if job_id:
            job_ids['pymol'] = job_id
            print(f"✅ Submitted PyMOL comparison job {job_id}")
        else:
            print("⚠️  PyMOL comparison submission failed (non-critical)")
    else:
        print("⚠️  Skipping PyMOL comparison (ColabFold not submitted)")

    # ================================
    # STAGE 3: SUMMARY
    # ================================

    print("\n" + "=" * 60)
    print("🎉 PIPELINE SUBMITTED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\n📁 Job Directory: {job_dir}")
    print(f"\n📋 Submitted Jobs:")
    print(f"   HHblits chain:        Job {job_ids['hhblits_final']}")
    print(f"   HHfilter:             Job {job_ids['hhfilter']}")
    print(f"   Conservation:         Job {job_ids['conservation']}")
    print(f"   Reference structure:  Job {job_ids['reference']}")
    print(f"   LigandMPNN designs:   Jobs {ligandmpnn_job_ids}")
    print(f"   Post-processing:      Job {job_ids['postprocess']}")
    if 'colabfold' in job_ids:
        print(f"   ColabFold monomer:    Job {job_ids['colabfold']}")
    if 'pymol' in job_ids:
        print(f"   PyMOL comparison:     Job {job_ids['pymol']}")

    print(f"\n📊 Monitor jobs with: squeue -u $USER")
    print(f"📂 View logs in: {job_dir}/logs/")
    print(f"\n🎯 Expected outputs:")
    print(f"   - Conserved residues: {job_dir}/hhblits/{job_name}_conserved_residues.xlsx")
    print(f"   - Reference structure: {job_dir}/reference/colabfold_output/")
    print(f"   - LigandMPNN designs: {job_dir}/ligandmpnn/T*/")
    print(f"   - Structure predictions: {job_dir}/colabfold/colabfold_output/")
    print(f"   - RMSD analysis: {job_dir}/pymol_analysis/{job_name}_rmsd_results.csv")

    print(f"\n✅ Complete pipeline submitted for {job_name}!")

if __name__ == "__main__":
    main()