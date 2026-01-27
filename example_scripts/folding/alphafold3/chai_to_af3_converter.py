#!/usr/bin/env python3
"""
Convert Chai Discovery formatted FASTA to AlphaFold3 formatted JSON
"""

import json
import argparse
from typing import Dict, List, Tuple
import re


def parse_chai_fasta(fasta_path: str) -> Tuple[List[Dict], Dict[str, str], Dict[str, str]]:
    """Parse Chai Discovery FASTA format and extract sequences with metadata."""
    sequences = []
    current_header = None
    current_sequence = []

    with open(fasta_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                # Save previous sequence if exists
                if current_header and current_sequence:
                    sequences.append({
                        'header': current_header,
                        'sequence': ''.join(current_sequence)
                    })
                    current_sequence = []

                current_header = line[1:]  # Remove '>'
            else:
                current_sequence.append(line)

        # Save last sequence
        if current_header and current_sequence:
            sequences.append({
                'header': current_header,
                'sequence': ''.join(current_sequence)
            })

    # Assign chain IDs as A, B, C, D, etc. in order
    chains = {}
    headers = {}
    for i, seq_data in enumerate(sequences):
        header = seq_data['header']
        sequence = seq_data['sequence']
        chain_id = chr(ord('A') + i)  # A, B, C, D, ...

        chains[chain_id] = sequence
        headers[chain_id] = header

    return sequences, chains, headers


def is_smiles_string(sequence: str) -> bool:
    """Check if a string is likely a SMILES notation."""
    # SMILES typically contain these characters
    smiles_chars = set('CNOSPFClBrI[]()=#@+-.0123456789\\/')
    # And often have these patterns
    smiles_patterns = ['C(', ')', '[', ']', '=', '#', '@', 'Cl', 'Br', 'O', 'N', 'S']

    # Remove whitespace
    seq = sequence.strip()

    # Check if it contains typical SMILES characters
    if not all(c in smiles_chars or c.isspace() for c in seq):
        return False

    # Check for common SMILES patterns
    smiles_score = 0
    for pattern in smiles_patterns:
        if pattern in seq:
            smiles_score += 1

    # If it has brackets or parentheses and other SMILES features, likely SMILES
    has_brackets = '(' in seq or '[' in seq
    has_bonds = '=' in seq or '#' in seq

    return smiles_score >= 2 or (has_brackets and len(seq) < 500)


def determine_entity_type(sequence: str, header: str = "") -> str:
    """Determine if sequence is protein, DNA, RNA, or ligand/SMILES."""
    sequence = sequence.strip().upper()

    # Check header for hints
    header_lower = header.lower()
    if any(keyword in header_lower for keyword in ['ligand', 'smiles', 'small molecule', 'compound']):
        return 'ligand'

    # Check if it's a SMILES string
    if is_smiles_string(sequence):
        return 'ligand'

    # Count nucleotide characters
    nucleotides = set('ATCGU')
    amino_acids = set('ACDEFGHIKLMNPQRSTVWY')

    seq_chars = set(sequence.replace('-', '').replace('X', ''))

    # Check if mostly nucleotides
    if seq_chars.issubset(nucleotides):
        if 'U' in seq_chars:
            return 'rna'
        else:
            return 'dna'
    else:
        return 'protein'


def sanitize_sequence(sequence: str) -> str:
    """Remove truncation markers ('-') from sequences."""
    return sequence.replace('-', '')


def create_af3_json(chains: Dict[str, str], headers: Dict[str, str], job_name: str = "chai_to_af3_conversion") -> Dict:
    """Create AlphaFold3 formatted JSON from parsed chains."""
    af3_json = {
        "name": job_name,
        "sequences": [],
        "dialect": "alphafold3",
        "version": 1
    }

    # Process each chain
    for chain_id, sequence in sorted(chains.items()):
        header = headers.get(chain_id, "")
        entity_type = determine_entity_type(sequence, header)

        if entity_type == 'protein':
            entity = {
                "protein": {
                    "id": chain_id,
                    "sequence": sanitize_sequence(sequence)
                }
            }
        elif entity_type == 'dna':
            entity = {
                "dna": {
                    "id": chain_id,
                    "sequence": sanitize_sequence(sequence)
                }
            }
        elif entity_type == 'rna':
            entity = {
                "rna": {
                    "id": chain_id,
                    "sequence": sanitize_sequence(sequence)
                }
            }
        elif entity_type == 'ligand':
            # Don't sanitize SMILES - dashes are valid in SMILES notation
            entity = {
                "ligand": {
                    "id": chain_id,
                    "smiles": sequence.strip()
                }
            }

        af3_json["sequences"].append(entity)

    # Add modelSeeds for reproducibility
    af3_json["modelSeeds"] = [42]  # Default seed

    return af3_json


def main():
    parser = argparse.ArgumentParser(
        description='Convert Chai Discovery FASTA to AlphaFold3 JSON format'
    )
    parser.add_argument('input_fasta', help='Input FASTA file in Chai Discovery format')
    parser.add_argument('output_json', nargs='?', help='Output JSON file (default: input filename with .json extension)')
    parser.add_argument('--output-dir', '-o', help='Output directory for JSON file (overrides output_json path)')
    parser.add_argument('--name', default='chai_to_af3_conversion',
                       help='Job name for the AlphaFold3 run')
    parser.add_argument('--seeds', nargs='+', type=int, default=[42],
                       help='Model seeds for AlphaFold3 (default: 42)')

    args = parser.parse_args()

    import os

    # Get base name from input file
    base_name = os.path.splitext(os.path.basename(args.input_fasta))[0]

    # Use input filename as job name if not specified
    if args.name == 'chai_to_af3_conversion':
        args.name = base_name

    # Auto-generate output filename if not provided
    if not args.output_json:
        args.output_json = base_name + '.json'

    # If output directory is specified, place the output file there
    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        args.output_json = os.path.join(args.output_dir, os.path.basename(args.output_json))

    # Parse the FASTA file
    print(f"Reading Chai Discovery FASTA from: {args.input_fasta}")
    sequences, chains, headers = parse_chai_fasta(args.input_fasta)

    print(f"Found {len(chains)} chain(s):")
    for chain_id, seq in chains.items():
        header = headers.get(chain_id, "")
        entity_type = determine_entity_type(seq, header)
        if entity_type == 'ligand':
            print(f"  Chain {chain_id}: {entity_type} (SMILES: {seq.strip()})")
        else:
            print(f"  Chain {chain_id}: {entity_type} ({len(seq)} residues)")

    # Create AlphaFold3 JSON
    af3_json = create_af3_json(chains, headers, args.name)
    af3_json["modelSeeds"] = args.seeds

    # Write output JSON
    with open(args.output_json, 'w') as f:
        json.dump(af3_json, f, indent=2)

    print(f"\nAlphaFold3 JSON written to: {args.output_json}")
    print("\nExample AlphaFold3 command:")
    print(f"alphafold3 --json_path={args.output_json} --output_dir=./af3_output")


if __name__ == "__main__":
    main()
