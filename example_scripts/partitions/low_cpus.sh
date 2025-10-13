#!/bin/bash 
#SBATCH -J hello_test
#SBATCH -t 3000
#SBATCH -n 1
#SBATCH --mem 4GB
#SBATCH -p low
#SBATCH --requeue  
#SBATCH --output=logs/hello_%A_%a.out
#SBATCH --error=logs/hello_%A_%a.err
