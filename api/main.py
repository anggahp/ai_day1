from celery.result import AsyncResult
from tasks.celery_app import celery_app
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel
import tasks.celery_tasks as celeryTask
import os
import uuid

app = FastAPI(title="IT Support Automation API")

FILE_FOLDER = "uploads"
IMAGE_FOLDER = "images"
os.makedirs(FILE_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

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