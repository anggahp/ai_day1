import json
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class SolutionCrew():
    """Crew 2 — Solution: Troubleshooter + Documentation"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # ── AGENTS ────────────────────────────────────────────────────────────────

    @agent
    def solution_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['solution_agent'],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def documentation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['documentation_agent'],  # type: ignore[index]
            verbose=True,
        )

    # ── TASKS ─────────────────────────────────────────────────────────────────

    @task
    def generate_solution_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_solution_task'],  # type: ignore[index]
        )

    @task
    def create_documentation_task(self) -> Task:
        return Task(
            config=self.tasks_config['create_documentation_task'],  # type: ignore[index]
        )

    # ── CREW ──────────────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the Solution crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    def kickoff_and_parse(self, inputs: dict) -> dict:
        """Jalankan crew dan parse output JSON dari documentation agent."""
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
                "solution": [raw],
                "documentation": raw,
            }
