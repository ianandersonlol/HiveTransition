# `run_chai.py`

This script performs protein structure prediction using the `chai_lab` library. It takes a FASTA file containing the protein sequence as input and generates a PDB file with the predicted structure.

## Usage

```bash
python example_scripts/run_chai.py <input_fasta_file> <output_directory>
```

### Arguments

*   `<input_fasta_file>`: Path to the input FASTA file containing the protein sequence.
*   `<output_directory>`: Path to the directory where the output PDB file will be saved.

## Example

```bash
python example_scripts/run_chai.py inputs/my_protein.fasta outputs/
```

This will generate a PDB file in the `outputs/` directory.

## Script Details

The script uses the `chai_lab.chai1.run_inference` function to perform the structure prediction. It is configured with the following parameters:

*   `num_trunk_recycles`: 3
*   `num_diffn_timesteps`: 200
*   `seed`: 42
*   `device`: "cuda:0"
*   `use_esm_embeddings`: True
