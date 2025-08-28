import asyncio
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.teams.magentic_one import MagenticOne


TASK = """
You are a cautious clinical data analyst. Read a local heartbeat buffer file at:
  C:/Users/Peyton Maahs/Desktop/repos/care-guard/patient/biometric/demo_scenarios/normal.json

Goal:
1) Load the buffer. It is a json document
2) Clean: remove RR outliers (<300 ms or >2000 ms), interpolate gaps < 5 s.
3) Compute features over sliding 5-minute windows with 50 percent overlap:
   - mean_hr, sdnn, rmssd, pnn50, sample_entropy (if easy), irregularity_index = stdev(diff(rr_ms))
4) Heuristic AF flag per window:
   - mean_hr between 40–140 bpm AND irregularity_index and rmssd above the 80th percentile of baseline for that subject OR above common cutoffs (rmssd > 50 ms and irregularity_index > 80 ms).
   - Require >=30 consecutive minutes of AF-like pattern to raise 'AF_suspected = true'.
5) Output a single JSON to ./out/triage.json:
   {
     "AF_suspected": true|false,
     "minutes_flagged": number,
     "windows_flagged": [ { "start": "...", "end": "...", "metrics": {...} } ],
     "advice": "NOT A DIAGNOSIS. If neurological symptoms (FAST) call emergency services now."
   }

Constraints / safety:
- DO NOT claim to diagnose stroke. Only flag rhythm irregularity compatible with AF risk.
- Prefer pure-Python + numpy/pandas; install extras only if necessary.
- Print a short summary at the end and write the JSON file.
"""

async def require_approval(action):
    print(f"\n--- Proposed action ---\n{action}\n")
    ans = input("Approve this action? (y/n): ").strip().lower()
    return ans == "y"

async def run():
    client = OpenAIChatCompletionClient(model="gpt-4o",
                                        api_key="")
    team = MagenticOne(client=client, approval_func=require_approval)   # you could add executor=DockerCodeExecutor()
    stream = team.run_stream(task=TASK)

    # wrap the stream in Console, then await the console
    console = Console(stream)
    result = await console
    print("\nFinal result:", result)


asyncio.run(run())

