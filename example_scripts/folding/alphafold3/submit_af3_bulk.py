"""
AlphaFold 3 Array Job Submission Script

This script finds all JSON files in a specified directory and submits them as a SLURM array job.
Usage: python submit_af3_bulk.py <directory_path>
"""

import sys
import os
import subprocess
from pathlib import Path
import argparse


def main():
    parser = argparse.ArgumentParser(description='Submit AlphaFold 3 predictions as SLURM array job')
    parser.add_argument('directory', help='Directory containing JSON files to process')
    args = parser.parse_args()

    # Convert to Path object and resolve
    input_dir = Path(args.directory).resolve()

    if not input_dir.exists():
        print(f"Error: Directory {input_dir} does not exist")
        sys.exit(1)

    if not input_dir.is_dir():
        print(f"Error: {input_dir} is not a directory")
        sys.exit(1)

    # Find all JSON files
    json_files = list(input_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {input_dir}")
        sys.exit(1)

    print(f"Found {len(json_files)} JSON file(s) to process")
    print(f"Directory: {input_dir}")
    print()

    # Setup directories
    current_dir_name = input_dir.name
    base_output_dir = input_dir / f"{current_dir_name}_output"
    logs_dir = input_dir / "logs"

    # Create logs directory
    logs_dir.mkdir(exist_ok=True)

    print(f"Base output directory: {base_output_dir}")
    print(f"Logs directory: {logs_dir}")
    print()

    # Create file list for array job
    json_list_file = logs_dir / "json_files_list.txt"
    with open(json_list_file, 'w') as f:
        for json_file in sorted(json_files):
            f.write(f"{json_file.name}\n")

    print(f"Created file list: {json_list_file}")
    print(f"Array job will process indices 1-{len(json_files)}")
    print()

    # Generate SLURM script
    slurm_script_path = input_dir / "af3_array_job.sbatch"

    af3_dir = "/quobyte/jbsiegelgrp/software/alphafold3"

    slurm_script_content = f"""#!/bin/bash
#SBATCH --partition=low
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --array=1-{len(json_files)}
#SBATCH --job-name=af3_array
#SBATCH --output={logs_dir}/af3_%A_%a.txt
#SBATCH --error={logs_dir}/af3_%A_%a.txt

# Load required modules
module load apptainer/latest

# Get the JSON file for this array task
JSON_FILE=$(sed -n "${{SLURM_ARRAY_TASK_ID}}p" "{json_list_file}")
if [ -z "$JSON_FILE" ]; then
    echo "Error: Could not get JSON file for array task ${{SLURM_ARRAY_TASK_ID}}"
    exit 1
fi

# Get the base name without extension and clean it
BASE_NAME="${{JSON_FILE%.json}}"
SAFE_NAME=$(echo "$BASE_NAME" | tr ' ' '_' | tr -cd '[:alnum:]._-')

# Set up paths
INPUT_DIR="{input_dir}"
OUTPUT_DIR="{base_output_dir}/${{SAFE_NAME}}"
LOGS_DIR="{logs_dir}"

START_TIME=$(date +%s)
echo "Starting AlphaFold 3 prediction for $JSON_FILE at $(date)"
echo "Job ID: ${{SLURM_JOB_ID}}"
echo "Array Task ID: ${{SLURM_ARRAY_TASK_ID}}"
echo "Running on node: ${{SLURM_NODELIST}}"
echo "Input JSON: $INPUT_DIR/$JSON_FILE"
echo "Output directory: $OUTPUT_DIR"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Start background GPU monitoring
(
    while true; do
        nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv,noheader >> "${{LOGS_DIR}}/${{SAFE_NAME}}_gpu_monitor_${{SLURM_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}.csv" 2>/dev/null
        sleep 5
    done
) &
MONITOR_PID=$!

# Run AlphaFold 3
singularity exec \\
    --bind "$INPUT_DIR:/input" \\
    --bind "$OUTPUT_DIR:/output" \\
    --bind "{af3_dir}:/models" \\
    --bind "{af3_dir}/public_databases:/databases" \\
    --bind "$LOGS_DIR:/logs" \\
    --nv \\
    "{af3_dir}/alphafold3.sif" \\
    python /app/alphafold/run_alphafold.py \\
    --json_path="/input/$JSON_FILE" \\
    --model_dir=/models \\
    --output_dir=/output \\
    --db_dir=/databases

# Stop GPU monitoring
kill $MONITOR_PID 2>/dev/null || true

END_TIME=$(date +%s)
RUNTIME=$((END_TIME - START_TIME))
HOURS=$((RUNTIME / 3600))
MINUTES=$(( (RUNTIME % 3600) / 60 ))
SECONDS=$((RUNTIME % 60))

echo "Prediction completed at $(date)"
echo "Total runtime: ${{HOURS}}h ${{MINUTES}}m ${{SECONDS}}s"

# Analyze GPU usage from monitoring data
if [ -f "${{LOGS_DIR}}/${{SAFE_NAME}}_gpu_monitor_${{SLURM_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}.csv" ]; then
    echo ""
    echo "=== Resource Usage Summary ==="

    # Get peak VRAM usage and average GPU utilization
    PEAK_VRAM=$(awk -F', ' '{{gsub(" MiB","",$3); if($3>max) max=$3}} END {{printf "%.1f", max/1024}}' "${{LOGS_DIR}}/${{SAFE_NAME}}_gpu_monitor_${{SLURM_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}.csv" 2>/dev/null || echo "N/A")
    TOTAL_VRAM=$(awk -F', ' 'NR==1 {{gsub(" MiB","",$4); printf "%.1f", $4/1024}}' "${{LOGS_DIR}}/${{SAFE_NAME}}_gpu_monitor_${{SLURM_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}.csv" 2>/dev/null || echo "N/A")
    AVG_GPU_UTIL=$(awk -F', ' '{{gsub(" %","",$5); sum+=$5; count++}} END {{if(count>0) printf "%.1f", sum/count; else print "N/A"}}' "${{LOGS_DIR}}/${{SAFE_NAME}}_gpu_monitor_${{SLURM_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}.csv" 2>/dev/null || echo "N/A")
    GPU_NAME=$(awk -F', ' 'NR==1 {{print $2}}' "${{LOGS_DIR}}/${{SAFE_NAME}}_gpu_monitor_${{SLURM_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}.csv" 2>/dev/null || echo "Unknown")

    echo "GPU: ${{GPU_NAME}}"
    echo "Peak VRAM usage: ${{PEAK_VRAM}} GB / ${{TOTAL_VRAM}} GB"
    echo "Average GPU utilization: ${{AVG_GPU_UTIL}}%"

    # Get SLURM job efficiency stats
    echo ""
    echo "CPU/Memory efficiency (from SLURM):"
    seff ${{SLURM_JOB_ID}} 2>/dev/null | grep -E "(CPU Efficiency|Memory Efficiency|Memory Utilized)" || echo "Unable to retrieve SLURM efficiency data"

    echo "=============================="

    # Clean up monitoring file
    rm -f "${{LOGS_DIR}}/${{SAFE_NAME}}_gpu_monitor_${{SLURM_JOB_ID}}_${{SLURM_ARRAY_TASK_ID}}.csv"
fi

echo ""
echo "Output files:"
ls -la "$OUTPUT_DIR/"

echo ""
echo "AlphaFold 3 prediction for $JSON_FILE finished successfully!"
"""

    # Write the SLURM script
    with open(slurm_script_path, 'w') as f:
        f.write(slurm_script_content)

    print(f"Created SLURM script: {slurm_script_path}")
    print()

    # Submit the job
    print("Submitting array job...")
    try:
        # Change to the input directory before submitting
        result = subprocess.run(
            ["sbatch", str(slurm_script_path)],
            cwd=input_dir,
            capture_output=True,
            text=True,
            check=True
        )

        print(f"Job submitted successfully!")
        print(f"SLURM output: {result.stdout.strip()}")

        # Extract job ID from output if possible
        if "Submitted batch job" in result.stdout:
            job_id = result.stdout.split()[-1]
            print()
            print("Useful commands:")
            print(f"  Check job status: squeue -j {job_id}")
            print(f"  Check all array tasks: squeue -j {job_id} -t all")
            print(f"  Cancel job: scancel {job_id}")
            print(f"  Monitor logs: tail -f {logs_dir}/af3_{job_id}_*.txt")

    except subprocess.CalledProcessError as e:
        print(f"Error submitting job: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: sbatch command not found. Make sure SLURM is available.")
        sys.exit(1)


if __name__ == "__main__":
    main()