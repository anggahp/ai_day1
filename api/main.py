from celery.result import AsyncResult
from tasks.celery_app import celery_app
from fastapi import FastAPI
from pydantic import BaseModel
import tasks.celery_tasks as celeryTask

app = FastAPI(title="IT Support Automation API")


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