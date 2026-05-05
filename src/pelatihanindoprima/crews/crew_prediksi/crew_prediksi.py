from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from src.pelatihanindoprima.tools.tool_prediksi import tool_prediksi

@CrewBase
class CrewPrediksi():
    """CrewPrediksi crew for sales forecasting"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def prediksi_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['prediksi_agent'], # type: ignore[index]
            tools=[tool_prediksi()],
            verbose=True
        )

    @task
    def prediksi_task(self) -> Task:
        return Task(
            config=self.tasks_config['prediksi_task'], # type: ignore[index]
            output_file="output/output_prediksi.md"
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CrewPrediksi crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
