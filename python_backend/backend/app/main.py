from fastapi import FastAPI
from routes import router as websocket_router  # 使用相对导入

app = FastAPI()

app.include_router(websocket_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
