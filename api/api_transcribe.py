# coding: utf-8
import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from util.client_cosmic import Cosmic
from util.client_transcribe import transcribe
from util.client_adjust_srt import adjust_srt

router = APIRouter(prefix="/transcribe", tags=["Transcription"])

@router.post("/upload", response_class=JSONResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """
    上传文件后后台异步处理（转录或调整字幕）
    """
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    saved_files = []
    for file in files:
        file_path = upload_dir / file.filename
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            saved_files.append(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")

    background_tasks.add_task(process_files, saved_files)

    return {
        "status": "success",
        "message": f"共上传 {len(saved_files)} 个文件，后台开始转录。",
        "files": [str(f) for f in saved_files]
    }


async def process_files(files: List[Path]):
    """
    后台任务：异步处理转录或字幕调整
    """
    for file in files:
        print(f"🔍 开始处理文件: {file.name}")
        if file.suffix in ['.txt', '.json', '.srt']:
            adjust_srt(file)
        else:
            await transcribe(file)
        print(f"✅ 文件处理完成: {file.name}")

    if Cosmic.websocket:
        await Cosmic.websocket.close()
