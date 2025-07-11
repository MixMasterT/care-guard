from langgraph.graph import StateGraph, START, END
from langgraph_agents.agents.heartbeat_classification import (
    AgentState,
    load_heartbeat_data,
    analyze_heartbeat_data,
    classify_heartbeat,
)
from dotenv import load_dotenv
import os

def load_data(state: AgentState) -> AgentState:
    """Load heartbeat data from buffer file."""
    try:
        heartbeat_data = load_heartbeat_data()
        return {**state, "heartbeat_data": heartbeat_data, "error": None}
    except Exception as e:
        return {**state, "error": f"Failed to load heartbeat data: {e}"}

def analyze_data(state: AgentState) -> AgentState:
    """Analyze the heartbeat data."""
    if state.get("error"):
        return state
    try:
        analysis = analyze_heartbeat_data(state["heartbeat_data"])
        return {**state, "analysis": analysis, "error": None}
    except Exception as e:
        return {**state, "error": f"Failed to analyze heartbeat data: {e}"}

def classify_data(state: AgentState) -> AgentState:
    """Classify the heartbeat pattern."""
    if state.get("error") or not state.get("analysis"):
        return state
    try:
        analysis = state["analysis"]
        if analysis is None:
            return {**state, "error": "No analysis data available"}
        classification = classify_heartbeat(analysis)
        return {**state, "classification": classification, "error": None}
    except Exception as e:
        return {**state, "error": f"Failed to classify heartbeat: {e}"}

def should_continue(state: AgentState) -> str:
    """Determine if we should continue processing or end due to error."""
    if state.get("error"):
        return "end"
    return "continue"

def create_heartbeat_classification_graph():
    """Create the heartbeat classification workflow."""
    workflow = StateGraph(AgentState)
    # Add nodes
    workflow.add_node("load_data", load_data)
    workflow.add_node("analyze_data", analyze_data)
    workflow.add_node("classify_data", classify_data)
    # Add edges
    workflow.add_edge(START, "load_data")
    workflow.add_edge("load_data", "analyze_data")
    workflow.add_edge("analyze_data", "classify_data")
    workflow.add_edge("classify_data", END)
    return workflow.compile()

def run_heartbeat_classification():
    """Run the heartbeat classification workflow."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set. Using rule-based classification only.")
        print("   💡 Create a .env file with: OPENAI_API_KEY=your-api-key-here")
    app = create_heartbeat_classification_graph()
    initial_state: AgentState = {
        "heartbeat_data": [],
        "analysis": None,
        "classification": None,
        "error": None
    }
    result = app.invoke(initial_state)
    return result 