
import unittest
import io
import sys

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
        # Create a temporary file to store the tests
        with open("temp_test.py", "w") as f:
            f.write(data)

        # Run the tests
        suite = unittest.defaultTestLoader.discover(".", pattern="temp_test.py")
        runner = unittest.TextTestRunner(stream=io.StringIO())
        result = runner.run(suite)

        # Send the results back to the backend
        await websocket.send_text(str(result))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
