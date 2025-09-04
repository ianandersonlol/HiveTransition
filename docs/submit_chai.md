[View Script: submit_chai.sh](../example_scripts/submit_chai.sh)
[View Script: submit_chai_with_msa.sh](../example_scripts/submit_chai_with_msa.sh)

# Submitting ChAI Jobs

The `submit_chai.sh` and `submit_chai_with_msa.sh` scripts are used to submit ChAI jobs to a SLURM cluster. These scripts handle the setup of the environment and the execution of the ChAI python scripts.

## Usage

To submit a job, use the `sbatch` command followed by the script and the required arguments:

```bash
sbatch <script_name>.sh <input.fasta> <output_dir>
```

- `<script_name>.sh`: Either `submit_chai.sh` or `submit_chai_with_msa.sh`.
- `<input.fasta>`: Path to the input FASTA file.
- `<output_dir>`: Path to the directory where the output files will be saved.

### `submit_chai.sh`

This script is used to run the `run_chai.py` script, which performs a single sequence prediction.

### `submit_chai_with_msa.sh`

This script is used to run the `chai_with_msa.py` script, which performs a prediction using a multiple sequence alignment.

## SLURM Directives

The scripts include the following SBATCH directives:

- `--job-name`: Sets the job name.
- `--partition`: Specifies the partition (queue) to use.
- `--account`: Specifies the account to use.
- `--ntasks`: Number of tasks to run.
- `--cpus-per-task`: Number of CPUs per task.
- `--mem`: Memory per node.
- `--gres`: Generic consumable resources (in this case, 1 GPU).
- `--time`: Wall clock time limit.
- `--output`: Path to the output log file.
- `--error`: Path to the error log file.

These directives can be modified to suit the needs of your specific cluster and job.
