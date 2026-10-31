"""Run all 5 demo scenarios non-interactively and print full reports."""
import sys
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agent import MechanicalFaultAgent
from main import DEMO_SCENARIOS

agent = MechanicalFaultAgent()

for i, scenario in enumerate(DEMO_SCENARIOS, 1):
    print()
    print("=" * 70)
    print(f"  SCENARIO {i}: {scenario['title']}")
    print("=" * 70)
    report = agent.diagnose(scenario["query"], verbose=True)
    print()
    print(">>> FINAL REPORT <<<")
    print(report)
    print()
