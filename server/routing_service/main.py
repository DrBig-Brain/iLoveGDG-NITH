from fastapi import FastAPI
import uvicorn
from .router import router

app = FastAPI(
    title="Routing Service",
    description="Intelligent LLM Router Middleware",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "Routing-Service",
        "status": "healthy",
        "endpoints": ["/v1/route", "/v1/chat/completions"],
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
