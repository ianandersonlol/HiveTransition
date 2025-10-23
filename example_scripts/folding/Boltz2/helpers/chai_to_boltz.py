#!/usr/bin/env python3
"""
Convert CHAI fasta format to Boltz2 YAML format.

Usage:
    python chai_to_boltz.py input.fasta [output.yaml]

If output filename is not provided, will use input filename with .yaml extension.
"""

import sys
import os
from pathlib import Path


def parse_chai_fasta(fasta_file):
    """Parse CHAI fasta file and extract sequences."""
    sequences = []

    with open(fasta_file, 'r') as f:
        current_header = None
        current_seq = []

        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith('>'):
                # Save previous entry if exists
                if current_header is not None:
                    sequences.append({
                        'header': current_header,
                        'sequence': ''.join(current_seq)
                    })

                # Parse new header
                current_header = line[1:]  # Remove '>'
                current_seq = []
            else:
                current_seq.append(line)

        # Save last entry
        if current_header is not None:
            sequences.append({
                'header': current_header,
                'sequence': ''.join(current_seq)
            })

    return sequences


def convert_to_boltz_yaml(sequences):
    """Convert parsed CHAI sequences to Boltz2 YAML format."""
    yaml_lines = ['version: 1', 'sequences:']

    # Track chain IDs
    chain_id_counter = ord('A')

    for seq_entry in sequences:
        header = seq_entry['header']
        sequence = seq_entry['sequence']

        # Parse header: format is "type|name"
        parts = header.split('|', 1)
        if len(parts) != 2:
            print(f"Warning: Skipping malformed header: {header}", file=sys.stderr)
            continue

        entity_type = parts[0].lower()
        entity_name = parts[1] if len(parts) > 1 else "unknown"

        # Assign chain ID
        chain_id = chr(chain_id_counter)
        chain_id_counter += 1

        if entity_type == 'protein':
            yaml_lines.append(f'  - protein:')
            yaml_lines.append(f'      id: {chain_id}')
            yaml_lines.append(f'      sequence: {sequence}')
            yaml_lines.append(f'      # {entity_name}')

        elif entity_type == 'ligand':
            yaml_lines.append(f'  - ligand:')
            yaml_lines.append(f'      id: {chain_id}')
            yaml_lines.append(f"      smiles: '{sequence}'")
            yaml_lines.append(f'      # {entity_name}')

        elif entity_type in ['dna', 'rna']:
            yaml_lines.append(f'  - {entity_type}:')
            yaml_lines.append(f'      id: {chain_id}')
            yaml_lines.append(f'      sequence: {sequence}')
            yaml_lines.append(f'      # {entity_name}')

        else:
            print(f"Warning: Unknown entity type '{entity_type}' for {entity_name}", file=sys.stderr)
            print(f"         Treating as ligand with SMILES", file=sys.stderr)
            yaml_lines.append(f'  - ligand:')
            yaml_lines.append(f'      id: {chain_id}')
            yaml_lines.append(f"      smiles: '{sequence}'")
            yaml_lines.append(f'      # {entity_name}')

    return '\n'.join(yaml_lines)


def main():
    if len(sys.argv) < 2:
        print("Error: No input file provided", file=sys.stderr)
        print(f"Usage: {sys.argv[0]} input.fasta [output.yaml]", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' does not exist", file=sys.stderr)
        sys.exit(1)

    # Determine output filename
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        # Replace extension with .yaml
        input_path = Path(input_file)
        output_file = input_path.with_suffix('.yaml')

    print(f"Converting {input_file} to {output_file}...", file=sys.stderr)

    # Parse and convert
    sequences = parse_chai_fasta(input_file)

    if not sequences:
        print("Error: No sequences found in input file", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(sequences)} sequences:", file=sys.stderr)
    for seq in sequences:
        header_parts = seq['header'].split('|', 1)
        entity_type = header_parts[0]
        entity_name = header_parts[1] if len(header_parts) > 1 else "unknown"
        print(f"  - {entity_type}: {entity_name}", file=sys.stderr)

    yaml_content = convert_to_boltz_yaml(sequences)

    # Write output
    with open(output_file, 'w') as f:
        f.write(yaml_content)
        f.write('\n')

    print(f"\nConversion complete! Output written to: {output_file}", file=sys.stderr)
    print(f"\nTo run with Boltz2:", file=sys.stderr)
    print(f"  sbatch run_boltz.sh {output_file} --use_msa_server", file=sys.stderr)


if __name__ == '__main__':
    main()
