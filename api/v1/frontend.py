from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from api.v1.captch import captcha_generator, generate_captcha_text

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/captcha")
def captcha(request: Request):
    text = generate_captcha_text()
    request.session["captcha"] = text.lower()
    data = captcha_generator.generate(text)
    return StreamingResponse(data, media_type="image/png")


@router.post("/submit", response_class=HTMLResponse)
async def submit(request: Request, captcha: str = Form(...)):
    real = request.session.get("captcha")
    if not real or captcha.lower() != real:
        return HTMLResponse(
            "<h2>❌ Неверная капча</h2><a href='/'>← Назад</a>",
            status_code=400,
        )

    request.session.pop("captcha", None)
    return HTMLResponse(
        "<h2>✅ Капча пройдена успешно!</h2><a href='/'>← На главную</a>"
    )
