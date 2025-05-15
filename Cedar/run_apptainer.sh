#!/bin/bash
#SBATCH --job-name=apptainer_job  
#SBATCH --account=def-ycoady
#SBATCH --time=01:00:00           
#SBATCH --gpus=p100:1            # Request one P100 GPU
#SBATCH --mem=15G                # Necessary but could probably be lower
#SBATCH --signal=B:SIGUSR1@120   # Signal at 120 seconds before termination
#SBATCH --cpus-per-task=1         
#SBATCH --output=/scratch/zeyu167/logs/apptainer_output.log 

# run apptainer through ceder
module load apptainer

# turn on apptainer
# prepare for activation of Apptainer, Grpc, Ollama, Phi4, KGGen
apptainer instance run \
  --bind /scratch/zeyu167/grpc_server:/app \
  --bind /scratch/zeyu167/SLM/models:/opt/ollama-storage \
  --bind /scratch/zeyu167/SLM/logs:/var/log/ollama \
  grpcApptainer.sif grpcApptainer

if [ $? -eq 0 ]; then
    echo "Apptainer started with name grpcApptainer in the background"
else
    echo "Error: Apptainer instance launch failed."
    exit 1
fi

# wait for the GRPC to be activatedc
echo "Waiting 5 for apptainer to start"
sleep 5

#activate Grpc instance
cd /scratch/zeyu167/grpc_server

apptainer exec instance://grpcApptainer python3 /app/grpc_serv.py >> /scratch/zeyu167/logs/grpc_server.log 2>&1 &

if [ $? -eq 0 ]; then
    echo "gRPC service command issued successfully."
else
    echo "Error: Failed to execute gRPC service inside Apptainer."
    exit 1
fi


#change folder
# reverse tunnelling 
echo "Establishing Reverse SSH Tunnel to Arbutus"
ssh -i ~/.ssh/ceder_key -N -R 5052:localhost:5050 ubuntu@206.12.92.63 &
tunnel_pid=$!

trap "echo 'Terminating SSH tunnel...'; kill $tunnel_pid" EXIT

sleep 5
if ps -p $tunnel_pid > /dev/null; then
    echo "Reverse SSH Tunnel established successfully."
else
    echo "Error: Failed to establish reverse SSH tunnel."
    exit 1
fi

#Establish the tunnelling between Arbutus and Cedar
echo "Running testTunnelling.py"
python3 /scratch/zeyu167/grpc_server/testTunnelling.py
if [ $? -eq 0 ]; then
    echo "Tunnel health check passed."
else
    echo "Tunnel health check failed."
    kill $tunnel_pid
    exit 1
fi

while true; do sleep 10; done