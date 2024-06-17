# login_server.py
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import logging
from starlette.middleware.sessions import SessionMiddleware
from secrets import token_urlsafe
from .routers import login, users, internal
import os
from .paths import BASE_PATH
from contextlib import asynccontextmanager
from .services.chatbot import Chatty
from .models.Models import init_db

logger = logging.getLogger("uvicorn.error")
logging.basicConfig(filename="gpt-rag.log", encoding="utf-8", level=logging.DEBUG)


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    print("init lifespan")
    init_db()  # Ensure the database and tables are created
    app.state.chatty = Chatty()
    yield
    print("clean up lifespan")


app = FastAPI(lifespan=app_lifespan)
app.add_middleware(
    SessionMiddleware, secret_key=token_urlsafe(32), session_cookie="gpt-rag"
)

app.mount("/static", StaticFiles(directory=str(BASE_PATH / "static")), name="static")


@app.get("/favicon.ico")
async def favicon():
    file_name = "favicon.ico"
    file_path = os.path.join(BASE_PATH, "static", file_name)
    return FileResponse(
        path=file_path,
        headers={"Content-Disposition": "attachment; filename=" + file_name},
    )


app.include_router(login.router)
app.include_router(users.router)
app.include_router(internal.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
