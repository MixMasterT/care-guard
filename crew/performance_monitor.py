#!/usr/bin/env python3
"""
Performance monitoring system for framework comparison.
Tracks speed, cost, and result quality across different agentic frameworks.
"""

import time
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class PerformanceMetrics:
    """Performance metrics for framework comparison."""
    framework: str
    task_type: str
    start_time: float
    end_time: float
    duration_seconds: float
    token_count: Optional[int] = None
    cost_usd: Optional[float] = None
    result_quality_score: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class PerformanceMonitor:
    """Monitor and track performance across different frameworks."""
    
    def __init__(self, output_dir: str = "performance_logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.current_session = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def start_timer(self) -> float:
        """Start timing a task."""
        return time.time()
    
    def end_timer(self, start_time: float) -> float:
        """End timing and return duration."""
        return time.time() - start_time
    
    def log_performance(self, metrics: PerformanceMetrics):
        """Log performance metrics to file."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "session": self.current_session,
            **asdict(metrics)
        }
        
        # Save to session-specific file
        session_file = self.output_dir / f"session_{self.current_session}.jsonl"
        with open(session_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Save to framework-specific summary
        framework_file = self.output_dir / f"{metrics.framework}_summary.jsonl"
        with open(framework_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_framework_summary(self, framework: str) -> Dict[str, Any]:
        """Get performance summary for a specific framework."""
        framework_file = self.output_dir / f"{framework}_summary.jsonl"
        
        if not framework_file.exists():
            return {"error": f"No data found for framework: {framework}"}
        
        metrics_list = []
        with open(framework_file, 'r') as f:
            for line in f:
                metrics_list.append(json.loads(line.strip()))
        
        if not metrics_list:
            return {"error": "No metrics found"}
        
        # Calculate summary statistics
        durations = [m['duration_seconds'] for m in metrics_list if m['success']]
        costs = [m['cost_usd'] for m in metrics_list if m['cost_usd'] is not None]
        quality_scores = [m['result_quality_score'] for m in metrics_list if m['result_quality_score'] is not None]
        
        summary = {
            "framework": framework,
            "total_tasks": len(metrics_list),
            "successful_tasks": len([m for m in metrics_list if m['success']]),
            "success_rate": len([m for m in metrics_list if m['success']]) / len(metrics_list) * 100,
            "avg_duration_seconds": sum(durations) / len(durations) if durations else 0,
            "min_duration_seconds": min(durations) if durations else 0,
            "max_duration_seconds": max(durations) if durations else 0,
            "total_cost_usd": sum(costs) if costs else 0,
            "avg_cost_usd": sum(costs) / len(costs) if costs else 0,
            "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "recent_tasks": metrics_list[-5:]  # Last 5 tasks
        }
        
        return summary
    
    def compare_frameworks(self, frameworks: List[str]) -> Dict[str, Any]:
        """Compare performance across multiple frameworks."""
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "frameworks": {}
        }
        
        for framework in frameworks:
            comparison["frameworks"][framework] = self.get_framework_summary(framework)
        
        # Calculate relative performance
        if len(frameworks) > 1:
            comparison["relative_performance"] = self._calculate_relative_performance(comparison["frameworks"])
        
        return comparison
    
    def _calculate_relative_performance(self, framework_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate relative performance metrics."""
        # Find best performers in each category
        best_speed = min(framework_data.items(), 
                        key=lambda x: x[1].get('avg_duration_seconds', float('inf')))
        best_cost = min(framework_data.items(), 
                       key=lambda x: x[1].get('avg_cost_usd', float('inf')))
        best_quality = max(framework_data.items(), 
                          key=lambda x: x[1].get('avg_quality_score', 0))
        
        return {
            "fastest": best_speed[0],
            "most_cost_effective": best_cost[0],
            "highest_quality": best_quality[0]
        }
    
    def export_comparison_report(self, frameworks: List[str], output_file: str = None):
        """Export a comprehensive comparison report."""
        if output_file is None:
            output_file = self.output_dir / f"comparison_report_{self.current_session}.json"
        
        comparison = self.compare_frameworks(frameworks)
        
        with open(output_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        return output_file

# Context manager for easy performance tracking
class PerformanceTracker:
    """Context manager for tracking performance metrics."""
    
    def __init__(self, monitor: PerformanceMonitor, framework: str, task_type: str):
        self.monitor = monitor
        self.framework = framework
        self.task_type = task_type
        self.start_time = None
        self.metrics = None
    
    def __enter__(self):
        self.start_time = self.monitor.start_timer()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = self.monitor.end_timer(self.start_time)
        
        self.metrics = PerformanceMetrics(
            framework=self.framework,
            task_type=self.task_type,
            start_time=self.start_time,
            end_time=time.time(),
            duration_seconds=duration,
            success=exc_type is None,
            error_message=str(exc_val) if exc_val else None
        )
        
        self.monitor.log_performance(self.metrics)
    
    def add_metrics(self, token_count: int = None, cost_usd: float = None, 
                   quality_score: float = None, metadata: Dict[str, Any] = None):
        """Add additional metrics after task completion."""
        if self.metrics:
            if token_count is not None:
                self.metrics.token_count = token_count
            if cost_usd is not None:
                self.metrics.cost_usd = cost_usd
            if quality_score is not None:
                self.metrics.result_quality_score = quality_score
            if metadata is not None:
                self.metrics.metadata = metadata
            
            self.monitor.log_performance(self.metrics)

# Example usage
if __name__ == "__main__":
    monitor = PerformanceMonitor()
    
    # Example: Track a task
    with PerformanceTracker(monitor, "crewai", "patient_assessment") as tracker:
        # Simulate some work
        time.sleep(1)
        
        # Add additional metrics
        tracker.add_metrics(
            token_count=1500,
            cost_usd=0.03,
            quality_score=0.85,
            metadata={"patient_id": "123", "severity": "normal"}
        )
    
    # Get summary
    summary = monitor.get_framework_summary("crewai")
    print("CrewAI Performance Summary:")
    print(json.dumps(summary, indent=2)) 