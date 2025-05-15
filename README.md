# CedarArbutusCode
- [Part 1: tunnelling](#part-1-apptainer-arbutus-and-cedar-automation-connection-and-tunnelling-instruction)
- [Part 2: KgGen update](#2nd-part---arbutus-initiated-knowledge-graph-generation--kggen-ollama-phi-4)

*Some of the naming in the code is different from the description and instruction below, the below instruction does a better in naming.*

---
## Part 1: Apptainer, Arbutus and Cedar Automation Connection and Tunnelling Instruction

### General Idea
- The Cedar/ Slurm Node with Apptainer is going to run a small embeddings Language Model which will be helping the Arbutus side to generate Knowledge Graph.
- The Communication/Connection must be established between Arbutus and Cedar/ Slurm that runs Apptainer to achieve this goal.
- This Instruction helps on the establishment of the connection tunnelling and Connection.
### Needs to be installed 
1. Flask, gRPC and Apptainer needs to be installed and setup on Arbutus
2. gRPC and Apptainer needs to be Installed on Cedar
3. Detail installation instruction will be mentioned in the Steps section
	- Grpc:
		- Enables two-way communication.
		- https://grpc.io/docs/languages/python/quickstart/
	- Flask: 
		- Provides API access 
		- https://flask.palletsprojects.com/en/stable/installation/
	- Nginx (For this tutorial): 
		- Acts as a reverse proxy.
		- https://flask.palletsprojects.com/en/stable/deploying/nginx/

### Restrictions
1. Cedar and Slurm limits the runnling directly from Arbutus to Cedar, since tunnelling to Slurm Node requires 2-factor in my tests
	- Solution use reverse tunnelling to initiate the connection from Slurm.
2. When try to create a bridge from inside Apptainer with Slurm, showing require Root
	- Skip the bridge connection initiate from Slurm to Apptainer, but communicate from Apptainer out.
	- https://apptainer.org/docs/user/1.0/networking.html
3. Cedar head node should be use for Job and Apptainer Activation instead of doing the actual job, apply for a Slurm node instead.
	1. Slurm MUST be request in `/scratch/username` folder
	2. To Run Slurm job in front, 2 hours, 1 CPU
		- `salloc --time=2:0:0 --mem-per-cpu=2G --ntasks=1`
4. Do not create a Slurm node which run for too long. Details about Slurm please see following link
	- https://share.descript.com/view/FZwguxe9djH	
	- https://docs.alliancecan.ca/wiki/Running_jobs
	- https://docs.alliancecan.ca/wiki/Multifactor_authentication
5. Automatic connection won't be allowed for creating long term connection, only job submissions. Will be mentioned below when relevant.
	- https://docs.alliancecan.ca/wiki/Automation_in_the_context_of_multifactor_authentication#Increased_security_measures

### Step Overview
1. Install `Apptainer` on Arbutus 
	1. create the `Definition File`, generate the Container and send to Cedar
	- If Apptainer Container is Created in a Server with Root Access, your Container could also have root access.
2. A Bash Script needs to be created on Cedar to 
	1. Request for a Slurm Node
	2. Start the Apptiner
	3. Activate gRPC and make sure the Apptiner Keep running
3. Reverse Tunelling Connection
	1. Through reverse tunnelling, Arbutus could request Cedar Apptainer to do job processing.
4. Individual tests should be done on separate parts instead of set everything up and test all together.
## Additional Useful Links
- Compute Canada Apptainer Guide: 
	- https://docs.alliancecan.ca/wiki/Apptainer#If_you_are_currently_using_Singularity
- Apptainer quick start Guide:
	- https://apptainer.org/docs/user/main/quick_start.html#installation
- Tunnelling:
	- https://docs.alliancecan.ca/wiki/SSH_tunnelling
- gRPC:
	- https://grpc.io/docs/languages/python/basics/
	- https://www.velotio.com/engineering-blog/grpc-implementation-using-python

## Install Apptainer on Arbutus
- https://github.com/apptainer/apptainer/blob/main/INSTALL.md
- This page provides a full and great instruction to be followed.

## Steps for create Apptainer Hello World Container
### 1. Create Apptainer Container on Arbutus
#### 1. Create a Definition File
- It's normally a good habit to create definition file first and use the dinition file for creating the apptainer it self. 
- `vim helloworld_container.def`

```def
Bootstrap: docker 
From: ubuntu:20.04

%labels //could add your name and description here

%post
    apt-get update && apt-get install -y python3 python3-pip
    pip3 install grpcio grpcio-tools

%environment
    export PYTHONUNBUFFERED=1
    export PATH="/usr/local/bin:$PATH"

```
Explain of the template code:
- `Bootstrap: docker`  
    Uses Docker Hub as the source for the base image.
- F`rom: ubuntu:20.04  `
    Specifies Ubuntu 20.04 as the base image.
	`%post`
	- `apt update && apt install -y curl python3`: Update package lists and installs curl and Python.
	- `pip3 install grpcio grpcio-tools`: Install gRPC related tool for later operation
	- `apt clean` and `rm -rf /var/lib/apt/lists/*`: Clean up package caches to reduce image size.
	
	`%environment
	    `export PYTHONUNBUFFERED=1` : provide realtime log output instead of buffer then output
	    `export PATH="/usr/local/bin:$PATH"` : faster find the bin folder
#### 2.Build the container according to definition
How to use `build` Command : https://apptainer.org/docs/user/1.0/build_a_container.html

- Build a container instance with name helloworld_container:
```
apptainer build helloworld_container.sif helloworld_container.def
```
#### 3. Run the Apptainer to test
`apptainer run helloworld_container.sif`

### 2. Deploy container to Cedar
#### 1. Send .sif file to Cedar
1. Use scp to transfer the file 
	- `scp container_name.sif username@cedar.computecanada.ca:/scratch/username/`
	
	- Note: The .sif file should be send to the `scratch` folder, route is normally `/scratch/username/`
		- Or try `echo $SCRATCH`
	- Note 2: Before sending could try logging into Cedar from Arbutus through ssh, if ssh works scp should work smoothly 
		- ``ssh username@cedar.computecanada.ca`` 
		- Compute Canada password and 2 factor required
	
- After scp command success, could login to test run the .sif file.
- `apptainer run /scratch/username/container_name.sif`

### 3. Create Key pair in Arbutus for Cedar
- This step is essential for the automation to work
- Just like how key pairs works on local machine they work on Arbutus and Cedar. 

1. Create Key pairs `ssh-keygen -t rsa -b 4096 -f ~/.ssh/my_custom_key‘
	1. This key pair is generated using the RSA algorithm, but the protocol can be changed to a preferred alternative, such Ed25519.

2. Please refer to this page's "Available only through constrained SSH keys" and following sections to create a properly constrained Key : https://docs.alliancecan.ca/wiki/Automation_in_the_context_of_multifactor_authentication#Increased_security_measures
	- cat ~/.ssh/keyName.pub 
	- Since my automation initiates from Arbutus, use Arbutus's IP address for `restrict,from="xxx.xx.xxx.*"`
	- There are some defined `command =`, select according to need (use allowed_commands to allow all)
	- I also updated the key chain file, add the restrictions in.

3. Upload the Key chain to page https://ccdb.alliancecan.ca/ssh_authorized_keys
	- Or after login -> My Account -> Manager SSH Keys
	- Notification email will be send one SSH key added or removed

4. A email needs to be sent to tech support team if automation requests are needed to be performed. Details in the above page provided in step 2 *'Available only by request'* section.

### **Note**: Remote-SSH in **VSCode** will be helpful
- Extensions tab, search "Remote-SSH" and install
- click the 2 arrow head button on the bottom left corner of VSCode
	- connect to host
	- + add new SSH Host
	- Input the SSH command and select the 1st option.
	- After this step you can use VSCode make updates to the code in Arbutus and Cedar.

### 4. Creation of gRPC and gRPC Client

#### Cedar gRPC
**1: Install grpcio and grpcio-tools** - (this step is changeable)
- Cedar does not allow to install gRPC directly, could install through myenv
```
python3 -m venv myenv // create venv python environment
source /scratch/username/grpc_server/myenv/bin/activate
pip install grpcio grpcio-tools
```

- Cedar does not allow to do system level gRPC start when server starts, for testing purpose could through front end activation.
- Could also use nohup command to do a back end run which won't restart if closed
	- `nohup python3 grpc_server.py > grpc_server.log 2>&1 &`
	- The log will be saved to `grpc_server.log` for status checking.
- The command could be used to shut backgroud gRPC
	- `pkill -f grpc_server.py`
- After all the setup the gRPC server will be activated inside container which means it's not a must to install on Cedar.

**2: Create the protofile, gRPC will generate related code according to the Proto file.**
- https://protobuf.dev/programming-guides/proto3/
- This is the way I generated, could be altered accordingly
- `vim grpc_task.proto`

```
syntax = "proto3";

package grpc_task;

service TaskService {
    rpc SubmitTask(TaskRequest) returns (stream TaskResponse);
}

message TaskRequest {
    string task_name = 1;
    string input_data = 2;
}

message TaskResponse {
    string job_id = 1;
    string status = 2;
    string output_url = 3;
}
```

- **`package grpc_task;`**  
    Defines the package name (`grpc_task`) for the in the generated code. 
- **Service Definition: `TaskService`**  
    Declares a gRPC service called `TaskService` with one RPC method:
    - **`SubmitTask`**:
        - Request: Accepts a `TaskRequest` message.
        - Response: Returns a `TaskResponse` stream. 
- **Message Definitions:**
    - `TaskRequest`  : What fields will the request be sending in
    - `TaskResponse` : What fields will the response be sent out.

**3: Run the following command to auto generate two files**
- protocol message classes
- gRPC client/server class
- I am using my name  `grpc_task.proto`

`python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. grpc_task.proto`
- -I. : current directory is included for proto imports
-  --python_out=. 
	- where to output the generated protocol messages classes
-  --grpc_python_out=.
	- where to output the generated code

**4: gRPC Client construction**
- This is also a sample construction with a hardcoded response message for test only.
-  My version of the grpc uses asynchronous gRPC server.
```python
import grpc
import asyncio
import grpc_task_pb2
import grpc_task_pb2_grpc
import subprocess
import os
import time
from concurrent import futures
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="/scratch/username/logs/grpc_serv_run.log", #change to your own directory to save logs
    filemode="a", 
    format="%(asctime)s %(levelname)s: %(message)s"
)

class TaskService(grpc_task_pb2_grpc.TaskServiceServicer):
    async def SubmitTask(self, request, context):
        logging.info((f"Slurm Grpc Processing")
        logging.info(f"Received task request: {request.task_name}, Data: {request.input_data}")

        input_file = f"/scratch/username/input_data/{request.input_data}" # assume input will be a file
         
         # check if the file exists, if not create a dummy folder and file with a message
        if not os.path.exists(input_file):
            logging.warning(f"Input file '{input_file}' not found, creating a dummy file for testing.")
            os.makedirs(os.path.dirname(input_file), exist_ok=True)
            with open(input_file, 'w') as f:
                f.write("This is simulated input data for testing container mapping.\n")
        
        # get the job ID, uses timestep as jobid
        job_id = f"job_{int(time.time())}"
		logging.info(f"Task submitted to Slurm: job_id={job_id}")
        yield grpc_task_pb2.TaskResponse(job_id=job_id, status="Task submitted to Slurm", output_url="")

		# check the job status for every 5 seconds, resuturn a state, sleep and repeat until 3 times.
        for i in range(3):
            status = f"Processing step {i+1}/3"
			logging.info(f"{job_id} - {status}")
            yield grpc_task_pb2.TaskResponse(job_id=job_id, status=status, output_url="")
            await asyncio.sleep(5)
        
        # output the the destinated folder and respond
        output_path = f"/scratch/username/results/{job_id}.zip"
        if os.path.exists(output_path):
			logging.info(f"Task completed successfully: {job_id}, output_url={output_path}")
            yield grpc_task_pb2.TaskResponse(job_id=job_id, status="Task completed", output_url=f"file://{output_path}")
        else:
			logging.warning(f"Task completed but no output file found: {job_id}")
            yield grpc_task_pb2.TaskResponse(job_id=job_id, status="Task completed, but no output found", output_url="")

# The grpc will be occupying port 5050, service is through asynchronized.
async def serve():
    server = grpc.aio.server()
    grpc_task_pb2_grpc.add_TaskServiceServicer_to_server(TaskService(), server)
    server.add_insecure_port("0.0.0.0:5050")
    
    logging.info("Starting gRPC Server on port 5050...")
    await server.start()  # make sure server server starts using await
    logging.info("gRPC Server started.")
    await server.wait_for_termination()  # keep server active

if __name__ == "__main__":
   asyncio.run(serve())
```

**5: Could use test_grpc.py to test if the gRPC is working properly**
```python
import asyncio
import grpc
import grpc_task_pb2
import grpc_task_pb2_grpc

async def run_test():
    async with grpc.aio.insecure_channel('127.0.0.1:5050') as channel:
        stub = grpc_task_pb2_grpc.TaskServiceStub(channel)
        
        # fake message
        request = grpc_task_pb2.TaskRequest(task_name="TestTask", input_data="test_input.txt")
        response_iterator = stub.SubmitTask(iter([request]))
        async for response in response_iterator:
            print("Received response:")
            print(f"Job ID: {response.job_id}")
            print(f"Status: {response.status}")
            print(f"Output URL: {response.output_url}")

if __name__ == '__main__':
    asyncio.run(run_test())

```
#### Arbutus gRPC
- The gRPC installation steps is the same as Cedar's setup.
- Arbutus only needs to install gRPC module, `grpcio` and `grpcio-tools`
	- could use the same `grpc_task.proto` to generate
	- The next step Flask will be using gRPC on port 5052 (can be change to any other ports)
- Since we will use reverse tunnelling from Cedar to Arbutus, the requests sent from Arbutus will be handled by the gRPC server running on Cedar/Slurm, not by a gRPC client.

- gRPC can be started in the backgroud once server starts
	- change the route accordingly
	- `sudo vim /etc/systemd/system/grpc_service.service`
```
[Unit]
Description=Arbutus GRPC Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/myapp
ExecStart=/home/ubuntu/myenv/bin/python3 /home/ubuntu/myapp/grpc_serv.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

- **Commands to initiate and check status**
	sudo systemctl daemon-reload
	sudo systemctl start grpc_service
	sudo systemctl status grpc_service
	sudo systemctl enable grpc_service
- Stop the service
	sudo systemctl stop grpc_service

### 5. Creation of Flask on Arbutus
#### **Quick installation steps**
- Possible that Ubuntu don't allow pip install in python environment, use venv environment instead
	- if gRPC on Arbutus created a venv environment Flask could use the same enviroment.
	`python3 -m venv myenv`
- Activate Venv Environment: 
	`source myenv/bin/activate`
- Install Flask
	`pip install flask`

- Creation of the Flask Server file, change to any directory you prefere
	`vim /home/ubuntu/myenv/flask_server.py`

####  **Below is a prototype version of Flask, should be changed according to needs.**
- According to my design, 
	- The port Arbutus Opens to public will be port **5050**, FLask will monitor 5050
	- The port that will connect to Cedar through reverse tunnelling will be 5052 
	- The Flask is currently asynchronous for testing, should be updated accordingly.
```python
import grpc
import grpc_task_pb2
import grpc_task_pb2_grpc
import asyncio
from flask import Flask, request, jsonify

app = Flask(__name__)

# Cedar IP and port 5052
GRPC_SERVER_ADDRESS = "127.0.0.1:5052"

async def submit_task(context_data):
    """
    use grpc to submit task to Cedar and monitor the status
    """
    async with grpc.aio.insecure_channel(GRPC_SERVER_ADDRESS) as channel:
        stub = grpc_task_pb2_grpc.TaskServiceStub(channel)

        request_proto = grpc_task_pb2.TaskRequest(
            task_name="test_task", 
            input_data=str(context_data))

        response_iterator = stub.SubmitTask(iter([request_proto]))
        
        results = []
        async for response in response_iterator:
            print(f"Received from Cedar: {response.status}")
            results.append({
                "job_id": response.job_id,
                "status": response.status,
                "output_url": response.output_url
            })
        return results

def get_context_for_query(query):
    # A simple implementation for testing purposes.
    return {"query": query, "embedding": "simulate_vector"}

@app.route('/api/start', methods=['POST'])
def start_task():
    try:
        # get query from user input
        query = request.json.get("query")
        # get simulated data
        context_data = get_context_for_query(query)
        # run gRPC and submit task
        results = asyncio.run(submit_task(context_data))
        # summerize and submit to LLM API
        return jsonify({"message": "Task processed", "results": results})
    except Exception as e:
        import traceback
        print(f"Error in start_task: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5050)

```
#### **Use the following script to make sure Flask runs in the background when the server starts.**
- Note: This action is only required if you have the Root of the machine.
- sudo vim /etc/systemd/system/flask_api.service
	
```
[Unit]
Description=Flask API Service
After=network.target

[Service]
User=ubuntu # username
WorkingDirectory=/home/ubuntu/myenv

# address for file update accordingly
ExecStart=/home/ubuntu/myenv/bin/python /home/ubuntu/myenv/flask_server.py 

Restart=always

[Install]
WantedBy=multi-user.target
```

- Commands to Reload System and Start the API
	sudo systemctl daemon-reload
	sudo systemctl start flask_api
	sudo systemctl enable flask_api
- Use status to check if success
	sudo systemctl status flask_api
#### additional Flask useful commands 
- **Commands to check Flask Status**
	sudo ss -tulnp | grep 5050  //check if port if monitored
	ps aux | grep flask    //check the status of flask
	
- **Start Flask in the for ground**
	python3 /home/ubuntu/myenv/flask_server.py

### 6. Create the Bash Script on Cedar
- Needs to be placed in /scratch folder
- Create the file  `vim /scratch/username/example.sh
	- I have named the file `run_apptainer.sh`

- **What the bash script will be doing** 
	- The Apptainer will be started
		- --bind command will allow apptainer to work with the folder included in the command.
	- Start the gRPC server inside the Apptainer container on the back groud
	- Reverse Tunnel will be connected from Arbutus Port 5052 to Slurm Port 5050

- **For testing, I do recommand apply for a Slurm node and run the script inside Slurm through `bash filename.sh`**
	- This way of running won't repeatedly apply for new Slurm nodes
	- Repeatedly apply for Slurm is not a good practice, harm the node distribution priority
	- Could login to the same Slurm node through `ssh slurmNodeName`
		- Slurm node name could be find by doing `sq` once node stated
		- node name: cdr1234

```bash
#!/bin/bash
#SBATCH --job-name=apptainer_job  
#SBATCH --time=00:30:00           
#SBATCH --mem=1G                  
#SBATCH --cpus-per-task=1         
#SBATCH --output=/scratch/username/logs/apptainer_output.log 

# run apptainer through Cedar
module load apptainer

# turn on apptainer, the apptiner will be run with shell name grpc_instance
echo "Starting Apptainer instance..."
apptainer instance run \
    --bind /scratch/username/grpc_server:/app \
    /scratch/username/test.sif grpc_instance

# wait for the GRPC to be activatedc
echo "Waiting 5 seconds for Apptainer to stabilize..."
sleep 5

#activate Grpc instance
apptainer exec instance://grpc_instance python3 /app/grpc_serv.py >> /scratch/username/logs/grpc_server.log 2>&1 &

# reverse tunnelling 
echo "Establishing Reverse SSH Tunnel to Arbutus..."
ssh -i ~/.ssh/Cedar_key -N -R 5052:localhost:5050 ubuntu@206.12.92.63 &
tunnel_pid=$!

trap "echo 'Terminating SSH tunnel...'; kill $tunnel_pid" EXIT

sleep 5

echo "Running testTunnelling.py..."
python3 /scratch/username/grpc_server/testTunnelling.py
if [ $? -eq 0 ]; then
    echo "Tunnel health check passed."
else
    echo "Tunnel health check failed."
    kill $tunnel_pid
    exit 1
fi

#Keep live
while true; do sleep 10; done
```

- **Can Create Tunnelling directly from Slurm to Arbutus and check status**
	- ssh -i ~/.ssh/Cedar_key -N -R 5052:localhost:5050 ubuntu@206.12.92.63 &
		- if with & in the end, it runs in the backgroud, needs to be terminated mannually.
		- script uses a trap to kill the tunnel. 
	- Needs to make sure Flask is active on Arbutus 
	- Make sure gRPC is running on Slurm
	- Could also check Arbutus connection status by
		- `sudo ss -tulpn | grep 5052`

- **Check the Apptainer Status**
	- check the running instance 
		`apptainer instance list`
	- Get into Apptainer
		`apptainer shell instance://grpc_instance`
	- Terminate the Instance
		`apptainer instance stop grpc_instance`

- **Test if inside Apptainer could communicate with Slurm**
	- I named the file testApptainerGrpc.py
```python
import socket
import sys

def check_grpc(host='127.0.0.1', port=5050):
    s = socket.socket()
    try:
        s.settimeout(5)
        s.connect((host, port))
        print(f"Connected to {host}:{port} successfully.")
        return True
    except Exception as e:
        print(f"Failed to connect to {host}:{port}. Exception: {e}")
        return False
    finally:
        s.close()

if __name__ == '__main__':
    if not check_grpc():
        sys.exit(1)

```

- **Test Tunnelling**
	-  Make sure Arbutus Flask is running 
	-  Make sure Apptainer gRPC in running
```python
import socket
import sys

def check_grpc(host='127.0.0.1', port=5052):
    s = socket.socket()
    try:
        s.settimeout(5)
        s.connect((host, port))
        print(f"Connected to {host}:{port} successfully.")
        return True
    except Exception as e:
        print(f"Failed to connect to {host}:{port}. Exception: {e}")
        return False
    finally:
        s.close()

if __name__ == '__main__':
    if not check_grpc():
        sys.exit(1)
```
#### Test the Bash file
- Could run this command to test if it works accordingly 
	1. `sbatch /scratch/username/example.sh`
		1. use sbatch to run will request for a new Slrum node
	2. check job status: `sq`
	3. output log result: `cat /scratch/username/apptainer_output.log` 

### 7. Creation of Paramiko on Arbutus
1. Install Paramiko
	`pip3 install paramiko`

- The objective of Paramiko file is to: 
	- Act as the entry from Arbutus to automatically envoke Slurm and Apptainer on Cedar.
		- The Key we previously created will be used to run the bash file on Cedar through 
			- username.robot.cedar.alliancecan.ca
	- The file is named as apptainer_connect.py
	- After run the apptainer_connect.py 
		- run `sq` on Cedar to check the job status

- **Needs to be improved on**
	- After submitting the job, the current script lost track of the requested Slurm. Job needs to be verified manually. 
```python
import paramiko
import time
import subprocess

# SSH to run the slurm command
KEY_PATH = "/home/ubuntu/.ssh/cedar_automation_key"
USER = "username"
HOST = "robot.cedar.alliancecan.ca" #the slurm submission ssh host
TUNNEL_HOST = "cedar.alliancecan.ca"

LOG_PATH = "/scratch/username/logs/apptainer_output.log"



def ssh_connect(host, user, key_path):
    """do ssh connection"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key_file(key_path)
    ssh.connect(hostname=host, username=user, pkey=key)
    return ssh



def submit_slurm_job(ssh):
    """ sumbit a slurm job"""
    cmd = "sbatch --chdir=/scratch/username /scratch/username/run_apptainer.sh"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    sbatch_output = stdout.read().decode().strip()
    error_output = stderr.read().decode().strip()
    
    if error_output:
        print("SLURM submission error:", error_output)
    else:
        print("SLURM submitted successfully:", sbatch_output)

    return sbatch_output

def main():

    # first SSH 
    ssh = ssh_connect(HOST, USER, KEY_PATH)
    submit_slurm_job(ssh)

if __name__ == "__main__":
    main()
```

### 8. Connection Check Commands and Tunnelling Check Commands
- **The activation, Slurm distribution, Apptainer and Grpc Creation will take a while to activate**

1.  **Check if Flask Working properly listening to port 5050**
	- Arbutus Run
		`sudo ss -tulpn | grep 5050` 
	- for flask
		`sudo ss -tulpn | grep 5052`
		- check tunnelling connection after the reverse tunnelling is working
	- Arbutus run the following script `test_grpc_communication` and see if gRPC response is received.

2. **Slurm Check, ssh insiede the node number** 
	1. Find Slurm Node name/ check Slurm status (pending, running and timer)
		- `sq`
	2. Check Grpc activated user python3 
		- `ss -tulpn | grep 5050` 
	3. Go inside Apptainer to run script check if grpc and connection is fine
		- `module load apptainer` 
		- `apptainer instance list` # make sure apptainer running
		- `apptainer shell instance://grpc_instance` # go inside Apptainer
		- `apptainer instance stop grpc_instance` # command to stop the Apptainer
		- Could write a python file or use `testApptainerGrpc.py` to test connection
			- Please put the python file under the folder that's under the command --bind
			-     **--bind /scratch/username/grpc_server**:/app /scratch/username/test.sif grpc_instance
		- Should connect successful, connect to 127.0.0.1 through port number 5050
			- `python3 testTunnelling.py`

3. **After Confirm Slurm is activated, gRPC is running, Reverse Tunnelling is successful**
	- The following python script could be used to test if Arbutus can access gRPC to process the request. `test_grpc_communication.py`

```python
import asyncio
import grpc
import grpc_task_pb2
import grpc_task_pb2_grpc

async def test_grpc_call():
    async with grpc.aio.insecure_channel("127.0.0.1:5052") as channel:
        stub = grpc_task_pb2_grpc.TaskServiceStub(channel)
        request = grpc_task_pb2.TaskRequest(task_name="health_check", input_data="test")

        async for response in stub.SubmitTask(iter([request])):
            print(f"Received: job_id={response.job_id}, status={response.status}, output_url={response.output_url}")

if __name__ == "__main__":
    asyncio.run(test_grpc_call())

```



----

## 2nd Part - Arbutus initiated Knowledge Graph Generation- KGGen, Ollama, Phi-4

-  The **KGGen** and **Phi4** processing logic is from another team member Kieran's github repo. 
- Repository from Kieran: `https://github.com/Saskapult/graph-ingestion-playground/tree/main`

### Embedding & KGGen Service
- Arbutus sends the File via gRPC to the Cedar-hosted KGGen endpoint.
- Inside the Apptainer instance, a Python service loads the Phi-4 model via Ollama and runs a KG-generation pipeline.


### Arbutus gRPC Client update
- **Prerequisites**:
	- Requires active tunnel connection to Cedar server (`cedar:5050`)
	- Local directories must exist:
	    - `~/myenv/results/` (folder name could be changed accordingly)
	    - `~/myenv/logs/` 

- **PDF Processing Workflow**
1. **Task Submission**:
    - Accepts PDF via:
        - Direct binary upload (`file_content`) 
	        - *This is currently a fixed address, should be updated accordingly*
        - Filesystem path (`input_data`)
		
    - Constructs `TaskRequest` with:
	```
	grpc_task_pb2.TaskRequest(
	    task_name="process_pdf",
	    file_content=pdf_bytes,  # or input_data="/path/to/file.pdf"
	    file_name=os.path.basename(path)
	```

2. **Asynchronous Processing**:
    - Three status phase:
        - `Step 1/3: Preparing PDF` 
        - `Step 2/3: Processing in SLURM` 
        - `Step 3/3: Processing completed`
    - Through a busy waiting polling to get status of current job:
        - Starts with 10s intervals, maximum 20 minutes.
    
3. **Result Retrieval**:
    - The current implementation assumes the file system is shared, this should be updated to for example a streaming back from gRPC server to receive the result.

### Cedar gRPC Server for PDF Ingestion
- **Prerequisites:**
	- The tunnel needs to be connected between Cedar and Arbutus before hand.
	- The Apptainer container need to be built using the KGGen Playground's definition file.

1. **Startup & Configuration**
    - Listens on port **5050** via `server.add_insecure_port("[::]:5050")`through gRPC async.
    - The current design ensures the three base directories exist 
	    - `/scratch/username/inputs`
	    - `/scratch/username/results`
	    - `/scratch/username/logs`
    - Writes logs to both stdout and `grpc_server.log` under `logs` folder.

2. **`SubmitTask` RPC**, **PDF Processing**
    - **`process_pdf`**
        1. Pulls the first `TaskRequest` from the stream, assigns a unique `job_id = "job_<timestamp>"`.
        2. Saves uploaded PDF bytes to `<inputs>/<job_id>_<filename>`.
        3. Yields a `"Step 1/3: Preparing PDF"` status response.
        4. Calls  helper `pdf_processor.py` file's function  `await process_pdf_job(SCRIPT_PATH, file_path, job_output_dir)` which:
	        - Permission management
            - Launches the Apptainer script,
            - Binds `/input` and `/output`,
            - Packs the resulting JSON chunks into `<results>/<job_id>.zip`.
        5. On success, yields `"Step 3/3: Processing completed"` with `output_url="file://<zip_path>"`, and cleans up the temp PDF.
        6. On failure, yields `"Processing failed: <error message>"`.
        
    - **`check_job`**
        - Allows polling: if `<results>/<job_id>.zip` exists, returns status `"Done"` plus that file URL; otherwise returns `"Running"`.
    
    - **`health_check`**
        - Immediately returns `"Health check successful"`.
    
3. **Error Handling & Cleanup**
    - Catches any exception in `_handle_process_pdf` and streams back an `"Exception"` status.
    - Uses `set_missing_ok` unlink to avoid noisy errors when deleting the uploaded PDF.


