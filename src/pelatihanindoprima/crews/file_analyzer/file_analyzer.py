from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from pydantic import BaseModel
from typing import List
from src.pelatihanindoprima.crews.file_analyzer.tools.file_reader_tool import FileReaderTool

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class FileAnalyzer():
    """FileAnalyzer crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    fileRead = FileReaderTool()

    class InsightItem(BaseModel):
        insight: str
        indikator: str

    class Output_file_analyzer(BaseModel):
        results: List['FileAnalyzer.InsightItem']

    @agent
    def agent_file_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['agent_file_analyzer'], # type: ignore[index]
            verbose=True,
            tools=[self.fileRead]
        )

    @task
    def task_file_analyzer(self) -> Task:
        return Task(
            config=self.tasks_config['task_file_analyzer'], # type: ignore[index]
            output_json=self.Output_file_analyzer,
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CrewRag crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
