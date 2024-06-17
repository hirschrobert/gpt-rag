from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import APIRouter, Request, Form, Depends
from .dependencies import templates, get_db
from sqlalchemy.orm import Session
from pwdlib import PasswordHash
from ..models.Models import User


# Helper function to verify user credentials and retrieve user roles
def verify_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    password_hash = PasswordHash.recommended()
    hash = password_hash.hash(password)
    if user and password_hash.verify(password=password, hash=hash):
        return user
    return None


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    user_id = request.session.get("user_id")
    if user_id:
        return RedirectResponse(url="/dashboard", status_code=303)
    return RedirectResponse(url="/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = verify_user(db, username, password)
    if user:
        request.session["user_id"] = user.id
        response = RedirectResponse(url="/dashboard", status_code=303)
        return response
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": "Invalid username or password"}
    )
