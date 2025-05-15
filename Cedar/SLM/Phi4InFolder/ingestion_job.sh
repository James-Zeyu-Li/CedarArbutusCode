#!/bin/bash
#SBATCH --time=00:15:00
#SBATCH --account=def-ycoady
#SBATCH --gpus=p100:1            # Request one P100 GPU
#SBATCH --mem=15G                # Necessary but could probably be lower
#SBATCH --signal=B:SIGUSR1@120   # Signal at 120 seconds before termination

# Expects a single pdf file 
INPUT=$1
# Output directory 
OUTDIR=$2

[[ -f "$INPUT" ]] || { echo "Input file not found: $INPUT"; exit 1; }


# Set up termination signal handling
function sig_handler_USR1() {
	echo "Received prophecy of impending termination"
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
cp newOllama.sif $SLURM_TMPDIR

echo "Starting apptainer"
# module load apptainer
# apptainer instance start \
# --nv \
# "$SLURM_TMPDIR/newOllama.sif" ollama-phi4
module load apptainer
apptainer instance run --nv \
  --env PATH="/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin" \
  --env PYTHONPATH="/app:/workspace" \
  --bind /scratch/zeyu167/grpc_server:/app \
  --bind /scratch/zeyu167/SLM/models:/opt/ollama-storage \
  --bind /scratch/zeyu167/SLM/logs:/var/log/ollama \
  --bind /scratch/zeyu167/SLM/host_config:/host_config \
  --bind /scratch/zeyu167/SLM:/workspace \
  "$SLURM_TMPDIR/newOllama.sif" ollama-phi4


echo "Waiting for instance to start..."
sleep 10

echo "Starting Ollama service in instance..."
apptainer exec instance://ollama-phi4 bash -c 'nohup ollama serve > /var/log/ollama/ollama.log 2>&1 &'

echo "Waiting for Ollama service to be ready..."
sleep 10

echo "Testing Ollama API from instance:"
apptainer exec instance://ollama-phi4 curl -s http://127.0.0.1:11434/api/tags

# 测试 phi4 模型：检查 /opt/ollama-storage/models 是否已有缓存
echo "Testing Ollama model call (phi4):"
if [ ! -d "/opt/ollama-storage/models" ] || [ -z "$(ls -A /opt/ollama-storage/models)" ]; then
  echo "No cached model found, pulling phi4..."
  apptainer exec instance://ollama-phi4 bash -c 'nohup ollama serve > /var/log/ollama/ollama.log 2>&1 &'
  sleep 10
  apptainer exec instance://ollama-phi4 ollama pull phi4:14b
else
  echo "phi4 already cached, skipping download."
fi

echo "Testing KGgen CLI (help message):"
# apptainer exec instance://ollama-phi4 python3 -c "import kg_gen; print('KGGen version:', getattr(kg_gen, '__version__', 'Not defined')); print('KGGen contents:', dir(kg_gen))"
apptainer exec instance://ollama-phi4 bash -c '
  echo "=== PATH ==="
  echo $PATH
  echo "=== PYTHONPATH ==="
  echo $PYTHONPATH
  echo "=== Python modules ==="
  python3 -c "import sys, kg_gen; print(sys.path); print(kg_gen.__file__)"
  source /app/.venv/bin/activate
  export PYTHONPATH="/app:/workspace"  
  cd /workspace && uv run main.py --only 3 -o "'"$OUTDIR"'" "'"$INPUT"'"
'


echo "Running KGGen to generate knowledge graph..."
# I'm assuming it's fine to leave these in the home storage
# TODO: the checkpoints should be written to network storage 
# Add a checkpoints directory option to the script 
mkdir -p "$OUTDIR"
# Add this before running main.py

# apptainer exec instance://ollama-phi4 python3 main.py --only 3 -o "$OUTDIR" "$INPUT"
apptainer exec \
  --env PATH="/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin" \
  --env PYTHONPATH="/usr/local/lib/python3.10/dist-packages:/app:/workspace" \
  --env LITELLM_LOG="DEBUG" \
  instance://ollama-phi4 bash -c "cd /workspace && python3 main.py --only 1 -o '$OUTDIR' '$INPUT' 2>&1 | tee $OUTDIR/debug_log.txt"

#apptainer exec instance://ollama-phi4 bash sky_command.sh

echo "Stopping apptainer"
apptainer instance stop ollama-phi4

echo "Done!"
exit 0