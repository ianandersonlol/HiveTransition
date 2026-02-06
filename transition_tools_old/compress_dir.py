#!/bin/bash
#SBATCH -J compress_dir
#SBATCH -t 72:00:00
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH --partition=high
#SBATCH --account=jbisegelgrp
#SBATCH --mail-type=FAIL,END
#SBATCH --output=./out_files/compress_files-%j.out

set -euo pipefail

DIR=$1
ARCHIVE="${DIR}.tar.xz"

echo "Creating archive: $ARCHIVE"
tar -cJf "$ARCHIVE" "$DIR"

echo "Verifying archive integrity..."
if tar -tf "$ARCHIVE" > /dev/null 2>&1; then
    echo "Archive is valid."
    echo "Removing original directory: $DIR"
    rm -r "$DIR"
    echo "Done!"
else
    echo "Archive verification failed. Original directory NOT deleted."
    exit 1
fi