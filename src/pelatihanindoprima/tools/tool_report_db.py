from typing import Type
from pydantic import BaseModel, Field, ConfigDict
from crewai.tools import BaseTool
from typing import Optional
from src.pelatihanindoprima.tools.database import get_db_connection

class tool_report_db_input(BaseModel):
    head: int = Field(..., description="count of head detected")
    person: int = Field(..., description="count of person detected")
    helmet: int = Field(..., description="count of helmet detected")

class Tool_report(BaseTool):
    name: str = "tools report ke db"
    description: str = "Store detection results to database for record keeping"
    args_schema : Type[BaseModel] = tool_report_db_input

    def _run(self, head:int, person:int, helmet:int) -> str:
        try:
            connec = get_db_connection()
            cursor = connec.cursor()
            if (head > 0):
                detil = f"{head} heads, {helmet} helmets, and {person} persons"
                query = "INSERT INTO helmet_report (report_result, report_detected) VALUES (%s, %s)"
                cursor.execute(query, (detil, head))
                connec.commit()

                cursor.close()
                connec.close()
                return ("stored to db")
            else:
                return ("report that everybody is safe")
        except Exception as e:
            raise(Exception(e))