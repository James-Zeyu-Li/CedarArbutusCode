#!/usr/bin/env python3
import asyncio
import grpc
import grpc_task_pb2
import grpc_task_pb2_grpc
import argparse


async def async_request_generator(request):
    """Asynchronized generator to yield a request."""
    yield request


async def test_grpc_call():
    async with grpc.aio.insecure_channel("127.0.0.1:5052") as channel:
        stub = grpc_task_pb2_grpc.TaskServiceStub(channel)
        request = grpc_task_pb2.TaskRequest(
            task_name="health_check", input_data="test")

        async for response in stub.SubmitTask(async_request_generator(request)):
            print(
                f"Response Received: job_id={response.job_id}, status={response.status}, output_url={response.output_url}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test gRPC Communication")
    parser.add_argument("--server", type=str,
                        default="127.0.0.1:5052", help="gRPC Server Address")
    args = parser.parse_args()

    asyncio.run(test_grpc_call())
