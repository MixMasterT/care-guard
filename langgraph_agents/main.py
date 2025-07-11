from langgraph_agents.workflows.heartbeat_workflow import run_heartbeat_classification

def main():
    print("🏥 Heartbeat Classification Agent")
    print("=" * 50)
    try:
        result = run_heartbeat_classification()
        if result.get("error"):
            print(f"Error: {result['error']}")
            return
        if result.get("classification"):
            classification = result["classification"]
            analysis = result["analysis"]
            print(f"📊 Analysis Results:")
            print(f"   Total heartbeats: {analysis.total_heartbeats}")
            print(f"   Average heart rate: {analysis.avg_heart_rate_bpm} BPM")
            print(f"   Min heart rate: {analysis.min_heart_rate_bpm} BPM")
            print(f"   Max heart rate: {analysis.max_heart_rate_bpm} BPM")
            print(f"   Heart rate variability: {analysis.heart_rate_variability}")
            print(f"   Duration: {analysis.duration_seconds} seconds")
            print()
            print(f"🔍 Classification: {classification.classification.upper()}")
            print(f"   Confidence: {classification.confidence:.1%}")
            print(f"   Reasoning: {classification.reasoning}")
            print()
            print(f"💡 Recommendations:")
            for i, rec in enumerate(classification.recommendations, 1):
                print(f"   {i}. {rec}")
        else:
            print("No classification result generated")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 