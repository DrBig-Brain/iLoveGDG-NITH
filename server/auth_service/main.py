from fastapi import FastAPI
import uvicorn
from .router import router

app = FastAPI(
    title="Auth Service",
    description="API Key Authentication & Management Service for Multi-Model Router",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "Auth-Service",
        "status": "healthy",
        "endpoints": ["/auth/keys", "/auth/validate", "/auth/revoke"],
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
