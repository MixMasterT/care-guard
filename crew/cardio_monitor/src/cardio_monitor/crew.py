from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import FileReadTool
from typing import List

# Import our Pydantic models for structured output
from agentic_types.models import (
    Finding,
    Recommendation,
    DecisionPayload,
    ConfidenceLevel,
    ConfidenceLevelEvidence,
    AgenticFinalOutput,
    PatientIdentity,
    ExecutionMetrics,
    Artifacts,
    TrendInsightPayload
)

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class CardioMonitor():
    """CardioMonitor crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def triage_nurse(self, pain_diary_path: str = None, weight_data_path: str = None) -> Agent:
        """Creates the triage nurse agent"""
        tools = []
        if pain_diary_path:
            tools.append(FileReadTool(file_path=pain_diary_path))
        if weight_data_path:
            tools.append(FileReadTool(file_path=weight_data_path))
        
        return Agent(
            config=self.agents_config['triage_nurse'], # type: ignore[index]
            tools=tools,
            allow_delegation=False,  # Temporarily disable delegation due to tool validation issues
            verbose=True
        )

    @agent
    def log_writer(self, biometric_buffer_path: str = None, pain_diary_path: str = None, weight_data_path: str = None) -> Agent:
        """Creates the log writer agent"""
        tools = []
        if biometric_buffer_path:
            tools.append(FileReadTool(file_path=biometric_buffer_path))
        if pain_diary_path:
            tools.append(FileReadTool(file_path=pain_diary_path))
        if weight_data_path:
            tools.append(FileReadTool(file_path=weight_data_path))
        
        return Agent(
            config=self.agents_config['log_writer'], # type: ignore[index]
            tools=tools,
            verbose=True
        )

    @agent
    def biometric_reviewer(self, biometric_buffer_path: str = None) -> Agent:
        """Creates the biometric reviewer agent"""
        tools = []
        if biometric_buffer_path:
            print(f"The biometric_buffer_path was passed in as: {biometric_buffer_path}")
            tools.append(FileReadTool(file_path=biometric_buffer_path))
        else:
            print("-----------NO biometric_buffer_path WAS PASSED IN ----------------")
        return Agent(
            config=self.agents_config['biometric_reviewer'], # type: ignore[index]
            tools=tools,
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def analyze_patient_status(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_patient_status'], # type: ignore[index]
            expected_output="""Analyze patient status and produce structured output with triage decision, findings, and recommendations.
            
            CRITICAL: Use the biometric analysis from the biometric_reviewer to inform your triage decision.
            Pay special attention to:
            - risk_assessment: If "high" or "critical", this MUST influence your priority
            - requires_attention: If true, this indicates urgent care needs
            - immediate_concerns: Address each concern in your rationale
            - recommendations: Incorporate biometric recommendations into your follow-ups
            
            The output should contain:
            - A priority value of "High", "Medium", or "Low" (escalate if biometrics show risk)
            - A next action that describes the immediate next step in patient care
            - A summary describing the patient's overall condition at this time
            - A rationale that describes why the priority value was assigned (include biometric factors)
            - A list of follow-ups which would be a list of strings describing actions that should be taken in the future
            for best outcomes. Each item in the list should include the number of days after which to do the follow-up action
            
            EMERGENCY ESCALATION:
            - If biometrics show "critical" risk → priority MUST be "High" or "Immediate"
            - If biometrics require_attention → next action MUST address the concern
            - If biometrics show "high" risk → consider escalating priority
            
            Be concise and actionable. Focus on medical insights that inform care decisions.""",
            agent=self.triage_nurse(),
            output_pydantic=DecisionPayload,
            context=[self.review_biometrics()],  # Gets biometric analysis as context
            output_file='patient/agentic_monitor_logs/{timestamp}_{run_id}_{patient_name}_triage_decision.json'
        )

    @task
    def create_medical_log(self) -> Task:
        return Task(
            config=self.tasks_config['create_medical_log'], # type: ignore[index]
            expected_output="""Create the final medical log entry based on the triage nurse's analysis and recommendations.

            The JSON must contain triage_decision, findings, and recommendations that match the OUTPUT_FORMAT.md specification.
            
            IMPORTANT: Set the framework field to "crewai" (not "unknown").

            Keep content concise and actionable. Do not dump raw data or long transcripts.

            Use the triage decision from the triage_nurse to create the final medical log.""",
            agent=self.log_writer(),
            output_pydantic=AgenticFinalOutput,
            context=[self.analyze_patient_status()],  # Gets triage analysis as context
            output_file='patient/agentic_monitor_logs/{timestamp}_{run_id}_{patient_name}_medical_log.json'
        )

    @task
    def review_biometrics(self, biometric_buffer_path: str = None) -> Task:
        return Task(
            config=self.tasks_config['review_biometrics'],
            expected_output="""Provide a comprehensive, actionable analysis of biometric data that directly informs patient care decisions.

            CRITICAL REQUIREMENTS:
            1. ALWAYS analyze the actual biometric data file using FileReadTool
            2. Provide specific, measurable insights (exact values, ranges, trends)
            3. Identify ANY concerning patterns that require immediate attention
            4. Generate actionable recommendations based on the data

            REQUIRED OUTPUT STRUCTURE:
            - metric: The primary biometric being analyzed (heart_rate, spo2, blood_pressure, etc.)
            - description: Clear summary of what the data shows
            - window: Time period analyzed (e.g., "Last 30 minutes", "Last 2 hours")
            - stats: Detailed statistics including averages, ranges, min/max values, trends
            - risk_assessment: "low", "moderate", "high", or "critical" based on data
            - immediate_concerns: List of specific issues found (e.g., ["bradycardia < 50 bpm", "hypoxemia < 90%"])
            - recommendations: List of specific actions needed (e.g., ["check patient immediately", "contact physician", "increase monitoring frequency"])
            - requires_attention: true if ANY concerning patterns are detected
            - next_action: The immediate next step for the care team

            RISK ASSESSMENT GUIDELINES:
            - LOW: All values within normal ranges, stable trends
            - MODERATE: Some values outside normal ranges, minor fluctuations
            - HIGH: Multiple values outside normal ranges, concerning trends, requires monitoring
            - CRITICAL: Values in dangerous ranges, rapid changes, requires immediate intervention

            EMERGENCY FLAGS:
            - Heart rate < 50 or > 120 bpm → requires_attention = true, risk_assessment = "critical"
            - SpO2 < 90% → requires_attention = true, risk_assessment = "critical"  
            - Blood pressure < 90/60 or > 180/110 → requires_attention = true, risk_assessment = "high"
            - Any rapid deterioration → requires_attention = true, risk_assessment = "critical"

            This analysis directly impacts patient safety - be thorough and actionable.""",
            agent=self.biometric_reviewer(biometric_buffer_path=biometric_buffer_path),
            output_pydantic=TrendInsightPayload,
            output_file='patient/agentic_monitor_logs/{timestamp}_{run_id}_{patient_name}_biometric_analysis.json'
        )

    @crew
    def crew(self, biometric_buffer_path: str = None, pain_diary_path: str = None, weight_data_path: str = None) -> Crew:
        """Creates the CardioMonitor crew"""
        # Store paths for use in tasks
        self.biometric_buffer_path = biometric_buffer_path
        self.pain_diary_path = pain_diary_path
        self.weight_data_path = weight_data_path
        
        ordered_tasks = [
            self.review_biometrics(biometric_buffer_path=biometric_buffer_path),  # First: analyze biometrics
            self.analyze_patient_status(),  # Second: use biometric insights for triage decision
            self.create_medical_log(),  # Third: create final medical log with all data
        ]

        ordered_agents = [
            self.biometric_reviewer(biometric_buffer_path=biometric_buffer_path),
            self.triage_nurse(pain_diary_path=pain_diary_path, weight_data_path=weight_data_path),
            self.log_writer(biometric_buffer_path=biometric_buffer_path, pain_diary_path=pain_diary_path, weight_data_path=weight_data_path),
        ]

        print(f"🤖 Crew created with {len(ordered_agents)} agents and {len(ordered_tasks)} tasks")
        print(f"📋 Task order:")
        for i, task in enumerate(ordered_tasks, 1):
            print(f"   {i}. {task.agent.role} → {task.description[:50]}...")
        
        return Crew(
            agents=ordered_agents,
            tasks=ordered_tasks,
            process=Process.sequential,
            verbose=True,
            memory=False  # Disable memory to ensure fresh analysis each time
        )
