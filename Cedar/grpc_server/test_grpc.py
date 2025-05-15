#!/usr/bin/env python3
import asyncio
import grpc
import grpc_task_pb2
import grpc_task_pb2_grpc
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)


async def test_grpc_call():
    try:
        async with grpc.aio.insecure_channel("localhost:5050") as channel:
            stub = grpc_task_pb2_grpc.TaskServiceStub(channel)
            request = grpc_task_pb2.TaskRequest(
                task_name="health_check", input_data="test")

            async def request_generator():
                yield request

            print("Sending health check request")
            async for response in stub.SubmitTask(request_generator()):
                print(
                    f"Respond received: job_id={response.job_id}, status={response.status}, output_url={response.output_url}")

            print("Healthcheck fininshed")
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_grpc_call())

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
