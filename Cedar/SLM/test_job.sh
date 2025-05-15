#!/bin/bash
#SBATCH --time=00:1:00
#SBATCH --account=def-ycoady

export PATH="/root/.local/bin:$PATH"


echo "Hello"
ls > /scratch/zeyu167/SLM/test_data/test_output_ls
echo "world"
uv sync > /scratch/zeyu167/SLM/test_data/test_output_uv
echo "!"

exit 0
