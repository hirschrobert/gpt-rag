from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from fastapi import Request, APIRouter, HTTPException, Depends
from ..models.Models import User
from .dependencies import templates, get_db
from starlette.responses import RedirectResponse, HTMLResponse, JSONResponse


router = APIRouter()


@router.get("/chatbot", response_class=HTMLResponse)
async def chatbot(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=403, detail="Not authorized")
    if not request.app.state.chatty.get_client(user.id):
        request.app.state.chatty.set_client(user.id)
    chatbot = request.app.state.chatty.get_client(user.id)
    return templates.TemplateResponse(
        "chatbot.html",
        {
            "request": request,
            "bot_name": request.app.state.chatty.get_bot_name(user.id),
            "chat_history": request.app.state.chatty.get_history(user.id),
        },
    )


@router.post("/chatbot/send_message")
async def send_message(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return JSONResponse(status_code=403, content={"error": "Not authorized"})
    data = await request.json()
    user_message = data.get("message")
    if user_message:
        gpt_response = request.app.state.chatty.chat_completion(user_id, user_message)
        return JSONResponse(content=gpt_response)
    return JSONResponse(status_code=400, content={"error": "Invalid input"})
