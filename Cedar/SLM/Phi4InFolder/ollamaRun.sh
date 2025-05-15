#!/bin/bash

# run apptainer through ceder
module load apptainer

# turn on apptainer
# Apptainer, Grpc, Ollama, Phi4, KGGen
apptainer instance run --nv \
  --env PATH="/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin" \
  --bind /scratch/zeyu167/grpc_server:/app \
  --bind /scratch/zeyu167/SLM/models:/opt/ollama-storage \
  --bind /scratch/zeyu167/SLM/logs:/var/log/ollama \
  newOllama.sif ollama_grpc

echo "Waiting for instance to start..."
sleep 10

# 手动在容器内启动 Ollama 服务（后台运行）
echo "Starting Ollama service in instance..."
apptainer exec instance://ollama_grpc bash -c 'nohup ollama serve > /var/log/ollama/ollama.log 2>&1 &'

# 等待服务启动
echo "Waiting for Ollama service to be ready..."
sleep 10

# 测试 Ollama API 是否可用
echo "Testing Ollama API from instance:"
apptainer exec instance://ollama_grpc curl -s http://127.0.0.1:11434/api/tags

# 测试调用 phi4 模型
echo "Testing Ollama model call (phi4):"
if [ ! -d "/opt/ollama-storage/models" ] || [ -z "$(ls -A /opt/ollama-storage/models)" ]; then
  echo "No cached model found, pulling phi4..."
  apptainer exec instance://ollama_grpc bash -c 'nohup ollama serve > /var/log/ollama/ollama.log 2>&1 &'
  sleep 10
  apptainer exec instance://ollama_grpc ollama pull phi4
else
  echo "phi4 already cached, skipping download."
fi


# 测试 KGgen 命令行工具是否正常（显示帮助信息）
echo "Testing KGgen CLI (help message):"
apptainer exec instance://ollama_grpc python3 -c "import kg_gen; print('KGGen version:', getattr(kg_gen, '__version__', 'Not defined')); print('KGGen contents:', dir(kg_gen))"

echo "All tests complete."