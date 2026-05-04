import json
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class TicketAnalysisCrew():
    """Crew 1 — Ticket Analysis: Analyzer + Classifier"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # ── AGENTS ────────────────────────────────────────────────────────────────

    @agent
    def ticket_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['ticket_analyzer'],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def ticket_classifier(self) -> Agent:
        return Agent(
            config=self.agents_config['ticket_classifier'],  # type: ignore[index]
            verbose=True,
        )

    # ── TASKS ─────────────────────────────────────────────────────────────────

    @task
    def analyze_ticket_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_ticket_task'],  # type: ignore[index]
        )

    @task
    def classify_issue_task(self) -> Task:
        return Task(
            config=self.tasks_config['classify_issue_task'],  # type: ignore[index]
        )

    # ── CREW ──────────────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the Ticket Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    def kickoff_and_parse(self, inputs: dict) -> dict:
        """Jalankan crew dan parse output JSON dari classifier."""
        result = self.crew().kickoff(inputs=inputs)
        raw = result.raw.strip()
        # Bersihkan markdown code block jika ada
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "category": "Unknown",
                "technical_area": "Unknown",
                "summary": raw,
            }
