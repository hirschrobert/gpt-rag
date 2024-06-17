from fastapi import WebSocket, APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from ..models.Models import User, Role
from pwdlib import PasswordHash
from .dependencies import templates, get_db
import json

router = APIRouter()


# regular user
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(url="/", status_code=303)
    roles = [role.name for role in user.roles]
    return templates.TemplateResponse(
        "dashboard.html", {"request": request, "roles": roles}
    )


@router.post("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()
    return templates.TemplateResponse(
        "login.html", {"request": request, "message": "You are logged out!"}
    )


# admin user
@router.get("/manage_users", response_class=HTMLResponse)
async def manage_users(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    user = db.query(User).filter(User.id == user_id).first()
    if not user or "admin" not in [role.name for role in user.roles]:
        raise HTTPException(status_code=403, detail="Not authorized")
    users = db.query(User).all()
    roles = jsonable_encoder(db.query(Role).all())
    return templates.TemplateResponse(
        "manage_users.html", {"request": request, "users": users, "roles": roles}
    )


@router.post("/add_user", response_class=HTMLResponse)
async def add_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/", status_code=303)
    user = db.query(User).filter(User.id == user_id).first()
    if not user or "admin" not in [role.name for role in user.roles]:
        raise HTTPException(status_code=403, detail="Not authorized")
    password_hash = PasswordHash.recommended()
    hashed_password = password_hash.hash(password)
    new_user = User(username=username, password=hashed_password)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/manage_users", status_code=303)


@router.post("/delete_user", response_class=HTMLResponse)
async def delete_user(
    request: Request, user_id: int = Form(...), db: Session = Depends(get_db)
):
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return RedirectResponse(url="/", status_code=303)
    current_user = db.query(User).filter(User.id == current_user_id).first()
    if not current_user or "admin" not in [role.name for role in current_user.roles]:
        raise HTTPException(status_code=403, detail="Not authorized")
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete:
        db.delete(user_to_delete)
        db.commit()
    return RedirectResponse(url="/manage_users", status_code=303)


@router.post("/update_user_role", response_class=HTMLResponse)
async def update_user_role(
    request: Request,
    user_id: int = Form(...),
    role_id: int = Form(...),
    action: str = Form(...),
    db: Session = Depends(get_db),
):
    current_user_id = request.session.get("user_id")
    if not current_user_id:
        return RedirectResponse(url="/", status_code=303)
    current_user = db.query(User).filter(User.id == current_user_id).first()
    if not current_user or "admin" not in [role.name for role in current_user.roles]:
        raise HTTPException(status_code=403, detail="Not authorized")
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    if user and role:
        if action == "add":
            user.roles.append(role)
        elif action == "remove":
            user.roles.remove(role)
        db.commit()
        await broadcast_roles_update(user)
    return RedirectResponse(url="/manage_users", status_code=303)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # handle incoming messages if needed
        await websocket.send_text(f"Message text was: {data}")


async def broadcast_roles_update(user: User):
    message = {
        "user_id": user.id,
        "roles": [{"id": role.id, "name": role.name} for role in user.roles],
    }
    # TODO: send the message to all connected WebSocket clients


# TODO: add WebSocket broadcasting mechanism
websocket_manager = []


async def broadcast_message(message):
    for websocket in websocket_manager:
        await websocket.send_text(json.dumps(message))
