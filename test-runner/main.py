
import docker

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        client = docker.from_env()
        container = client.containers.run(
            "python:3.9-slim",
            command=["python", "-c", data],
            detach=True,
        )
        result = container.wait()
        logs = container.logs()
        await websocket.send_text(logs.decode("utf-8"))
        container.remove()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
