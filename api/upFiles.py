# coding: utf-8
import os
import asyncio
import shutil
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from util.client_cosmic import Cosmic
from util.client_transcribe import transcribe
from util.client_adjust_srt import adjust_srt
from util.client_show_tips import show_file_tips
from util.client_hot_update import update_hot_all
from util.empty_working_set import empty_current_working_set

app = FastAPI(title="CapsWriter Transcription Server", version="1.0.0")

# 确保当前目录为根目录
BASE_DIR = os.path.dirname(__file__)
os.chdir(BASE_DIR)

# 初始化（可放入 startup 事件）
@app.on_event("startup")
async def startup_event():
    # update_hot_all()
    if os.name == 'nt':  # Windows清理物理内存
        empty_current_working_set()
    print("✅ CapsWriter Transcription Server 已启动")


@app.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    上传文件后转录生成字幕或修正字幕。
    上传完成后才会开始转录（异步后台执行）。
    """
    # show_file_tips() 关闭提示

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    saved_files = []

    # 逐个保存上传文件
    for file in files:
        file_path = upload_dir / file.filename
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            saved_files.append(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")

    # 上传完成后才开始异步处理
    background_tasks.add_task(process_files, saved_files)

    return JSONResponse({
        "status": "success",
        "message": f"共上传 {len(saved_files)} 个文件，后台开始转录。",
        "files": [str(f) for f in saved_files]
    })


async def process_files(files: List[Path]):
    """
    异步后台任务：文件上传完成后处理转录或字幕调整
    """
    for file in files:
        print(f"🔍 开始处理文件: {file.name}")

        # 根据扩展名判断任务类型
        if file.suffix in ['.txt', '.json', '.srt']:
            adjust_srt(file)
        else:
            await transcribe(file)

        print(f"✅ 文件处理完成: {file.name}")

    if Cosmic.websocket:
        await Cosmic.websocket.close()


@app.get("/")
async def root():
    return {"message": "CapsWriter FastAPI Server 正在运行"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "upFiles:app",   # 模块名:应用对象
        host="0.0.0.0",          # 允许外部访问
        port=8000,               # 指定端口
        reload=True,             # 开发模式自动重载
        workers=1                # 单进程（保持全局状态一致）
    )
