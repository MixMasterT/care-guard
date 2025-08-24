#!/usr/bin/env python
import sys
import warnings
import os
from pathlib import Path

from datetime import datetime
from dotenv import load_dotenv

from knowledge_base_crew.crew import KnowledgeBaseCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Load .env from project root
project_root = Path(__file__).parent.parent.parent.parent.parent
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from: {env_path}")
else:
    print(f"⚠️ No .env file found at: {env_path}")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'Post-operative cardiac monitoring and vital signs interpretation',
        'current_year': str(datetime.now().year),
        'research_topics': [
            'Live monitoring of patient vitals for cardiac patients',
            'Cardio post-operative recovery and complications to watch out for',
            'Normal and abnormal ranges by age for heartbeats-per-minute, pulse-strength, spo2, temperature, blood pressure and ecg-rhythm'
        ]
    }
    
    try:
        KnowledgeBaseCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "Post-operative cardiac monitoring and vital signs interpretation",
        'current_year': str(datetime.now().year),
        'research_topics': [
            'Live monitoring of patient vitals for cardiac patients',
            'Cardio post-operative recovery and complications to watch out for',
            'Normal and abnormal ranges by age for heartbeats-per-minute, pulse-strength, spo2, temperature, blood pressure and ecg-rhythm'
        ]
    }
    try:
        KnowledgeBaseCrew().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        KnowledgeBaseCrew().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "Post-operative cardiac monitoring and vital signs interpretation",
        "current_year": str(datetime.now().year),
        'research_topics': [
            'Live monitoring of patient vitals for cardiac patients',
            'Cardio post-operative recovery and complications to watch out for',
            'Normal and abnormal ranges by age for heartbeats-per-minute, pulse-strength, spo2, temperature, blood pressure and ecg-rhythm'
        ]
    }
    
    try:
        KnowledgeBaseCrew().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
