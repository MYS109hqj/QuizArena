from fastapi import FastAPI
from .routes import router as websocket_router  # 使用相对导入
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],        # 允许所有方法（GET, POST, OPTIONS 等）
    allow_headers=["*"],        # 允许所有头
)

app.include_router(websocket_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
