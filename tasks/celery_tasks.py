from tasks.celery_app import celery_app
from src.pelatihanindoprima.crews.content_crew.content_crew import ContentCrew
from src.pelatihanindoprima.crews.analisator.analisator import Analisator
from src.pelatihanindoprima.crews.ticket_analysis.ticket_analysis import TicketAnalysisCrew
from src.pelatihanindoprima.crews.solution_crew.solution_crew import SolutionCrew
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