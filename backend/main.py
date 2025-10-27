import fastapi
from api.routes import router as websocket_router


def create_app():
    app = fastapi.FastAPI(title="CodeLens")

    # CORS managed by Nginx

    app.include_router(websocket_router)

    return app


app = create_app()


@app.head("/")
async def root():
    return {"message": "Welcome to CodeLens API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
