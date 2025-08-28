from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import FileReadTool, RagTool
from opensearchpy import OpenSearch
from typing import List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import sys
from pathlib import Path

# Add the agentic_types directory to the path
workspace_root = Path.cwd()  # Use current working directory
agentic_types_dir = workspace_root / "agentic_types"
sys.path.insert(0, str(agentic_types_dir))

# Import our Pydantic models for structured output
from models import (
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

# Define the input schema for the medical knowledge tool
class MedicalKnowledgeInput(BaseModel):
    query: str = Field(description="The medical question or topic to search for in the knowledge base")

# Create a proper CrewAI tool wrapper for the RAG tool
class MedicalKnowledgeTool(BaseTool):
    name: str = "Medical Knowledge Base"
    description: str = "Access to medical research articles and clinical guidelines. Use this tool to search for medical information by asking a question."
    args_schema: type[BaseModel] = MedicalKnowledgeInput
    
    def __init__(self, rag_tool: RagTool):
        super().__init__()
        # Store rag_tool after calling super().__init__()
        self._rag_tool = rag_tool
    
    def _run(self, query: str) -> str:
        """Execute the tool with the given query"""
        try:
            # Use the stored RAG tool to get the answer
            if hasattr(self, '_rag_tool') and self._rag_tool:
                result = self._rag_tool.run(query)
                return result
            else:
                return "Error: Medical knowledge base not properly initialized"
        except Exception as e:
            return f"Error accessing medical knowledge base: {str(e)}"

# Initialize RAG tool with medical knowledge base articles
def initialize_medical_rag_tool():
    """Initialize RAG tool with all medical articles from OpenSearch"""
    try:
        # Check if OPENAI_API_KEY is available
        import os
        if not os.environ.get('OPENAI_API_KEY'):
            print("Warning: OPENAI_API_KEY not set, skipping RAG tool initialization")
            return None
        
        # Connect to OpenSearch
        client = OpenSearch(hosts=[{'host': 'localhost', 'port': 9200}])
        
        # Search for all medical articles
        response = client.search(
            index="medical-knowledge-base",
            body={
                "query": {"match_all": {}},
                "size": 1000  # Get all articles
            }
        )
        
        # Create RAG tool instance
        rag_tool = RagTool(
            name="Medical Knowledge Base",
            description="Access to medical research articles and clinical guidelines. Use this tool to search for medical information by asking a question."
        )
        
        # Add each article URL to the RAG tool
        added_count = 0
        for hit in response['hits']['hits']:
            source = hit['_source']
            url = source.get('url')
            if url:
                try:
                    rag_tool.add(url, data_type="web_page")
                    added_count += 1
                except Exception as add_error:
                    print(f"Warning: Could not add URL {url}: {add_error}")
                    continue
        
        print(f"✅ RAG tool initialized with {added_count} medical articles")
        
        # Wrap the RAG tool in our CrewAI-compatible wrapper
        medical_tool = MedicalKnowledgeTool(rag_tool)
        return medical_tool
        
    except Exception as e:
        print(f"Warning: Could not initialize RAG tool: {e}")
        return None

# Initialize the RAG tool
medical_rag_tool = initialize_medical_rag_tool()

@CrewBase
class CardioMonitor():
    """CardioMonitor crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def biometric_reviewer(self, biometric_buffer_path: str = None) -> Agent:
        """Creates the biometric reviewer agent"""
        tools = []
        
        # Add medical knowledge RAG tool if available
        if medical_rag_tool:
            tools.append(medical_rag_tool)
        
        # Add FileReadTool for biometric data if path is provided
        if biometric_buffer_path:
            from crewai_tools import FileReadTool
            file_tool = FileReadTool(
                file_path=biometric_buffer_path,
                description="Read the entire biometric data file to analyze all available biometric metrics including heart rate, SpO2, temperature, blood pressure, respiration, and ECG rhythm data. IMPORTANT: Read the COMPLETE file, not just the first few lines. Use start_line=1 and line_count=1000 or higher to ensure you get all the data.",
                start_line=1,
                line_count=10000  # Ensure we read the entire file
            )
            tools.append(file_tool)
        
        return Agent(
            config=self.agents_config['biometric_reviewer'], # type: ignore[index]
            tools=tools,
            verbose=True
        )

    @agent
    def triage_nurse(self, pain_diary_path: str = None, weight_data_path: str = None) -> Agent:
        """Creates the triage nurse agent"""
        tools = []
        
        # Add medical knowledge RAG tool if available
        if medical_rag_tool:
            tools.append(medical_rag_tool)
        
        # Add FileReadTool for pain diary if path is provided
        if pain_diary_path:
            from crewai_tools import FileReadTool
            pain_tool = FileReadTool(
                file_path=pain_diary_path,
                description="Read the entire pain diary file to analyze patient-reported symptoms and pain levels over time. IMPORTANT: Read the COMPLETE file, not just the first few lines.",
                start_line=1,
                line_count=10000  # Ensure we read the entire file
            )
            tools.append(pain_tool)
        
        # Add FileReadTool for weight data if path is provided
        if weight_data_path:
            from crewai_tools import FileReadTool
            weight_tool = FileReadTool(
                file_path=weight_data_path,
                description="Read the entire weight data file to analyze weight trends and changes over time. IMPORTANT: Read the COMPLETE file, not just the first few lines.",
                start_line=1,
                line_count=10000  # Ensure we read the entire file
            )
            tools.append(weight_tool)
        
        return Agent(
            config=self.agents_config['triage_nurse'], # type: ignore[index]
            tools=tools,
            allow_delegation=False,
            verbose=True
        )

    @agent
    def log_writer(self, pain_diary_path: str = None, weight_data_path: str = None) -> Agent:
        """Creates the log writer agent"""
        tools = []
        
        # Add FileReadTool for pain diary if path is provided
        if pain_diary_path:
            from crewai_tools import FileReadTool
            pain_tool = FileReadTool(
                file_path=pain_diary_path,
                description="Read the entire pain diary file to analyze patient-reported symptoms and pain levels over time. IMPORTANT: Read the COMPLETE file, not just the first few lines.",
                start_line=1,
                line_count=10000  # Ensure we read the entire file
            )
            tools.append(pain_tool)
        
        # Add FileReadTool for weight data if path is provided
        if weight_data_path:
            from crewai_tools import FileReadTool
            weight_tool = FileReadTool(
                file_path=weight_data_path,
                description="Read the entire weight data file to analyze weight trends and changes over time. IMPORTANT: Read the COMPLETE file, not just the first few lines.",
                start_line=1,
                line_count=10000  # Ensure we read the entire file
            )
            tools.append(weight_tool)
        
        return Agent(
            config=self.agents_config['log_writer'], # type: ignore[index]
            tools=tools,
            verbose=True
        )

    @task
    def review_biometrics(self, biometric_buffer_path: str = None) -> Task:
        return Task(
            config=self.tasks_config['review_biometrics'],
            agent=self.biometric_reviewer(biometric_buffer_path=biometric_buffer_path),
            output_pydantic=TrendInsightPayload,
            output_file='patient/agentic_monitor_logs/{timestamp}_{patient_name}_biometric_analysis.json'
        )

    @task
    def analyze_patient_status(self, pain_diary_path: str = None, weight_data_path: str = None) -> Task:
        return Task(
            config=self.tasks_config['analyze_patient_status'],
            agent=self.triage_nurse(pain_diary_path=pain_diary_path, weight_data_path=weight_data_path),
            output_pydantic=DecisionPayload,
            output_file='patient/agentic_monitor_logs/{timestamp}_{patient_name}_triage_decision.json'
        )

    @task
    def create_medical_log(self, pain_diary_path: str = None, weight_data_path: str = None) -> Task:
        return Task(
            config=self.tasks_config['create_medical_log'],
            agent=self.log_writer(pain_diary_path=pain_diary_path, weight_data_path=weight_data_path),
            output_pydantic=AgenticFinalOutput,
            output_file='patient/agentic_monitor_logs/{timestamp}_{patient_name}_medical_log.json'
        )

    @crew
    def crew(self, biometric_buffer_path: str = None, pain_diary_path: str = None, weight_data_path: str = None) -> Crew:
        """Creates the CardioMonitor crew"""
        # Create tasks in the correct order for sequential execution
        ordered_tasks = [
            self.review_biometrics(biometric_buffer_path=biometric_buffer_path),
            self.analyze_patient_status(pain_diary_path=pain_diary_path, weight_data_path=weight_data_path),
            self.create_medical_log(pain_diary_path=pain_diary_path, weight_data_path=weight_data_path),
        ]

        # Create agents with FileReadTools using the provided file paths
        biometric_agent = self.biometric_reviewer(biometric_buffer_path=biometric_buffer_path)
        triage_agent = self.triage_nurse(pain_diary_path=pain_diary_path, weight_data_path=weight_data_path)
        log_agent = self.log_writer(pain_diary_path=pain_diary_path, weight_data_path=weight_data_path)
        
        ordered_agents = [biometric_agent, triage_agent, log_agent]
        
        print(f"🤖 Crew created with {len(ordered_agents)} agents and {len(ordered_tasks)} tasks")
        
        crew_instance = Crew(
            agents=ordered_agents,
            tasks=ordered_tasks,
            process=Process.sequential,
            verbose=True,
            memory=False
        )
        
        return crew_instance
