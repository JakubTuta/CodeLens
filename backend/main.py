import fastapi
from fastapi.middleware.cors import CORSMiddleware
from websocket.routes import router as websocket_router


def create_app():
    app = fastapi.FastAPI(title="CodeLens")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(websocket_router)

    return app


app = create_app()
