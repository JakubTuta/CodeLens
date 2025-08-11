import os

import fastapi
from api.routes import router as websocket_router
from fastapi.middleware.cors import CORSMiddleware


def create_app():
    app = fastapi.FastAPI(title="CodeLens")

    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(websocket_router)

    return app


app = create_app()


@app.get("/")
async def root():
    return {"message": "Welcome to CodeLens API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
