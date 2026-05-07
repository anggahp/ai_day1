from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from src.pelatihanindoprima.tools.tool_helmet_detection import ToolHelmetDetection
from src.pelatihanindoprima.tools.tool_report_db import tool_report_db_input, Tool_report
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class HelmetDetector():
    """HelmetDetector crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def helmet_detector(self) -> Agent:
        return Agent(
            config=self.agents_config['helmet_detector'], # type: ignore[index]
            verbose=True,
            tools= [ToolHelmetDetection(), Tool_report()]
            # tools= [ToolHelmetDetection()]
        )

    # @agent
    # def database_reporter(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['database_reporter'], # type: ignore[index]
    #         verbose=True,
    #         tools= [Tool_report()]
    #     )

    @task
    def helmet_detector_task(self) -> Task:
        return Task(
            config=self.tasks_config['helmet_detector_task'], # type: ignore[index]
            output_json = tool_report_db_input
        )

    # @task
    # def database_reporting_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['database_reporting_task'], # type: ignore[index]
    #         context = [self.helmet_detector_task()]
    #     )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task

    @crew
    def crew(self) -> Crew:
        """Creates the HelmetDetector crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
