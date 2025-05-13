import asyncio
import grpc
import grpc_task_pb2
import grpc_task_pb2_grpc

async def run_test():
    channel_addr = "127.0.0.1:5051"
    async with grpc.aio.insecure_channel(channel_addr) as channel:
        stub = grpc_task_pb2_grpc.TaskServiceStub(channel)

        response_iterator = stub.SubmitTask(grpc_task_pb2.TaskRequest(
            task_name="testTask",
            input_data="testInput"
        ))
        async for resp in response_iterator:
            print("Received response:")
            print(f"  job_id: {resp.job_id}")
            print(f"  status: {resp.status}")
            print(f"  output_url: {resp.output_url}")

if __name__ == "__main__":
    asyncio.run(run_test())
