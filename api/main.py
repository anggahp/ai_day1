from celery.result import AsyncResult
from tasks.celery_app import celery_app
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException, Response, Request
from pydantic import BaseModel
import tasks.celery_tasks as celeryTask
import os
import uuid
import httpx
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from contextlib import asynccontextmanager
from http import HTTPStatus
import logging
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL",
    "https://abc.trycloudflare.com/webhook"
)

# Initialize the Application
ptb = Application.builder().token(TOKEN).build()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI app.
    Starts the PTB application and sets the webhook on startup.
    """
    await ptb.bot.set_webhook(WEBHOOK_URL) # Register the webhook with Telegram
    async with ptb:
        await ptb.start()
        yield # The FastAPI app runs here
    await ptb.stop() # Cleanup on shutdown

app = FastAPI(title="IT Support Automation API", lifespan=lifespan)

FILE_FOLDER = "uploads"
IMAGE_FOLDER = "images"
os.makedirs(FILE_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)


# ── TELEGRAM HANDLERS ────────────────────────────────────────────────────────

async def send_long_message(message, text):
    """
    Helper function to send long messages in chunks.
    """
    chunk_size = 4000
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        await message.reply_text(chunk)

# Definisikan status untuk percakapan
TOPIC, LOCATION = range(2)

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /start command.
    """
    await update.message.chat.send_action(action="typing")
    await update.message.reply_text(
        "Halo dari CrewAI Bot 🚀\n\n"
        "Gunakan /research untuk memulai riset terpandu.\n"
        "Gunakan /status <task_id> jika Anda ingin mengecek manual, namun sekarang saya akan **mengirimkan hasilnya secara otomatis** begitu selesai! 🤖"
    )

async def start_research(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Langkah 1: Memulai riset dan menanyakan topik."""
    await update.message.chat.send_action(action="typing")
    # await update.message.reply_text("🔍 **Mode Riset Terpandu**\nSilakan ketik **Topik** yang ingin Anda riset (atau ketik /cancel untuk batal):")
    await update.message.reply_text("🔍 **Input Topik Riset**\n\nSebutkan topik spesifik yang akan dianalisis oleh sistem.\n\n Ketik /cancel untuk batal.",
    parse_mode="HTML"
)
    return TOPIC

async def get_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Langkah 2: Menyimpan topik dan menanyakan lokasi."""
    context.user_data['topic'] = update.message.text
    await update.message.chat.send_action(action="typing")
    await update.message.reply_text(f"Topik: `{update.message.text}`\n\nSekarang, ketik **Lokasi** risetnya (misal: Indonesia, Global, dll):", parse_mode="Markdown")
    return LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Langkah 3: Menyimpan lokasi dan menjalankan task."""
    topic = context.user_data['topic']
    location = update.message.text
    
    await update.message.chat.send_action(action="typing")
    # Trigger Celery task
    task = celeryTask.research.delay(topic, location, chat_id=update.effective_chat.id)
    
    await update.message.reply_text(
        f"🚀 **Task Research Dimulai!**\n\n"
        f"• Topic: `{topic}`\n"
        f"• Location: `{location}`\n\n"
        f"Saya akan mengirimkan hasilnya ke sini jika sudah selesai. Silakan ditunggu! ☕️",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Membatalkan percakapan."""
    await update.message.reply_text("Riset dibatalkan. Gunakan /research untuk memulai lagi.")
    return ConversationHandler.END

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /status command.
    """
    await update.message.chat.send_action(action="typing")
    if not context.args:
        await update.message.reply_text("Format salah! Gunakan: /status <task_id>")
        return

    task_id = context.args[0]
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == 'SUCCESS':
        result = task_result.result
        if isinstance(result, dict):
            import json
            result_text = json.dumps(result, indent=2)
        else:
            result_text = str(result)
        
        await update.message.reply_text(f"Task Selesai! Berikut hasilnya:")
        await send_long_message(update.message, result_text)
    elif task_result.state == 'FAILURE':
        await update.message.reply_text(f"Task Gagal! Error: {task_result.info}")
    elif task_result.state == 'RUNNING' or task_result.state == 'PENDING':
        await update.message.reply_text(f"Task masih dalam proses (Status: {task_result.state}). Mohon tunggu sebentar.")
    else:
        await update.message.reply_text(f"Status Task: {task_result.state}")

async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle images sent to the bot.
    Downloads the image and triggers the helmet detection task.
    """
    await update.message.chat.send_action(action="typing")
    photo_size = update.message.photo[-1]
    file_id = photo_size.file_id
    
    # Get file info
    new_file = await context.bot.get_file(file_id)
    
    # Generate unique filename
    file_extension = ".jpg" 
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(IMAGE_FOLDER, unique_filename)
    
    # Download file
    await new_file.download_to_drive(file_path)
    
    # Trigger Celery task
    task = celeryTask.detect_helmet.delay(file_path, chat_id=update.effective_chat.id)
    
    reply_text = (
        f"📸 <b>Gambar Diterima!</b>\n\n"
        f"Sedang menjalankan deteksi helm...\n"
        f"Hasilnya akan saya kirimkan otomatis ke sini. Mohon tunggu sebentar! ⏱"
    )

    await update.message.reply_text(reply_text, parse_mode="HTML")

# Register handlers
research_conv = ConversationHandler(
    entry_points=[CommandHandler("research", start_research)],
    states={
        TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_topic)],
        LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

ptb.add_handler(CommandHandler("start", start_handler))
ptb.add_handler(research_conv)
ptb.add_handler(CommandHandler("status", status_handler))
ptb.add_handler(MessageHandler(filters.PHOTO, image_handler))

# ── INPUT MODELS ─────────────────────────────────────────────────────────────

class ResearchInput(BaseModel):
    topic: str
    location: str

class AnalyzeInput(BaseModel):
    topic: str
    location: str

class AnalyzeTicketInput(BaseModel):
    title: str
    description: str

class GenerateSolutionInput(BaseModel):
    issue_type: str
    system: str


# ── RESPONSE MODELS ───────────────────────────────────────────────────────────

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: dict | str | None = None
    error: str | None = None


# ── ENDPOINTS ────────────────────────────────────────────────────────────────

@app.post("/research")
async def research(researchInput: ResearchInput):
    task = celeryTask.research.delay(researchInput.topic, researchInput.location)
    return {"topic": researchInput.topic, "location": researchInput.location, "task_id": task.id}

@app.post("/analyze")
async def analyze(analyzeInput: AnalyzeInput):
    task = celeryTask.analyze_market.delay(analyzeInput.topic, analyzeInput.location)
    return {"topic": analyzeInput.topic, "location": analyzeInput.location, "task_id": task.id}

@app.post("/analyze-ticket")
async def analyze_ticket(body: AnalyzeTicketInput):
    """
    Crew 1: Ticket Analyzer + Classifier
    Output: { category, technical_area, summary }
    """
    task = celeryTask.analyze_ticket.delay(body.title, body.description)
    return {"title": body.title, "task_id": task.id}

@app.post("/generate-solution")
async def generate_solution(body: GenerateSolutionInput):
    """
    Crew 2: Solution Agent + Documentation Agent
    Output: { solution: [...], documentation: "..." }
    """
    task = celeryTask.generate_solution.delay(body.issue_type, body.system)
    return {"issue_type": body.issue_type, "system": body.system, "task_id": task.id}

@app.get("/status/{task_id}", response_model=TaskStatus)
async def get_status(task_id: str) -> TaskStatus:
    task_result = AsyncResult(task_id, app=celery_app)

    if task_result.state == 'SUCCESS':
        return TaskStatus(
            task_id=task_id,
            status=task_result.state,
            result=task_result.result,
        )
    elif task_result.state == 'FAILURE':
        return TaskStatus(
            task_id=task_id,
            status=task_result.state,
            error=str(task_result.info),
        )

    return TaskStatus(
        task_id=task_id,
        status=task_result.state,
    )

@app.post("/file-analyzer")
async def file_analyzer(file: UploadFile = File(...)):
    ALLOWED_EXTENSIONS = {".txt", ".json", ".csv", ".xlsx", ".xls"}
    ALLOWED_MIME_TYPES = {
        "text/plain",
        "application/json",
        "text/csv",
        "text/tab-separated-values",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        "application/vnd.ms-excel",                                          
        "application/octet-stream",
    }

    file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ""

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_extension}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported MIME type '{file.content_type}'. Allowed: TXT, JSON, CSV"
        )

    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(FILE_FOLDER, unique_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    task = celeryTask.file_analyzer.delay(file_path)
    return {"task_id": task.id, "file_path": file_path, "file_type": file_extension}

@app.post("/detect-anomalies")
async def detect_anomalies(file: UploadFile = File(...)):
    ALLOWED_EXTENSIONS = {".xlsx", ".xls"}
    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        "application/vnd.ms-excel",                                          
        "application/octet-stream",
    }

    file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ""

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_extension}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported MIME type '{file.content_type}'. Allowed: Excel (.xlsx, .xls)"
        )

    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(FILE_FOLDER, unique_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    task = celeryTask.detect_anomalies.delay(file_path)
    return {"task_id": task.id, "file_path": file_path, "file_type": file_extension}

@app.post("/predict-sales")
async def predict_sales(file: UploadFile = File(...)):
    ALLOWED_EXTENSIONS = {".xlsx", ".xls"}
    ALLOWED_MIME_TYPES = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        "application/vnd.ms-excel",                                          
        "application/octet-stream",
    }

    file_extension = os.path.splitext(file.filename)[1].lower() if file.filename else ""

    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_extension}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported MIME type '{file.content_type}'. Allowed: Excel (.xlsx, .xls)"
        )

    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(FILE_FOLDER, unique_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    task = celeryTask.predict_sales.delay(file_path)
    return {"task_id": task.id, "file_path": file_path, "file_type": file_extension}

@app.post("/detect-helmet")
async def detect_helmet(image: UploadFile = File(...)):
    if image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="File must be a JPEG or PNG image")

    file_extension = os.path.splitext(image.filename)[1] or ".jpg"
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(IMAGE_FOLDER, unique_filename)

    content = await image.read()
    with open(file_path, "wb") as f:
        f.write(content)

    task = celeryTask.detect_helmet.delay(file_path)
    return {"task_id": task.id, "file_path": file_path}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    The endpoint Telegram will send updates to.
    """
    # Parse the incoming JSON payload into an Update object
    req_json = await request.json()
    update = Update.de_json(req_json, ptb.bot)

    await ptb.process_update(update)

    # Acknowledge receipt to Telegram
    return Response(status_code=HTTPStatus.OK)