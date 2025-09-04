[View Script: chai_with_msa.py](../example_scripts/chai_with_msa.py)
[View Script: submit_chai_with_msa.sh](../example_scripts/submit_chai_with_msa.sh)

# `chai_with_msa.py`

This script performs protein structure prediction using the `chai_lab` library with support for Multiple Sequence Alignments (MSAs). It can use either a pre-computed MSA or an MSA server (ColabFold's MMseqs2).

## Usage

```bash
python example_scripts/chai_with_msa.py <input_fasta_file> <output_directory> [msa_directory]
```

### Arguments

*   `<input_fasta_file>`: Path to the input FASTA file containing the protein sequence.
*   `<output_directory>`: Path to the directory where the output PDB file will be saved.
*   `[msa_directory]` (optional): Path to a directory containing pre-computed MSAs. If not provided, the script will use an MSA server.

## Example with MSA Server

```bash
python example_scripts/chai_with_msa.py inputs/my_protein.fasta outputs/
```

## Example with Pre-computed MSA

```bash
python example_scripts/chai_with_msa.py inputs/my_protein.fasta outputs/ my_msas/
```

## Script Details

The script uses the `chai_lab.chai1.run_inference` function. Key parameters include:

*   `num_trunk_recycles`: 3
*   `num_diffn_timesteps`: 200
*   `seed`: 42
*   `device`: "cuda:0"
*   `use_esm_embeddings`: True
*   `msa_directory`: Path to the MSA directory (if provided).
*   `use_msa_server`: True if no MSA directory is provided.
