"""
Run AF2 initial guess on multiple sequences from a FASTA file using a reference PDB
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from Bio import SeqIO
import pyrosetta
from pyrosetta import pose_from_pdb
from pyrosetta.rosetta.core.pose import Pose
from pyrosetta.rosetta.core.chemical import oneletter_to_name3
from pyrosetta.rosetta.protocols.simple_moves import MutateResidue


def parse_args():
    parser = argparse.ArgumentParser(
        description='Run AF2 initial guess on sequences from FASTA with reference PDB'
    )
    parser.add_argument(
        '-f', '--fasta',
        required=True,
        help='Path to multi-sequence FASTA file'
    )
    parser.add_argument(
        '-r', '--reference',
        required=True,
        help='Path to reference PDB structure'
    )
    parser.add_argument(
        '-o', '--output_dir',
        required=True,
        help='Output directory for AF2 predictions'
    )
    parser.add_argument(
        '--recycle',
        type=int,
        default=3,
        help='Number of AF2 recycles (default: 3)'
    )
    parser.add_argument(
        '--force_monomer',
        action='store_true',
        help='Force monomer prediction (no template)'
    )

    return parser.parse_args()


def thread_sequence_onto_pdb(ref_pdb_path, sequence, output_pdb_path):
    """
    Thread a sequence onto a reference PDB structure using PyRosetta
    """
    # Load reference structure
    pose = pose_from_pdb(ref_pdb_path)

    # Check sequence length matches
    if len(sequence) != pose.total_residue():
        raise ValueError(
            f"Sequence length ({len(sequence)}) doesn't match "
            f"PDB residue count ({pose.total_residue()})"
        )

    # Thread sequence onto structure
    for i, aa in enumerate(sequence, start=1):
        # Convert single-letter to three-letter code
        aa3 = oneletter_to_name3(aa)

        # Mutate residue
        mutator = MutateResidue(i, aa)
        mutator.apply(pose)

    # Save threaded structure
    pose.dump_pdb(output_pdb_path)


def create_input_pdbs(fasta_file, ref_pdb, input_dir):
    """
    Create PDB files for each sequence by threading onto reference structure
    Returns list of PDB tags (without .pdb extension)
    """
    # Initialize PyRosetta (quiet mode)
    pyrosetta.init('-mute all')

    tags = []
    sequences = list(SeqIO.parse(fasta_file, 'fasta'))

    print(f"Processing {len(sequences)} sequences from {fasta_file}")
    print(f"Reference PDB: {ref_pdb}")

    for i, record in enumerate(sequences, start=1):
        # Create tag from sequence ID or use index
        seq_id = record.id if record.id else f"seq_{i:04d}"
        # Clean tag (remove special characters that might cause issues)
        tag = ''.join(c if c.isalnum() or c in '_-' else '_' for c in seq_id)

        output_pdb = os.path.join(input_dir, f"{tag}.pdb")

        try:
            thread_sequence_onto_pdb(ref_pdb, str(record.seq), output_pdb)
            tags.append(tag)
            print(f"  [{i}/{len(sequences)}] Created {tag}.pdb")
        except Exception as e:
            print(f"  ERROR processing {tag}: {e}")
            continue

    return tags


def create_runlist(tags, runlist_path):
    """
    Create runlist file with one tag per line
    """
    with open(runlist_path, 'w') as f:
        for tag in tags:
            f.write(f"{tag}\n")
    print(f"\nCreated runlist with {len(tags)} entries: {runlist_path}")


def run_af2(input_dir, output_dir, runlist_path, recycle=3, force_monomer=False):
    """
    Run AF2 predict.py on the prepared inputs
    """
    # Paths
    af2_script = "/quobyte/jbsiegelgrp/software/dl_binder_design/af2_initial_guess/predict.py"
    checkpoint_file = os.path.join(output_dir, "checkpoint.txt")
    score_file = os.path.join(output_dir, "af2_scores.sc")

    # Build AF2 command
    cmd = [
        "python", af2_script,
        "-pdbdir", input_dir,
        "-outpdbdir", output_dir,
        "-runlist", runlist_path,
        "-checkpoint_name", checkpoint_file,
        "-scorefilename", score_file,
        "-recycle", str(recycle)
    ]

    if force_monomer:
        cmd.append("-force_monomer")

    print(f"\nRunning AF2 prediction...")
    print(f"Command: {' '.join(cmd)}\n")

    # Run AF2
    subprocess.run(cmd, check=True)

    print(f"\nAF2 prediction complete!")
    print(f"  Output directory: {output_dir}")
    print(f"  Score file: {score_file}")


def main():
    args = parse_args()

    # Validate inputs
    if not os.path.exists(args.fasta):
        print(f"ERROR: FASTA file not found: {args.fasta}")
        sys.exit(1)

    if not os.path.exists(args.reference):
        print(f"ERROR: Reference PDB not found: {args.reference}")
        sys.exit(1)

    # Create output directory structure
    os.makedirs(args.output_dir, exist_ok=True)
    input_dir = os.path.join(args.output_dir, "input_pdbs")
    os.makedirs(input_dir, exist_ok=True)

    runlist_path = os.path.join(args.output_dir, "runlist.txt")

    print("="*80)
    print("AF2 Initial Guess from Multi-Sequence FASTA")
    print("="*80)

    # Step 1: Create input PDBs by threading sequences onto reference
    print("\nStep 1: Threading sequences onto reference structure...")
    tags = create_input_pdbs(args.fasta, args.reference, input_dir)

    if not tags:
        print("\nERROR: No valid sequences could be processed!")
        sys.exit(1)

    # Step 2: Create runlist
    print("\nStep 2: Creating runlist...")
    create_runlist(tags, runlist_path)

    # Step 3: Run AF2
    print("\nStep 3: Running AF2 prediction...")
    run_af2(
        input_dir=input_dir,
        output_dir=args.output_dir,
        runlist_path=runlist_path,
        recycle=args.recycle,
        force_monomer=args.force_monomer
    )

    print("\n" + "="*80)
    print("COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    main()