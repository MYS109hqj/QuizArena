from fastapi import FastAPI
from .routes import router as websocket_router  # 使用相对导入
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# 从环境变量读取允许的源，支持多个域名用逗号分隔
allowed_origins_env = os.getenv('ALLOWED_ORIGINS', '').strip()
if allowed_origins_env:
    # 如果设置了环境变量，使用环境变量中的域名
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(',') if origin.strip()]
    print(f"🔒 CORS配置: 使用环境变量中的允许源 - {allowed_origins}")
else:
    # 如果没有设置环境变量，默认允许开发环境（localhost）
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
    print("🔓 CORS配置: 使用开发环境默认源 - localhost")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # 动态配置允许的源
    allow_credentials=True,
    allow_methods=["*"],        # 允许所有方法（GET, POST, OPTIONS 等）
    allow_headers=["*"],        # 允许所有头
)

app.include_router(websocket_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
