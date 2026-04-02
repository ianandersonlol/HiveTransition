#!/bin/bash --norc
#SBATCH --job-name=bindcraft_setup
#SBATCH --partition=high
#SBATCH --account=jbsiegelgrp
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH --output=logs/bindcraft_setup_%j.out
#SBATCH --error=logs/bindcraft_setup_%j.err

set -eo pipefail
mkdir -p logs

# ============================================================================
# Create a fresh BindCraft conda environment with CUDA JAX support
#
# Usage: sbatch setup_bindcraft_env.sh
#
# This creates the env at /quobyte/jbsiegelgrp/software/envs/BindCraft
# ============================================================================

ENV_PATH="/quobyte/jbsiegelgrp/software/envs/BindCraft"
BINDCRAFT_DIR="/quobyte/jbsiegelgrp/software/BindCraft"

echo "=========================================="
echo "BindCraft Environment Setup"
echo "=========================================="
echo "Job ID:    ${SLURM_JOB_ID:-local}"
echo "Hostname:  $(hostname)"
echo "Env path:  ${ENV_PATH}"
echo "Date:      $(date)"
echo "=========================================="

module load conda/latest
eval "$(conda shell.bash hook)"

# Remove old env if it exists
if [ -d "${ENV_PATH}" ]; then
    echo "Removing existing environment at ${ENV_PATH}..."
    conda env remove -p "${ENV_PATH}" -y 2>/dev/null || rm -rf "${ENV_PATH}"
fi

# Create fresh Python 3.10 environment
echo "Creating conda environment..."
conda create -p "${ENV_PATH}" python=3.10 -y

# Activate
conda activate "${ENV_PATH}"

# Install packages with CUDA JAX support (CUDA 12)
echo "Installing packages with CUDA JAX..."
CONDA_OVERRIDE_CUDA="12" conda install \
    pip pandas matplotlib 'numpy<2.0.0' biopython scipy pdbfixer seaborn libgfortran5 tqdm jupyter ffmpeg pyrosetta fsspec py3dmol \
    chex dm-haiku 'flax<0.10.0' dm-tree joblib ml-collections immutabledict optax \
    'jax>=0.4,<=0.6.0' 'jaxlib>=0.4,<=0.6.0=*cuda*' cuda-nvcc cudnn \
    -c conda-forge -c nvidia --channel https://conda.graylab.jhu.edu -y

# Install ColabDesign
echo "Installing ColabDesign..."
pip install git+https://github.com/sokrypton/ColabDesign.git --no-deps

# Install DAlphaBall for BindCraft scoring
echo "Installing DAlphaBall..."
if [ -f "${BINDCRAFT_DIR}/functions/dssp_dalpha/DAlphaBall.gcc" ]; then
    chmod +x "${BINDCRAFT_DIR}/functions/dssp_dalpha/DAlphaBall.gcc"
fi

# Download AlphaFold2 weights if not already present
AF2_PARAMS_DIR="${ENV_PATH}/lib/python3.10/site-packages/colabdesign/af/alphafold/data"
if [ ! -d "${AF2_PARAMS_DIR}/params" ]; then
    echo "Downloading AlphaFold2 weights..."
    mkdir -p "${AF2_PARAMS_DIR}"
    params_file="${AF2_PARAMS_DIR}/alphafold_params.tar"
    wget -O "${params_file}" "https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar"
    tar -xf "${params_file}" -C "${AF2_PARAMS_DIR}"
    rm -f "${params_file}"
else
    echo "AlphaFold2 weights already present, skipping download."
fi

# Verify installation
echo ""
echo "=========================================="
echo "Verifying installation..."
echo "=========================================="
python -c "import jax; print(f'JAX {jax.__version__}, backend: {jax.default_backend()}')"
python -c "import colabdesign; print('ColabDesign OK')"
python -c "import pyrosetta; print('PyRosetta OK')"

echo ""
echo "=========================================="
echo "BindCraft environment setup complete!"
echo "Env location: ${ENV_PATH}"
echo "Date: $(date)"
echo "=========================================="
