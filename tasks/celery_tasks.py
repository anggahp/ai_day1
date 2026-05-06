from tasks.celery_app import celery_app
from src.pelatihanindoprima.crews.content_crew.content_crew import ContentCrew
from src.pelatihanindoprima.crews.analisator.analisator import Analisator
from src.pelatihanindoprima.crews.ticket_analysis.ticket_analysis import TicketAnalysisCrew
from src.pelatihanindoprima.crews.solution_crew.solution_crew import SolutionCrew
from src.pelatihanindoprima.crews.file_analyzer.file_analyzer import FileAnalyzer
from src.pelatihanindoprima.crews.crew_anomali.crew_anomali import CrewAnomali
from src.pelatihanindoprima.crews.crew_prediksi.crew_prediksi import CrewPrediksi
from src.pelatihanindoprima.crews.helmet_detector.helmet_detector import HelmetDetector

import logging
import traceback

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="research")
def research(self, topic: str, location: str):
    self.update_state(state='RUNNING', meta={'current': f'start job for {topic} in {location}'})
    try:
        result = ContentCrew().crew().kickoff(inputs={"topic": topic, "location": location})
        return result.raw
    except Exception as e:
        logger.error(f"Task failed with error: {e}\n{traceback.format_exc()}")
        raise

@celery_app.task(bind=True, name="analyze_market")
def analyze_market(self, topic: str, location: str):
    self.update_state(state='RUNNING', meta={'current': f'Memulai analisis pasar {topic} di {location}'})
    try:
        result = Analisator().crew().kickoff(inputs={"topic": topic, "location": location})
        return result.raw
    except Exception as e:
        logger.error(f"Task analyze_market failed: {e}\n{traceback.format_exc()}")
        raise

@celery_app.task(bind=True, name="analyze_ticket")
def analyze_ticket(self, title: str, description: str):
    self.update_state(state='RUNNING', meta={'current': f'Menganalisis tiket: {title}'})
    try:
        crew = TicketAnalysisCrew()
        return crew.kickoff_and_parse(inputs={"title": title, "description": description})
    except Exception as e:
        logger.error(f"Task analyze_ticket failed: {e}\n{traceback.format_exc()}")
        raise

@celery_app.task(bind=True, name="generate_solution")
def generate_solution(self, issue_type: str, system: str):
    self.update_state(state='RUNNING', meta={'current': f'Membuat solusi untuk {issue_type} pada {system}'})
    try:
        crew = SolutionCrew()
        return crew.kickoff_and_parse(inputs={"issue_type": issue_type, "system": system})
    except Exception as e:
        logger.error(f"Task generate_solution failed: {e}\n{traceback.format_exc()}")
        raise

@celery_app.task(bind=True, name="file_analyzer")
def file_analyzer(self, file:str):
    self.update_state(state='RUNNING', meta={'current':f'start job for {file}'})
    try:
        result = FileAnalyzer().crew().kickoff(inputs = {"file": file})
        if result.json_dict:
            return result.json_dict
        import json, re
        raw = result.raw or ""
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        match = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return raw
    except Exception as e:
        logger.error(f"Task file_analyzer failed: {e}\n{traceback.format_exc()}")
        raise

@celery_app.task(bind=True, name="detect_anomalies")
def detect_anomalies(self, file:str):
    self.update_state(state='RUNNING', meta={'current':f'start job for crew anomali with file {file}'})
    try:
        result = CrewAnomali().crew().kickoff(inputs = {"file": file})
        if result.json_dict:
            return result.json_dict
        import json, re
        raw = result.raw or ""
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        match = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return raw
    except Exception as e:
        logger.error(f"Task detect_anomalies failed: {e}\n{traceback.format_exc()}")
        raise

@celery_app.task(bind=True, name="predict_sales")
def predict_sales(self, file:str):
    self.update_state(state='RUNNING', meta={'current':f'start job for crew prediksi with file {file}'})
    try:
        result = CrewPrediksi().crew().kickoff(inputs = {"file": file})
        return result.raw or ""
    except Exception as e:
        logger.error(f"Task predict_sales failed: {e}\n{traceback.format_exc()}")
        raise
    
@celery_app.task(bind=True, name="detect_helmet")
def detect_helmet(self, image:str):
    self.update_state(state='RUNNING', meta={'current':f'start job for{image}'})
    try:
        result = HelmetDetector().crew().kickoff(inputs = {"image": image})
        return str(result)
    except Exception as e:
        logger.error(f"Task detect_helmet failed: {e}\n{traceback.format_exc()}")
        raise