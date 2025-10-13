# HIVE Partition Guide

This guide explains how to use different partitions (queues) on the HIVE cluster for submitting jobs with varying priority levels and resource access.

## Overview

HIVE offers multiple partitions with different priority levels and time limits. Understanding which partition to use can help you optimize job throughput and resource utilization.

## Available Partitions

### Low Priority Partition (`low`)
- **Time Limit:** 3 days maximum
- **Priority:** Low (jobs can be preempted)
- **Requeue:** Recommended to use `--requeue` flag
- **Account:** Not required
- **Best For:**
  - Short to medium-length jobs
  - Jobs that can be safely restarted
  - Testing and development
  - Non-urgent production runs

### High Priority Partition (`high`)
- **Time Limit:** 30 days maximum
- **Priority:** High (jobs won't be preempted)
- **Account:** Requires `--account=jbsiegelgrp`
- **Best For:**
  - Long-running jobs (> 3 days)
  - Jobs that cannot be interrupted
  - Critical production runs

### Genome Center High Priority Partition (`high` with genomecentergrp)
- **Time Limit:** 30 days maximum
- **Priority:** High (jobs won't be preempted)
- **Account:** Requires `--account=genomecentergrp`
- **Access:** Shared genome center resources
- **Best For:**
  - Long-running jobs when group resources are busy
  - Accessing shared genome center compute resources

## Example Submission Scripts

### Low Priority Example

**File:** `example_scripts/partitions/low_cpus.sh`

```bash
#!/bin/bash
#SBATCH -J hello_test
#SBATCH -t 3000
#SBATCH -n 1
#SBATCH --mem 4GB
#SBATCH -p low
#SBATCH --requeue
#SBATCH --output=logs/hello_%A_%a.out
#SBATCH --error=logs/hello_%A_%a.err
```

**Key Features:**
- Uses `-p low` partition
- Includes `--requeue` flag so job can be automatically restarted if preempted
- No account required
- Maximum runtime: 3 days (4320 minutes)

### High Priority - Group Resources

**File:** `example_scripts/partitions/high_cpus.sh`

```bash
#!/bin/bash
#SBATCH -J hello_test
#SBATCH -t 3000
#SBATCH -n 1
#SBATCH --mem 4GB
#SBATCH -p high
#SBATCH --account=jbsiegelgrp
#SBATCH --output=logs/hello_%A_%a.out
#SBATCH --error=logs/hello_%A_%a.err
```

**Key Features:**
- Uses `-p high` partition
- Requires `--account=jbsiegelgrp`
- Jobs won't be preempted
- Maximum runtime: 30 days

### High Priority - Genome Center Shared Resources

**File:** `example_scripts/partitions/gbsf_cpus.sh`

```bash
#!/bin/bash
#SBATCH -J hello_test
#SBATCH -t 3000
#SBATCH -n 1
#SBATCH --mem 4GB
#SBATCH -p high
#SBATCH --account=genomecentergrp
#SBATCH --output=logs/hello_%A_%a.out
#SBATCH --error=logs/hello_%A_%a.err
```

**Key Features:**
- Uses `-p high` partition
- Requires `--account=genomecentergrp`
- Access to shared genome center compute resources
- Maximum runtime: 30 days

## Decision Guide

### When to Use Low Priority (`low`)

Use the low priority partition when:
1. Your job runs in less than 3 days
2. Your job can be safely restarted (checkpoint-able)
3. You want faster queue times
4. You're testing or debugging code
5. Resource availability is more important than guaranteed completion

**Pro tip:** Always include `--requeue` flag with low priority jobs so they automatically restart if preempted.

### When to Use High Priority - Group Resources (`high` + `jbsiegelgrp`)

Use high priority with group account when:
1. Your job needs more than 3 days to complete
2. Your job cannot be interrupted or is difficult to restart
3. You need guaranteed completion without preemption
4. You're running critical production workloads
5. The job involves long simulations or optimizations

### When to Use High Priority - Genome Center Resources (`high` + `genomecentergrp`)

Use high priority with genome center account when:
1. All the criteria for high priority apply (see above)
2. Group resources are heavily utilized
3. You need access to additional compute capacity
4. You want to leverage shared genome center infrastructure

## Best Practices

### 1. Use Appropriate Time Limits
```bash
# Bad - requesting max time when you only need 1 hour
#SBATCH -t 30-00:00:00

# Good - request what you actually need plus buffer
#SBATCH -t 02:00:00
```

### 2. Always Use Requeue with Low Priority
```bash
# Ensures your job restarts automatically if preempted
#SBATCH --requeue
```

### 3. Create Log Directories
```bash
# Before submitting, make sure log directories exist
mkdir -p logs
sbatch your_script.sh
```

### 4. Monitor Your Jobs
```bash
# Check job status
squeue -u $USER

# Check job details
scontrol show job <job_id>

# Check partition availability
sinfo
```

### 5. Test with Low Priority First
```bash
# Start with low priority for testing
sbatch low_cpus.sh

# Move to high priority for production
sbatch high_cpus.sh
```

## Common SBATCH Parameters Explained

| Parameter | Description | Example |
|-----------|-------------|---------|
| `-J` or `--job-name` | Name of the job | `#SBATCH -J my_analysis` |
| `-t` or `--time` | Maximum runtime (minutes or DD-HH:MM:SS) | `#SBATCH -t 3000` (50 hours) |
| `-n` or `--ntasks` | Number of tasks/cores | `#SBATCH -n 8` |
| `--mem` | Memory per node | `#SBATCH --mem 32GB` |
| `-p` or `--partition` | Partition/queue name | `#SBATCH -p high` |
| `--account` | Account to charge resources to | `#SBATCH --account=jbsiegelgrp` |
| `--requeue` | Allow job to be requeued if preempted | `#SBATCH --requeue` |
| `--output` | Standard output file | `#SBATCH --output=logs/job_%j.out` |
| `--error` | Standard error file | `#SBATCH --error=logs/job_%j.err` |

## Partition Comparison Table

| Feature | Low Priority | High Priority (Group) | High Priority (Genome Center) |
|---------|-------------|---------------------|----------------------------|
| Partition Flag | `-p low` | `-p high` | `-p high` |
| Account Required | No | `--account=jbsiegelgrp` | `--account=genomecentergrp` |
| Max Time | 3 days | 30 days | 30 days |
| Can Be Preempted | Yes | No | No |
| Requeue Recommended | Yes | No | No |
| Queue Time | Usually faster | Varies | Varies |
| Resource Pool | Shared | Group allocation | Genome center shared |

## Troubleshooting

### Job Keeps Getting Preempted
**Solution:** Switch to high priority partition or ensure you're using `--requeue` flag.

### "Invalid account" Error
**Problem:**
```
sbatch: error: Batch job submission failed: Invalid account or account/partition combination specified
```

**Solution:**
- For high priority: Add `--account=jbsiegelgrp` or `--account=genomecentergrp`
- For low priority: Remove account specification

### Job Exceeds Time Limit
**Problem:**
```
slurmstepd: error: *** JOB 12345 ON node123 CANCELLED AT 2024-10-10T12:00:00 DUE TO TIME LIMIT ***
```

**Solution:**
- If job needs > 3 days: Switch to high priority partition
- If job needs < 3 days: Optimize code or break into smaller jobs
- Always add buffer time to your estimates

### Queue is Full
**Solution:**
- Try alternate partition (genomecentergrp if available)
- Check `sinfo` to see partition availability
- Consider breaking job into smaller chunks
- Use low priority for faster queue times

## Additional Resources

- [SLURM Documentation](https://slurm.schedmd.com/)
- [HIVE Cluster Documentation](https://hpc.ucdavis.edu/)
- Contact HPC support: hpc-help@ucdavis.edu

## Related Documentation

- [Main README](../README.md) - Overview of HIVE migration
- [Bash Profile Migration](bash_profile_migration.md) - Setting up your environment
- [Example Scripts](../example_scripts/) - Additional submission script examples
