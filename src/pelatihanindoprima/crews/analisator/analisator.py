from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent


@CrewBase
class Analisator():
    """Analisator crew — Analisis Pasar Profesional"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # ── AGENTS ────────────────────────────────────────────────────────────────

    @agent
    def market_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['market_researcher'],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def competitive_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['competitive_analyst'],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def consumer_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['consumer_analyst'],  # type: ignore[index]
            verbose=True,
        )

    @agent
    def strategic_advisor(self) -> Agent:
        return Agent(
            config=self.agents_config['strategic_advisor'],  # type: ignore[index]
            verbose=True,
        )

    # ── TASKS ─────────────────────────────────────────────────────────────────

    @task
    def market_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['market_research_task'],  # type: ignore[index]
        )

    @task
    def competitive_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['competitive_analysis_task'],  # type: ignore[index]
        )

    @task
    def consumer_analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['consumer_analysis_task'],  # type: ignore[index]
        )

    @task
    def strategic_recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config['strategic_recommendation_task'],  # type: ignore[index]
        )

    # ── CREW ──────────────────────────────────────────────────────────────────

    @crew
    def crew(self) -> Crew:
        """Creates the Analisator crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
