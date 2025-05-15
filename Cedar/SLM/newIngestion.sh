#!/bin/bash
#SBATCH --time=00:15:00
#SBATCH --account=def-ycoady
#SBATCH --gpus=p100:1            # Request one P100 GPU
#SBATCH --mem=15G                # Necessary but could probably be lower
#SBATCH --signal=B:SIGUSR1@120   # Signal at 120 seconds before termination

set -euo pipefail

# Expects a single pdf file 
INPUT=$1
# Output directory 
OUTDIR=$2

# Fallback for SLURM_TMPDIR if not running under sbatch/salloc
: "${SLURM_TMPDIR:=$(mktemp -d)}"

# Source and destination of your Apptainer image
SIF_SRC="AGrpcOllamaDef.sif"
SIF_DEST="$SLURM_TMPDIR/$(basename "$SIF_SRC")"

#checks
if [ -z "$INPUT" ] || [ -z "$OUTDIR" ]; then
    echo "Usage: $0 <pdf-path> <output-dir>"
    exit 1
fi

if [ ! -f "$INPUT" ]; then
    echo "ERROR: PDF not found: $INPUT"
    exit 1
fi

if [ ! -f "$SIF_SRC" ]; then
    echo "ERROR: Container image not found: $SIF_SRC"
    exit 1
fi


# Set up termination signal handling
function sig_handler_USR1() {
	echo "Received prophecy of impending termination"
    mkdir -p "$OUTDIR"
	touch "$OUTDIR/this_was_interrupted"
	
	exit 2
}
trap 'sig_handler_USR1' SIGUSR1

# Should be very fast becuase we've already installed everything 
# Profile perfromance impact of this versus node-local storage
# echo "Syncing uv dependencies"
# uv sync 

# echo "Moving input to node-local storage"
# cp $INPUT $SLURM_TMPDIR

echo "Moving apptainer to node local storage"
cp "$SIF_SRC" "$SIF_DEST" || { echo "ERROR: failed to copy SIF"; exit 1; }

echo "Starting apptainer"
module load apptainer
apptainer instance start \
	--nv \
	"$SLURM_TMPDIR/AGrpcOllamaDef.sif" ollama-phi4

# I'm assuming it's fine to leave these in the home storage
# TODO: the checkpoints should be written to network storage 
# Add a checkpoints directory option to the script 
echo "Running script"
mkdir -p $OUTDIR
apptainer exec --env PATH="/root/.local/bin:$PATH" instance://ollama-phi4 \
    uv run main.py --only 3 -o "$OUTDIR" "$INPUT"
# apptainer exec instance://ollama-phi4 uv run main.py --only 3 -o "$OUTDIR" "$INPUT" 
#apptainer exec instance://ollama-phi4 bash sky_command.sh

echo "Stopping apptainer"
apptainer instance stop ollama-phi4

echo "Done!"
exit 0