#!/usr/bin/env python3
import grpc
import asyncio
import logging
import time
from pathlib import Path

import grpc_task_pb2
import grpc_task_pb2_grpc

from pdf_processor import process_pdf_job

BASE_DIR = Path("/scratch/zeyu167")
INPUT_DIR = BASE_DIR / "inputs"
OUTPUT_DIR = BASE_DIR / "results"
SCRIPT_PATH = BASE_DIR / "SLM" / "newIngestion.sh"
LOG_PATH = BASE_DIR / "logs" / "grpc_server.log"

# directory check
for p in [INPUT_DIR, OUTPUT_DIR, LOG_PATH.parent]:
    p.mkdir(parents=True, exist_ok=True)

# Logging config
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PDFProcessingServer")


class TaskService(grpc_task_pb2_grpc.TaskServiceServicer):
    async def SubmitTask(self, request_iterator, context):
        request = await request_iterator.__anext__()
        job_id = f"job_{int(time.time())}"

        if request.task_name == "process_pdf":
            async for resp in self._handle_process_pdf(request, job_id):
                yield resp

        elif request.task_name == "check_job":
            zip_path = OUTPUT_DIR / f"{request.input_data}.zip"
            if zip_path.exists():
                yield grpc_task_pb2.TaskResponse(
                    job_id=job_id,
                    status="Done",
                    output_url=f"file://{zip_path}"
                )
            else:
                yield grpc_task_pb2.TaskResponse(
                    job_id=job_id,
                    status="Running",
                    output_url=""
                )

        elif request.task_name == "health_check":
            yield grpc_task_pb2.TaskResponse(
                job_id=job_id,
                status="Health check successful",
                output_url=""
            )

        else:
            yield grpc_task_pb2.TaskResponse(
                job_id=job_id,
                status=f"Unsupported task type: {request.task_name}",
                output_url=""
            )

    async def _handle_process_pdf(self, request, job_id):
        try:
            if request.file_content:
                file_path = INPUT_DIR / f"{job_id}_{request.file_name}"
                with open(file_path, "wb") as f:
                    f.write(request.file_content)
                logger.info(f"Received file: {file_path}")
            elif request.input_data:
                file_path = Path(request.input_data)
                if not file_path.is_absolute():
                    file_path = BASE_DIR / request.input_data
            else:
                yield grpc_task_pb2.TaskResponse(
                    job_id=job_id,
                    status="No file content or path provided",
                    output_url=""
                )
                return

            yield grpc_task_pb2.TaskResponse(
                job_id=job_id,
                status=f"Step 1/3: Preparing PDF {file_path}",
                output_url=""
            )

            job_output_dir = OUTPUT_DIR / job_id
            success, zip_path, status_msg = await process_pdf_job(SCRIPT_PATH, file_path, job_output_dir)

            if success:
                yield grpc_task_pb2.TaskResponse(
                    job_id=job_id,
                    status="Step 3/3: Processing completed",
                    output_url=f"file://{zip_path}"
                )
                if request.file_content:
                    file_path.unlink(missing_ok=True)
                    logger.info(f"Deleted temp file: {file_path}")
            else:
                yield grpc_task_pb2.TaskResponse(
                    job_id=job_id,
                    status=f"Processing failed: {status_msg}",
                    output_url=""
                )

        except Exception as e:
            logger.exception(f"Exception in PDF processing: {e}")
            yield grpc_task_pb2.TaskResponse(
                job_id=job_id,
                status=f"Exception: {e}",
                output_url=""
            )


async def serve():
    server = grpc.aio.server()
    grpc_task_pb2_grpc.add_TaskServiceServicer_to_server(TaskService(), server)
    server.add_insecure_port("[::]:5050")
    logger.info("Starting gRPC server on port 5050")
    await server.start()
    await server.wait_for_termination()

if __name__ == "__main__":
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        logger.info("Service interrupted")
    except Exception as e:
        logger.exception(f"Service crashed: {e}")
