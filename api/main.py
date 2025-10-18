# coding: utf-8
import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# 导入两个子模块中的 router
from api_transcribe import router as transcribe_router
from api_records import router as records_router

from util.empty_working_set import empty_current_working_set

app = FastAPI(
    title="CapsWriter Unified API Server",
    version="1.0.0",
    description="文件上传转录 + MySQL 查询 一体化服务"
)

# 注册路由
app.include_router(transcribe_router)
app.include_router(records_router)

# =====================================================
# 启动事件
# =====================================================
@app.on_event("startup")
async def startup_event():
    if os.name == 'nt':
        empty_current_working_set()
    print("✅ CapsWriter Unified Server 已启动")

# =====================================================
# 通用接口
# =====================================================
@app.get("/", response_class=JSONResponse)
async def root():
    return {"message": "CapsWriter FastAPI Server 正在运行"}

@app.get("/health", response_class=JSONResponse)
async def health_check():
    return {"status": "ok"}

# =====================================================
# 启动入口
# =====================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
