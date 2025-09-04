import sys
from pathlib import Path
import torch
from chai_lab.chai1 import run_inference


if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <input_fasta_file> <output_directory>")
    sys.exit(1)

fasta_path = Path(sys.argv[1])
output_dir = Path(sys.argv[2])

if not fasta_path.exists():
    print(f"Error: The file '{fasta_path}' does not exist.")
    sys.exit(1)

if not output_dir.exists():
    output_dir.mkdir(parents=True, exist_ok=True)

output_paths = run_inference(
    fasta_file=fasta_path,
    output_dir=output_dir,
    num_trunk_recycles=3,
    num_diffn_timesteps=200,
    seed=42,
    device=torch.device("cuda:0"),
    use_esm_embeddings=True,
)

print(f"Inference complete. Outputs saved to: {output_paths}")