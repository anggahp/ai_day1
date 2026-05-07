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
import os
import httpx
import json

logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")

def send_telegram_notification(chat_id, text, title="Hasil Task"):
    if not chat_id or not TOKEN:
        return
    
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Header message
    header = f"✅ **{title} Selesai!**\n\n"
    
    # Chunking message for Telegram (limit is 4096)
    chunk_size = 3500
    full_text = header + text
    
    for i in range(0, len(full_text), chunk_size):
        chunk = full_text[i:i+chunk_size]
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        try:
            httpx.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

@celery_app.task(bind=True, name="research")
def research(self, topic: str, location: str, chat_id: int = None):
    self.update_state(state='RUNNING', meta={'current': f'start job for {topic} in {location}'})
    try:
        result = ContentCrew().crew().kickoff(inputs={"topic": topic, "location": location})
        raw_result = result.raw
        
        if chat_id:
            send_telegram_notification(chat_id, raw_result, title=f"Riset: {topic}")
            
        return raw_result
    except Exception as e:
        logger.error(f"Task failed with error: {e}\n{traceback.format_exc()}")
        if chat_id:
            send_telegram_notification(chat_id, f"Maaf, terjadi kesalahan saat melakukan riset: {str(e)}", title="Error Riset")
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
def detect_helmet(self, image:str, chat_id: int = None):
    self.update_state(state='RUNNING', meta={'current':f'start job for{image}'})
    try:
        result = HelmetDetector().crew().kickoff(inputs = {"image": image})
        res_str = str(result)
        
        if chat_id:
            send_telegram_notification(chat_id, res_str, title="Deteksi Helm")
            
        return res_str
    except Exception as e:
        logger.error(f"Task detect_helmet failed: {e}\n{traceback.format_exc()}")
        if chat_id:
            send_telegram_notification(chat_id, f"Gagal mendeteksi helm: {str(e)}", title="Error Deteksi")
        raise