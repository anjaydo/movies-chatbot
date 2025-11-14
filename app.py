# app.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from chatbot import chat_with_bot

# === Middleware cho phép iframe embedding (Metabase) ===
class AllowIframeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Cho phép hiển thị trong iframe (Metabase)
        response.headers["X-Frame-Options"] = "ALLOWALL"
        response.headers["Content-Security-Policy"] = "frame-ancestors *"
        return response

# === Khởi tạo app FastAPI ===
app = FastAPI(title="Movie AI Chatbot (RAG Demo)")

# Cho phép Metabase và các client khác gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Metabase local
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # Local dev UI
        "http://127.0.0.1:8000",
        "*",  # Tùy chọn: cho phép tất cả (demo)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thêm middleware cho iframe
app.add_middleware(AllowIframeMiddleware)

# === Gắn thư mục tĩnh và template ===
app.mount("/static", StaticFiles(directory="ui"), name="static")
templates = Jinja2Templates(directory="ui")


# === ROUTES ===
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render giao diện chatbot"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/chat")
async def chat(q: str):
    """API chat đơn giản cho frontend hoặc Metabase"""
    if not q.strip():
        return {"response": "Vui lòng nhập câu hỏi!"}
    response = chat_with_bot(q)
    return {"response": response}


# === Kiểm tra chạy standalone ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
