# ─────────────────────────────────────────────────────────────────────────────
#  Smart Mechanical Fault Diagnosis Agent — Interactive CLI
#  Run: python main.py
#  Run demo scenarios: python main.py --demo
# ─────────────────────────────────────────────────────────────────────────────

import argparse
import sys
from agent import MechanicalFaultAgent

# ─── Demo Scenarios ────────────────────────────────────────────────────────────
DEMO_SCENARIOS = [
    {
        "title": "Scenario 1 — Bearing Fault (Outer Race)",
        "query": (
            "We have a 1500 RPM centrifugal pump with an SKF 6308 bearing "
            "(8 balls, pitch diameter 52 mm, ball diameter 12 mm, contact angle 0°). "
            "Our vibration spectrum shows dominant peaks at: 78.3 Hz, 156.6 Hz, 234.9 Hz. "
            "The bearing housing temperature has risen by 14°C above baseline. "
            "RMS vibration velocity is 6.8 mm/s. Noise level is 82 dB(A). "
            "Oil sample shows 45 ppm iron particles. "
            "Equipment criticality is HIGH. Next planned shutdown is in 10 days. "
            "Please diagnose the fault and provide a maintenance plan."
        ),
    },
    {
        "title": "Scenario 2 — Gear & Shaft Misalignment",
        "query": (
            "A 960 RPM gearbox input shaft is showing the following vibration peaks: "
            "16 Hz, 32 Hz, 480 Hz, 960 Hz. The gearbox has 30 teeth on the input pinion. "
            "RMS vibration is 5.2 mm/s. Temperature rise is 8°C. "
            "Noise level is 88 dB(A). Oil contamination is 30 ppm. "
            "Machine class is large. Equipment criticality is medium. "
            "Days to next shutdown: 21. "
            "Diagnose the faults and recommend corrective actions."
        ),
    },
    {
        "title": "Scenario 3 — Motor Rotor Bar + Imbalance",
        "query": (
            "A 3-phase 50 Hz induction motor running at 2940 RPM (slip ≈ 2%) is showing: "
            "- Current spectrum sidebands at 47.0 Hz and 53.0 Hz "
            "- Strong 49 Hz vibration component in the radial direction "
            "- RMS vibration: 4.1 mm/s, temperature rise: 12°C, "
            "- Noise: 79 dB(A), oil contamination: 5 ppm (oil bath bearings, clean). "
            "Equipment criticality: critical (production line motor). "
            "Days to next shutdown: 45. "
            "What faults are present and what should we do?"
        ),
    },
    {
        "title": "Scenario 4 — Pump Cavitation",
        "query": (
            "A centrifugal water pump running at 3000 RPM is exhibiting broadband vibration "
            "elevation between 500 Hz and 3000 Hz. The operator reports a crackling sound "
            "and 7% reduction in flow rate. Suction pressure gauge reads 0.3 bar absolute. "
            "RMS vibration: 8.9 mm/s, temperature rise: 3°C, noise: 94 dB(A), "
            "no oil (water-lubricated). Equipment criticality: high. "
            "Days to shutdown: 5. "
            "Diagnose the problem and provide an emergency action plan."
        ),
    },
    {
        "title": "Scenario 5 — Raw Vibration Signal Analysis",
        "query": (
            "I have a raw vibration signal sampled at 10000 Hz from a rolling element bearing. "
            "Here is a 20-sample excerpt (g units): "
            "[0.12, 0.08, 0.15, 0.95, 0.11, 0.09, 0.13, 0.87, 0.10, 0.14, "
            " 0.11, 0.09, 1.23, 0.12, 0.08, 0.10, 0.96, 0.11, 0.13, 0.09]. "
            "The shaft runs at 1800 RPM. Temperature rise 6°C, noise 75 dB(A), "
            "oil contamination 20 ppm. Machine class: small. "
            "Calculate the signal statistics and assess the fault severity."
        ),
    },
]


def run_demo(agent: MechanicalFaultAgent, scenario_index: int | None = None) -> None:
    """Run one or all demo scenarios."""
    scenarios = (
        [DEMO_SCENARIOS[scenario_index]] if scenario_index is not None else DEMO_SCENARIOS
    )
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*70}")
        print(f"  [GEAR]  {scenario['title']}")
        print(f"{'='*70}")
        agent.diagnose(scenario["query"], verbose=True)
        if i < len(scenarios):
            cont = input("\n>>  Press ENTER for next scenario (or 'q' to quit): ").strip()
            if cont.lower() == "q":
                break


def run_interactive(agent: MechanicalFaultAgent) -> None:
    """Interactive REPL loop."""
    print("\n" + "="*70)
    print("  [BOT]  Smart Mechanical Fault Diagnosis Agent")
    print("  Model : openai/gpt-oss-120b  |  Powered by Groq")
    print("  Type 'demo' to run built-in scenarios, 'quit' to exit.")
    print("="*70)

    while True:
        try:
            user_input = input("\n[FAULT] Describe the fault / enter sensor data:\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            sys.exit(0)

        if user_input.lower() == "demo":
            print("\nAvailable demo scenarios:")
            for i, s in enumerate(DEMO_SCENARIOS, 1):
                print(f"  {i}. {s['title']}")
            choice = input("Enter number (or ENTER for all): ").strip()
            idx = int(choice) - 1 if choice.isdigit() else None
            run_demo(agent, scenario_index=idx)
            continue

        if user_input.lower() == "help":
            print("""
Available commands:
  demo        — run built-in diagnostic scenarios
  help        — show this help
  quit / exit — exit the application

Or just describe your fault scenario, e.g.:
  "Our pump bearing shows 78 Hz vibration, temperature rise 12°C,
   RMS 6.5 mm/s. Shaft runs at 1500 RPM. What is wrong?"
""")
            continue

        agent.diagnose(user_input, verbose=True)


# ─── Entry Point ───────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smart Mechanical Fault Diagnosis Agent"
    )
    parser.add_argument(
        "--demo",
        nargs="?",
        const=-1,          # run all demos
        type=int,
        metavar="N",
        help="Run demo scenario N (1-5). Omit N to run all demos.",
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        default=None,
        help="Run a single diagnosis query non-interactively.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress step-by-step reasoning output (print final report only).",
    )
    args = parser.parse_args()

    agent = MechanicalFaultAgent()

    if args.query:
        report = agent.diagnose(args.query, verbose=not args.quiet)
        if args.quiet:
            print(report)
    elif args.demo is not None:
        idx = args.demo - 1 if args.demo != -1 else None
        run_demo(agent, scenario_index=idx)
    else:
        run_interactive(agent)


if __name__ == "__main__":
    main()
