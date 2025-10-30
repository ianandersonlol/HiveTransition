import sys
from pathlib import Path
import torch
from chai_lab.chai1 import run_inference


if len(sys.argv) < 3 or len(sys.argv) > 4:
    print(f"Usage: {sys.argv[0]} <input_fasta_file> <output_directory> [msa_directory]")
    print("  msa_directory is optional - if not provided, will use MSA server")
    sys.exit(1)


fasta_path = Path(sys.argv[1])
output_dir = Path(sys.argv[2])


msa_directory = None
if len(sys.argv) == 4:
    msa_directory = Path(sys.argv[3])
    if not msa_directory.exists():
        print(f"Error: The MSA directory '{msa_directory}' does not exist.")
        sys.exit(1)


if not fasta_path.exists():
    print(f"Error: The file '{fasta_path}' does not exist.")
    sys.exit(1)


if not output_dir.exists():
    output_dir.mkdir(parents=True, exist_ok=True)


use_msa_server = msa_directory is None
if use_msa_server:
    print("Using MSA server (ColabFold MMseqs2) for automatic MSA generation...")
else:
    print(f"Using pre-computed MSAs from directory: {msa_directory}")

output_paths = run_inference(
    fasta_file=fasta_path,
    output_dir=output_dir,
    num_trunk_recycles=3,
    num_diffn_timesteps=200,
    seed=42,
    device=torch.device("cuda:0"),
    use_esm_embeddings=True,
    # MSA configuration
    msa_directory=msa_directory,
    use_msa_server=use_msa_server,
)

print(f"Inference complete with MSA support. Outputs saved to: {output_paths}")