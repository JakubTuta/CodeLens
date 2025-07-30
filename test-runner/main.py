
import docker
import asyncio

import fastapi
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContainerPool:
    def __init__(self, size=5):
        self.size = size
        self.pool = asyncio.Queue(maxsize=size)
        self.client = docker.from_env()

    async def start(self):
        for _ in range(self.size):
            container = self.client.containers.run(
                "python:3.9-slim",
                command=["sleep", "infinity"],
                detach=True,
            )
            await self.pool.put(container)

    async def stop(self):
        while not self.pool.empty():
            container = await self.pool.get()
            container.stop()
            container.remove()

    async def execute_test(self, test_code: str):
        container = await self.pool.get()
        try:
            exec_result = container.exec_run(["python", "-c", test_code], timeout=30)
            return exec_result.output.decode("utf-8")
        except Exception as e:
            return str(e)
        finally:
            await self.pool.put(container)

container_pool = ContainerPool()

@app.on_event("startup")
async def startup_event():
    await container_pool.start()

@app.on_event("shutdown")
async def shutdown_event():
    await container_pool.stop()

@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        result = await container_pool.execute_test(data)
        await websocket.send_text(result)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
