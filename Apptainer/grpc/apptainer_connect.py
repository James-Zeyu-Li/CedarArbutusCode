import paramiko
import time
import subprocess

# SSH to run the slurm command
KEY_PATH = "/home/ubuntu/.ssh/cedar_automation_key"
USER = "zeyu167"
HOST = "robot.cedar.alliancecan.ca"  # the slurm submission ssh host

LOG_PATH = "/scratch/zeyu167/logs/apptainer_output.log"


def ssh_connect(host, user, key_path):
    """do ssh connection"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key_file(key_path)
    ssh.connect(hostname=host, username=user, pkey=key)
    return ssh


def submit_slurm_job(ssh):
    """ sumbit a slurm job"""
    cmd = "sbatch --chdir=/scratch/zeyu167 /scratch/zeyu167/run_apptainer.sh"
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
