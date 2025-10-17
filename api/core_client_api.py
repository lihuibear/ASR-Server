# coding: utf-8
# coding: utf-8

import os
import sys
import asyncio
import signal
from pathlib import Path
from platform import system
from typing import List, Optional, Dict
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import aiofiles

import colorama
import keyboard

from config import ClientConfig as Config
from util.client_cosmic import console, Cosmic
from util.client_stream import stream_open, stream_close
from util.client_shortcut_handler import shortcut_handler
from util.client_recv_result import recv_result
from util.client_show_tips import show_mic_tips, show_file_tips
from util.client_hot_update import update_hot_all, observe_hot

from util.client_transcribe import transcribe
from util.client_adjust_srt import adjust_srt

from util.empty_working_set import empty_current_working_set

# 初始化FastAPI应用
app = FastAPI(title="CapsWriter API", description="语音转文字服务接口")

# 确保根目录位置正确，用相对路径加载模型
BASE_DIR = os.path.dirname(__file__);
os.chdir(BASE_DIR)

# 确保终端能使用 ANSI 控制字符
colorama.init()

# 全局状态管理
app.state.mic_running = False
app.state.transcription_tasks = {}  # 存储正在进行的转录任务 {task_id: status}

# MacOS 的权限设置
if system() == 'Darwin':
    if os.getuid() != 0:
        console.print('在 MacOS 上需要以管理员启动客户端才能监听键盘活动，请 sudo 启动', style="red")
        sys.exit()
    else:
        os.umask(0o000)


# 后台任务 - 麦克风处理
async def mic_background_task():
    """后台运行麦克风实时转录任务"""
    try:
        Cosmic.loop = asyncio.get_event_loop()
        Cosmic.queue_in = asyncio.Queue()
        Cosmic.queue_out = asyncio.Queue()

        # 更新热词
        update_hot_all()

        # 实时更新热词
        observer = observe_hot()

        # 打开音频流
        Cosmic.stream = stream_open()

        # Ctrl-C 关闭音频流，触发自动重启
        signal.signal(signal.SIGINT, stream_close)

        # 绑定按键
        keyboard.hook_key(Config.shortcut, shortcut_handler)

        # 清空物理内存工作集
        if system() == 'Windows':
            empty_current_working_set()

        # 接收结果
        while app.state.mic_running:
            await recv_result()

    except Exception as e:
        console.print(f"麦克风处理任务出错: {str(e)}", style="red")
    finally:
        app.state.mic_running = False
        stream_close(None, None)  # 关闭流
        console.print("麦克风处理已停止", style="green")


# API端点
@app.post("/start-mic", response_model=Dict[str, str])
async def start_microphone(background_tasks: BackgroundTasks):
    """启动麦克风实时转录"""
    if app.state.mic_running:
        return JSONResponse(content={"status": "error", "message": "麦克风转录已在运行中"}, status_code=400)

    app.state.mic_running = True
    background_tasks.add_task(mic_background_task)
    return {"status": "success", "message": "麦克风转录已启动"}


@app.post("/stop-mic", response_model=Dict[str, str])
async def stop_microphone():
    """停止麦克风实时转录"""
    if not app.state.mic_running:
        return JSONResponse(content={"status": "error", "message": "麦克风转录未在运行中"}, status_code=400)

    app.state.mic_running = False
    return {"status": "success", "message": "麦克风转录已停止"}


@app.get("/mic-status", response_model=Dict[str, bool])
async def get_mic_status():
    """获取麦克风转录状态"""
    return {"running": app.state.mic_running}


async def process_file_task(file_path: str, task_id: str):
    """处理文件转录的后台任务（稳定版）"""
    from util.client_cosmic import Cosmic

    try:
        app.state.transcription_tasks[task_id] = "processing"
        file = Path(file_path)

        # ✅ 打印调试信息
        console.print(f"[调试] 任务 {task_id} 开始处理文件: {file.resolve()}", style="cyan")

        # ✅ 检查文件是否存在
        if not file.exists():
            console.print(f"[错误] 文件不存在: {file}", style="red")
            app.state.transcription_tasks[task_id] = "error: 文件不存在"
            return

        # ✅ 初始化 Cosmic 环境（让 transcribe 可用）
        Cosmic.loop = asyncio.get_event_loop()
        Cosmic.queue_in = asyncio.Queue()
        Cosmic.queue_out = asyncio.Queue()

        # ✅ 更新热词（可选）
        try:
            update_hot_all()
            observer = observe_hot()
        except Exception as e:
            console.print(f"[警告] 热词更新失败: {e}", style="yellow")

        # ✅ Windows 性能优化
        if system() == "Windows":
            try:
                empty_current_working_set()
            except Exception:
                pass

        # ✅ 开始处理
        if file.suffix.lower() in [".txt", ".json", ".srt"]:
            console.print(f"[提示] 调整字幕文件: {file.name}", style="magenta")
            adjust_srt(file)
        else:
            console.print(f"[提示] 开始转录音频/视频文件: {file.name}", style="magenta")
            await transcribe(file)

        app.state.transcription_tasks[task_id] = "completed"
        console.print(f"[完成] 任务 {task_id} 转录完成", style="green")

    except FileNotFoundError as e:
        console.print(f"[错误] 文件未找到: {e}", style="red")
        app.state.transcription_tasks[task_id] = f"error: {str(e)}"

    except Exception as e:
        # 捕获所有异常
        console.print(f"[异常] 文件处理出错: {str(e)}", style="red")
        app.state.transcription_tasks[task_id] = f"error: {str(e)}"

    finally:
        # ✅ 安全清理临时文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                console.print(f"[清理] 临时文件已删除: {file_path}", style="dim")
        except Exception as e:
            console.print(f"[警告] 删除临时文件失败: {e}", style="yellow")


@app.post("/transcribe-file", response_model=Dict[str, str])
async def transcribe_file(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...)
):
    """上传文件并进行转录"""
    import uuid

    task_id = str(uuid.uuid4())

    try:
        temp_dir = os.path.join(BASE_DIR, "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)
        safe_name = Path(file.filename).name.replace(" ", "_")  # 防止空格或特殊字符
        file_path = os.path.join(temp_dir, f"{task_id}_{safe_name}")

        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # ✅ 关闭 UploadFile，释放资源
        await file.close()

        # 注册后台任务
        app.state.transcription_tasks[task_id] = "pending"
        background_tasks.add_task(process_file_task, file_path, task_id)

        return {"status": "success", "task_id": task_id, "message": "文件已接收，正在处理"}

    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": f"文件处理失败: {str(e)}"},
            status_code=500
        )


@app.get("/task-status/{task_id}", response_model=Dict[str, str])
async def get_task_status(task_id: str):
    """查询转录任务状态"""
    if task_id not in app.state.transcription_tasks:
        raise HTTPException(status_code=404, detail="任务ID不存在")

    return {
        "task_id": task_id,
        "status": app.state.transcription_tasks[task_id]
    }


@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "CapsWriter API"}


if __name__ == "__main__":
    # 启动FastAPI服务
    uvicorn.run(
        "core_client_api:app",
        host="0.0.0.0",  # 允许所有网络接口访问
        port=8000,  # 服务端口
        reload=True,  # 开发模式下自动重载
        workers=1  # 单工作进程，因为有全局状态
    )
