[View Script: chai_to_boltz.py](../example_scripts/folding/boltz2/helpers/chai_to_boltz.py)

# Chai to Boltz2 Format Converter

This document provides a detailed explanation of the `chai_to_boltz.py` helper script located in the `example_scripts/folding/boltz2/helpers/` directory.

## Overview

The `chai_to_boltz.py` script is a Python utility that converts input files from Chai FASTA format to Boltz2 YAML format. This is useful if you already have input files prepared for Chai and want to run the same systems with Boltz2 without manually rewriting the input files.

## Usage

```bash
python chai_to_boltz.py input.fasta [output.yaml]
```

### Arguments

1.  **input.fasta** (required): Path to the input FASTA file in Chai format
2.  **output.yaml** (optional): Path to the output YAML file. If not provided, the script will use the input filename with a `.yaml` extension.

### Examples

```bash
# Convert to auto-named output file (protein_ligand.yaml)
python chai_to_boltz.py protein_ligand.fasta

# Convert to specific output file
python chai_to_boltz.py protein_ligand.fasta my_system.yaml

# Using full paths
python chai_to_boltz.py /path/to/input.fasta /path/to/output.yaml
```

## Input Format: Chai FASTA

The script expects input files in Chai FASTA format, where each sequence header has the format:

```
>type|name
```

-   **type**: The entity type (protein, ligand, dna, or rna)
-   **name**: A descriptive name for the entity

### Example Chai FASTA File

```fasta
>protein|MyEnzyme
MKLAVFLALAAGVLGVAVQPQSQFRYESPVLGGSHLPGASNGDPSTSPAFSDPGFHPSDHGFNP
>ligand|ATP
C1=NC(=C2C(=N1)N(C=N2)C3C(C(C(O3)COP(=O)(O)OP(=O)(O)OP(=O)(O)O)O)O)N
>dna|PromoterRegion
ATCGATCGATCGTAGC
```

### Supported Entity Types

- **protein**: Protein sequences (amino acids in single-letter code)
- **ligand**: Small molecules (SMILES strings)
- **dna**: DNA sequences (nucleotides: A, T, C, G)
- **rna**: RNA sequences (nucleotides: A, U, C, G)

**Note:** If the script encounters an unknown entity type, it will treat it as a ligand and issue a warning.

## Output Format: Boltz2 YAML

The script generates YAML files in Boltz2 format with automatic chain ID assignment.

### Conversion Rules

1.  **Chain IDs**: Automatically assigned in alphabetical order (A, B, C, ...)
2.  **Protein sequences**: Converted to `protein` entries with `sequence` field
3.  **Ligand SMILES**: Converted to `ligand` entries with `smiles` field
4.  **DNA/RNA sequences**: Converted to `dna`/`rna` entries with `sequence` field
5.  **Comments**: Original entity names are preserved as YAML comments

### Example Conversion

**Input (Chai FASTA):**
```fasta
>protein|MyEnzyme
MKLAVFLALAAGVLGVAVQPQSQFRYESP
>ligand|ATP
C1=NC(=C2C(=N1)N(C=N2)C3C(C(C(O3)COP(=O)(O)OP(=O)(O)OP(=O)(O)O)O)O)N
>dna|PromoterRegion
ATCGATCGATCGTAGC
```

**Output (Boltz2 YAML):**
```yaml
version: 1
sequences:
  - protein:
      id: A
      sequence: MKLAVFLALAAGVLGVAVQPQSQFRYESP
      # MyEnzyme
  - ligand:
      id: B
      smiles: 'C1=NC(=C2C(=N1)N(C=N2)C3C(C(C(O3)COP(=O)(O)OP(=O)(O)OP(=O)(O)O)O)O)N'
      # ATP
  - dna:
      id: C
      sequence: ATCGATCGATCGTAGC
      # PromoterRegion
```

## Script Breakdown

The script performs the following steps:

1.  **Argument Parsing**: Validates command-line arguments and checks that the input file exists.

2.  **Output Filename Determination**: If no output filename is provided, replaces the input file extension with `.yaml`.

3.  **FASTA Parsing**: Reads the input file and extracts sequence headers and sequences.
    -   Headers are parsed to extract entity type and name
    -   Multi-line sequences are concatenated

4.  **Format Conversion**: Converts each sequence to Boltz2 YAML format.
    -   Assigns chain IDs sequentially (A, B, C, ...)
    -   Generates appropriate YAML structure based on entity type
    -   Preserves entity names as comments

5.  **Output Writing**: Writes the formatted YAML to the output file.

6.  **Summary Report**: Prints conversion summary to stderr, including:
    -   Input and output filenames
    -   Number of sequences found
    -   Entity types and names
    -   Usage instructions for running with Boltz2

## Error Handling

The script includes error handling for common issues:

**No input file provided:**
```
Error: No input file provided
Usage: chai_to_boltz.py input.fasta [output.yaml]
```

**Input file doesn't exist:**
```
Error: Input file 'filename.fasta' does not exist
```

**Malformed headers:**
```
Warning: Skipping malformed header: invalid_header
```

**Unknown entity types:**
```
Warning: Unknown entity type 'unknown' for EntityName
         Treating as ligand with SMILES
```

**No sequences found:**
```
Error: No sequences found in input file
```

## Complete Workflow Example

### Example 1: Protein-Ligand Complex

**Step 1: Create Chai FASTA file**
```bash
cat > enzyme_substrate.fasta << 'EOF'
>protein|Kinase
MKLAVFLALAAGVLGVAVQPQSQFRYESPVLGGSHLPGASNGDPSTSPAFSDPGFHPSDHGFNP
>ligand|Ibuprofen
CC(C)Cc1ccc(cc1)C(C)C(=O)O
EOF
```

**Step 2: Convert to Boltz2 YAML**
```bash
python example_scripts/folding/boltz2/helpers/chai_to_boltz.py enzyme_substrate.fasta
```

**Output:**
```
Converting enzyme_substrate.fasta to enzyme_substrate.yaml...
Found 2 sequences:
  - protein: Kinase
  - ligand: Ibuprofen

Conversion complete! Output written to: enzyme_substrate.yaml

To run with Boltz2:
  sbatch run_boltz.sh enzyme_substrate.yaml --use_msa_server
```

**Step 3: Submit to Boltz2**
```bash
sbatch example_scripts/folding/boltz2/runners/run_boltz.sh enzyme_substrate.yaml --use_msa_server
```

### Example 2: Multi-Component System

**Step 1: Create complex Chai FASTA file**
```bash
cat > complex_system.fasta << 'EOF'
>protein|ChainA
MKLAVFLALAAGVLGVAVQPQS
>protein|ChainB
MHHHHHHSSGVDLGTENLYFQS
>ligand|Cofactor
CC(C)CCCC(C)CCCC(C)CCCC(C)C
>dna|Binding_Site
ATCGATCG
EOF
```

**Step 2: Convert and submit**
```bash
python example_scripts/folding/boltz2/helpers/chai_to_boltz.py complex_system.fasta
sbatch example_scripts/folding/boltz2/runners/run_boltz.sh complex_system.yaml --use_msa_server --use_potentials
```

## Validation Tips

### Validate YAML Output

After conversion, you can validate the YAML syntax:

```bash
python -c "import yaml; yaml.safe_load(open('output.yaml'))"
```

If the YAML is valid, no output will be produced. If there's an error, you'll see a Python exception.

### Validate SMILES Strings (for ligands)

If your input contains ligands with SMILES strings, you can validate them using RDKit:

```bash
python << 'EOF'
from rdkit import Chem
smiles = 'CC(C)Cc1ccc(cc1)C(C)C(=O)O'
mol = Chem.MolFromSmiles(smiles)
if mol is None:
    print("Invalid SMILES string!")
else:
    print(f"Valid SMILES: {Chem.MolToSmiles(mol)}")
EOF
```

## Common Use Cases

### Converting Batch Files

If you have multiple Chai FASTA files to convert:

```bash
# Convert all FASTA files in current directory
for file in *.fasta; do
    python example_scripts/folding/boltz2/helpers/chai_to_boltz.py "$file"
done
```

### Converting and Submitting

Combine conversion and submission in a single workflow:

```bash
# Convert
python example_scripts/folding/boltz2/helpers/chai_to_boltz.py input.fasta

# Submit
sbatch example_scripts/folding/boltz2/runners/run_boltz.sh input.yaml --use_msa_server
```

Or as a one-liner:

```bash
python example_scripts/folding/boltz2/helpers/chai_to_boltz.py input.fasta && \
sbatch example_scripts/folding/boltz2/runners/run_boltz.sh input.yaml --use_msa_server
```

## Limitations

1.  **Header Format**: Requires strict adherence to `>type|name` format
2.  **Single-line vs Multi-line**: Handles both, but some very long sequences might need verification
3.  **Entity Types**: Only supports protein, ligand, dna, and rna
4.  **SMILES Validation**: Does not validate SMILES strings (use RDKit separately for validation)
5.  **Chain ID Limit**: Limited to 26 chains (A-Z) in current implementation

## Troubleshooting

### Common Issues

**1. "Skipping malformed header"**
- Check that headers follow the `>type|name` format
- Ensure there's a pipe character (`|`) separating type and name
- Fix example:
  ```
  # Wrong
  >protein MyProtein

  # Correct
  >protein|MyProtein
  ```

**2. "Unknown entity type"**
- Use supported types: protein, ligand, dna, rna
- The script will treat unknown types as ligands
- Fix if needed by editing the FASTA file

**3. "No sequences found"**
- Check that file is not empty
- Verify FASTA format (headers start with `>`)
- Ensure sequences are present after headers

**4. Empty sequences in output**
- Verify input FASTA has sequences after headers
- Check for blank lines that might interrupt sequences

**5. Invalid YAML generated**
- Usually caused by special characters in sequences
- Check for non-standard amino acids or nucleotides
- Validate SMILES strings separately

### Debugging Tips

1.  **Inspect intermediate output:**
```bash
python chai_to_boltz.py input.fasta output.yaml 2>&1 | tee conversion.log
```

2.  **Check file contents:**
```bash
# View input
cat input.fasta

# View output
cat output.yaml
```

3.  **Test with minimal example:**
```bash
cat > test.fasta << 'EOF'
>protein|Test
MKLAVF
EOF

python chai_to_boltz.py test.fasta
cat test.yaml
```

## Best Practices

1.  **Descriptive Names**: Use clear, descriptive names in the `|name` part of headers
2.  **Validate SMILES**: Check SMILES strings before conversion using chemistry tools
3.  **Check Output**: Always inspect the generated YAML before submitting large jobs
4.  **Backup**: Keep original Chai FASTA files after conversion
5.  **Test First**: Test conversion with a small example before processing many files
6.  **Documentation**: Document what each chain represents in your research notes

## Related Documentation

- [run_boltz.sh](run_boltz.md) - Main Boltz2 submission script
- [Chai Documentation](run_chai.md) - Original Chai format documentation
- [Boltz2 GitHub](https://github.com/jwohlwend/boltz) - Boltz2 documentation and examples

## Additional Notes

### Why Convert from Chai to Boltz2?

- **Cross-compatibility**: Run the same systems with different prediction tools
- **Comparison**: Compare Chai and Boltz2 predictions on identical inputs
- **Workflow Integration**: Use existing Chai preprocessing pipelines with Boltz2
- **Convenience**: Avoid manually rewriting input files

### Differences Between Tools

While both Chai and Boltz2 can predict similar systems, they have different strengths:

- **Chai**: Generally faster, FASTA input format
- **Boltz2**: More flexible YAML format, additional configuration options
- **AlphaFold 3**: Most accurate but requires JSON format and more resources

This converter helps you leverage the strengths of multiple tools without duplicating input preparation work.
