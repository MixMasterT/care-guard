"""
Integrations package for agentic monitoring frameworks.
"""

from .base_integration import BaseIntegration
from .crewai_integration import CrewaiIntegration
from .langgraph_integration import LangGraphIntegration

# Export all available integrations
__all__ = [
    "BaseIntegration",
    "CrewaiIntegration",
    "LangGraphIntegration",
]

# Framework registry - maps framework names to integration classes
FRAMEWORK_REGISTRY = {
    "crewai": CrewaiIntegration,
    "Crewai": CrewaiIntegration,  # Handle both lowercase and title case
    "langgraph": LangGraphIntegration,
    "Langgraph": LangGraphIntegration,
    "LangGraph": LangGraphIntegration,
}

def get_integration(framework: str) -> BaseIntegration:
    """
    Get an integration instance for the specified framework.
    
    Args:
        framework: Framework name (e.g., "crewai", "Crewai")
        
    Returns:
        Integration instance
        
    Raises:
        ValueError: If framework is not supported
    """
    if framework not in FRAMEWORK_REGISTRY:
        available = ", ".join(FRAMEWORK_REGISTRY.keys())
        raise ValueError(f"Unsupported framework: {framework}. Available frameworks: {available}")
    
    integration_class = FRAMEWORK_REGISTRY[framework]
    return integration_class()
