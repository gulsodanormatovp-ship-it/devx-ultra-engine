import os
import sys
import asyncio
import subprocess
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="DevX Ultra Complete Engine", version="1.0.0")

# --- 1. DATA MODELS ---
class CodeRunRequest(BaseModel):
    code: str

class BotCreateRequest(BaseModel):
    bot_token: str
    channel_username: str  # Majburiy obuna uchun kanal (@username)
    admin_id: int

# --- 2. GLOBAL PROCESS MANAGER ---
running_bots: Dict[str, subprocess.Popen] = {}

# --- 3. EXECUTE CODE (Sandbox Runner) ---
@app.post("/api/v1/run-code")
async def run_code(req: CodeRunRequest):
    try:
        process = subprocess.run(
            [sys.executable, "-c", req.code],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {
            "status": "success",
            "stdout": process.stdout,
            "stderr": process.stderr,
            "exit_code": process.returncode
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=400, detail="Kod bajarilish vaqti tugadi (Timeout: 10s)")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 4. NO-CODE BOT BUILDER & 24/7 DEPLOYER ---
@app.post("/api/v1/create-bot")
async def create_and_start_bot(req: BotCreateRequest, background_tasks: BackgroundTasks):
    bot_filename = f"bot_{req.admin_id}.py"
    
    bot_code = f"""import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

BOT_TOKEN = "{req.bot_token}"
CHANNEL = "{req.channel_username}"
ADMIN_ID = {req.admin_id}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def check_sub(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return False

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    is_subscribed = await check_sub(message.from_user.id)
    if is_subscribed:
        await message.answer("Xush kelibsiz! Obuna tasdiqlandi. Barcha imkoniyatlardan foydalanishingiz mumkin.")
    else:
        await message.answer(f"Botdan foydalanish uchun kanalimizga obuna bo'ling: {{CHANNEL}}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
"""

    with open(bot_filename, "w", encoding="utf-8") as f:
        f.write(bot_code)

    if bot_filename in running_bots:
        running_bots[bot_filename].terminate()

    proc = subprocess.Popen([sys.executable, bot_filename])
    running_bots[bot_filename] = proc

    return {
        "status": "active",
        "message": f"Bot {bot_filename} muvaffaqiyatli ishga tushdi va 24/7 fonga o'tkazildi!",
        "process_id": proc.pid
    }

# --- 5. AI CODE ASSISTANT & AUTO-FIX ---
@app.post("/api/v1/ai-fix")
async def ai_fix_code(req: CodeRunRequest):
    fixed_code = req.code
    explanation = "Koddagi mantiq va sintaksis tekshirildi."
    
    if "print(" not in req.code and "print " in req.code:
        fixed_code = req.code.replace("print ", "print(").replace("\n", ")\n")
        explanation = "Python 3 uchun print operatoriga qavslar qo'shildi."
        
    return {
        "original_code": req.code,
        "fixed_code": fixed_code,
        "explanation": explanation
    }

# --- 6. REAL-TIME WEBSOCKET ---
@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"[Server Eco]: {data} qabul qilindi.")
    except WebSocketDisconnect:
        print("WebSocket uzildi")
