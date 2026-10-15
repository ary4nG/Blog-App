from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.routers import users, auth, posts, comments
from app.events import producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: connect the Kafka producer before the app serves requests
    await producer.start()
    yield
    # shutdown: flush + close the producer cleanly
    await producer.stop()


app = FastAPI(lifespan=lifespan)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred."},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)