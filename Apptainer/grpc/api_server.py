#!/usr/bin/env python3
import asyncio
import grpc
import grpc_task_pb2
import grpc_task_pb2_grpc
import argparse
import os
import sys
import logging
import time
import zipfile
import shutil
from pathlib import Path

# Logging Setting
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/home/ubuntu/myenvFlask/arbutus_client.log")
    ]
)
logger = logging.getLogger("arbutus_pdf_processor")

# Settings
DEFAULT_SERVER = "127.0.0.1:5052"
# this needs to changed or set to be flexible as required
DEFAULT_PDF = "/home/ubuntu/myenvFlask/fema_nims_doctrine-2017.pdf"
RESULTS_DIR = "/home/ubuntu/myenvFlask/results"


async def async_request_generator(request):
    yield request


async def check_job_status(job_id, server_address):
    async with grpc.aio.insecure_channel(server_address) as channel:
        stub = grpc_task_pb2_grpc.TaskServiceStub(channel)
        req = grpc_task_pb2.TaskRequest(
            task_name="check_job",
            input_data=job_id
        )
        async for resp in stub.SubmitTask(async_request_generator(req)):
            return resp.status, resp.output_url
    return "Error", ""


async def wait_for_job_completion(job_id, server_address, timeout=3600, check_interval=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        status, output_url = await check_job_status(job_id, server_address)
        if "completed" in status or "success" in status:
            return status, output_url
        if "error" in status or "failed" in status:
            logger.error(f"Job failed: {status}")
            return status, output_url
        logger.info(f"Job {job_id} running: {status}")
        await asyncio.sleep(check_interval)
    logger.error(f"Job {job_id} timed out after {timeout} seconds")
    return "Timeout finished", ""


async def download_results(output_url, download_dir):
    if not output_url.startswith("file://"):
        logger.error(f"Unsupported URL: {output_url}")
        return None
    src = output_url[len("file://"):]
    if not os.path.exists(src):
        logger.error(f"Result file not found: {src}")
        return None
    os.makedirs(download_dir, exist_ok=True)
    if src.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(src, 'r') as z:
                z.extractall(download_dir)
            logger.info(f"Unzipped result to: {download_dir}")
            return download_dir
        except zipfile.BadZipFile as e:
            logger.error(f"ZIP extraction failed: {e}")
            return None
    else:
        dest = os.path.join(download_dir, os.path.basename(src))
        try:
            shutil.copy2(src, dest)
            logger.info(f"Copied result to: {dest}")
            return dest
        except Exception as e:
            logger.error(f"File copy failed: {e}")
            return None


async def process_pdf(pdf_path, server_address=DEFAULT_SERVER, download_dir=RESULTS_DIR):
    if not os.path.exists(pdf_path):
        logger.error(f"Error: PDF file does not exist: {pdf_path}")
        return False
    with open(pdf_path, 'rb') as f:
        file_content = f.read()
    file_name = os.path.basename(pdf_path)
    logger.info(f"Read PDF file: {pdf_path} ({len(file_content)} bytes)")
    async with grpc.aio.insecure_channel(server_address) as channel:
        stub = grpc_task_pb2_grpc.TaskServiceStub(channel)
        req = grpc_task_pb2.TaskRequest(
            task_name="process_pdf",
            input_data="",
            file_content=file_content,
            file_name=file_name
        )
        job_id = None
        final_status = None
        output_url = None
        async for resp in stub.SubmitTask(async_request_generator(req)):
            logger.info(
                f"Received response: job_id={resp.job_id}, status={resp.status}, output_url={resp.output_url}")
            if job_id is None and resp.job_id:
                job_id = resp.job_id
            final_status = resp.status
            if resp.output_url:
                output_url = resp.output_url
    if not job_id:
        logger.error("No valid job ID received")
        return False
    if "completed" not in final_status and "success" not in final_status and not output_url:
        final_status, output_url = await wait_for_job_completion(job_id, server_address)
    if output_url:
        result_dir = await download_results(output_url, download_dir)
        if not result_dir:
            return False
        logger.info(f"PDF processing completed, result saved to: {result_dir}")
    return "completed" in final_status or "success" in final_status


async def health_check(server_address=DEFAULT_SERVER):
    async with grpc.aio.insecure_channel(server_address) as channel:
        stub = grpc_task_pb2_grpc.TaskServiceStub(channel)
        req = grpc_task_pb2.TaskRequest(task_name="health_check")
        async for resp in stub.SubmitTask(async_request_generator(req)):
            return "success" in resp.status
    return False


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', default=DEFAULT_PDF)
    parser.add_argument('--server', default=DEFAULT_SERVER)
    parser.add_argument('--output', default=RESULTS_DIR)
    parser.add_argument(
        '--action', choices=['process', 'health'], default='process')
    args = parser.parse_args()
    os.makedirs(args.output, exist_ok=True)
    if args.action == 'health':
        ok = await health_check(args.server)
        sys.exit(0 if ok else 1)
    else:
        success = await process_pdf(args.pdf, args.server, args.output)
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    asyncio.run(main())
