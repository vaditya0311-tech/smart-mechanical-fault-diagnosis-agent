# ─────────────────────────────────────────────────────────────────────────────
#  Smart Mechanical Fault Diagnosis Agent — Core Agent
#  ReAct loop powered by Groq API (model: openai/gpt-oss-120b)
# ─────────────────────────────────────────────────────────────────────────────

import json
import os
import time
from groq import Groq, RateLimitError
from tools import TOOL_SCHEMAS, TOOL_REGISTRY

# ─── Configuration ────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
MODEL_ID      = os.getenv("MODEL_ID",      "openai/gpt-oss-120b")
MAX_ITERATIONS = 10   # safety cap on ReAct loop turns

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert Smart Mechanical Fault Diagnosis Agent with deep knowledge
in predictive maintenance, vibration analysis, condition monitoring, and reliability engineering.

## Your Mission
Diagnose mechanical faults in rotating machinery (bearings, gears, motors, pumps, compressors,
shafts) by reasoning step-by-step and using your diagnostic tools.

## Diagnostic Tools Available
1. **analyze_frequency_spectrum** — Match dominant vibration frequencies to fault signatures
   (BPFO, BPFI, BSF, GMF, shaft harmonics, rotor bar sidebands)
2. **assess_fault_severity** — Compute ISO 10816 zone and an overall severity score (0–100)
   from vibration RMS, temperature rise, noise level, and oil contamination data
3. **lookup_fault_knowledge** — Retrieve detailed fault information: symptoms, causes,
   severity indicators, recommended actions, and diagnostic formulae
4. **generate_maintenance_plan** — Produce a prioritised, actionable maintenance schedule
5. **calculate_signal_statistics** — Extract kurtosis, crest factor, RMS, and peak values
   from raw vibration time-series data

## ReAct Protocol
- **Reason** about what data you have and what is missing
- **Act** by calling the most relevant tool
- **Observe** the tool result and update your understanding
- Repeat until you have enough information for a complete diagnosis
- End with a **structured diagnostic report**

## Final Report Structure (always include)
1. 🔍 **Executive Summary** — one-paragraph overview
2. ⚙️  **Identified Faults** — list with confidence level
3. 📊 **Severity Assessment** — score, ISO zone, urgency
4. 🔧 **Root Cause Analysis** — most probable causes
5. 📋 **Maintenance Recommendations** — prioritised action plan
6. 📈 **Monitoring Strategy** — ongoing condition monitoring advice

## Guidelines
- Always use SI units and cite relevant standards (ISO 10816, ISO 1940, ISO 13373)
- State your confidence level for each identified fault (High / Medium / Low)
- If data is insufficient, state what additional measurements are needed
- Be concise but thorough — engineers need actionable information
"""

# ─── Agent Class ──────────────────────────────────────────────────────────────
class MechanicalFaultAgent:
    """ReAct-loop agent for mechanical fault diagnosis."""

    def __init__(self, api_key: str = GROQ_API_KEY, model: str = MODEL_ID):
        self.client  = Groq(api_key=api_key)
        self.model   = model
        self.history: list[dict] = []

    def _reset(self):
        self.history = [{"role": "system", "content": SYSTEM_PROMPT}]

    def _call_llm(self) -> dict:
        """Call the Groq LLM with automatic retry on rate-limit (429)."""
        max_retries = 6
        backoff = 10  # seconds — start conservatively for 8k TPM limit
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.history,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=0.2,
                    max_tokens=4096,
                )
                return response.choices[0].message
            except RateLimitError as exc:
                if attempt == max_retries - 1:
                    raise
                # Parse retry-after from error message if present
                wait = backoff * (2 ** attempt)
                msg = str(exc)
                if "try again in" in msg:
                    try:
                        secs = float(msg.split("try again in")[1].split("s")[0].strip())
                        wait = max(secs + 2, wait)
                    except (ValueError, IndexError):
                        pass
                try:
                    print(
                        f"\n[RATE LIMIT] Waiting {wait:.0f}s before retry "
                        f"(attempt {attempt + 1}/{max_retries})..."
                    )
                except UnicodeEncodeError:
                    print("[RATE LIMIT] Waiting before retry...")
                time.sleep(wait)

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool from the registry and return JSON result."""
        fn = TOOL_REGISTRY.get(tool_name)
        if fn is None:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        try:
            result = fn(**arguments)
            return json.dumps(result, indent=2)
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    def diagnose(self, user_query: str, verbose: bool = True) -> str:
        """
        Run the full ReAct diagnosis loop for a given query.

        Args:
            user_query: Natural-language description of the fault scenario
                        (sensor readings, symptoms, machine type, etc.)
            verbose:    If True, print each reasoning step to stdout

        Returns:
            Final diagnostic report as a string.
        """
        self._reset()
        self.history.append({"role": "user", "content": user_query})

        if verbose:
            _print_step("USER QUERY", user_query, color="cyan")

        iteration  = 0
        final_text = ""

        while iteration < MAX_ITERATIONS:
            iteration += 1

            if verbose:
                _print_step(f"ITERATION {iteration}", "Calling LLM...", color="yellow")

            message = self._call_llm()

            # ── No tool calls → final answer ───────────────────────────────
            if not message.tool_calls:
                final_text = message.content or ""
                self.history.append({"role": "assistant", "content": final_text})
                if verbose:
                    _print_step("FINAL DIAGNOSIS", final_text, color="green")
                break

            # ── Tool call(s) ───────────────────────────────────────────────
            # Append assistant message with tool_calls
            self.history.append(message)

            for tc in message.tool_calls:
                tool_name = tc.function.name
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                if verbose:
                    _print_step(
                        f"TOOL CALL -> {tool_name}",
                        json.dumps(arguments, indent=2),
                        color="blue",
                    )

                result_str = self._execute_tool(tool_name, arguments)

                if verbose:
                    _print_step(f"TOOL RESULT <- {tool_name}", result_str, color="magenta")

                # Append tool result to history
                self.history.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "name":         tool_name,
                    "content":      result_str,
                })

        else:
            # Exceeded max iterations — ask for summary
            self.history.append({
                "role": "user",
                "content": (
                    "You have reached the maximum number of reasoning steps. "
                    "Please provide your best diagnostic report based on the information gathered so far."
                ),
            })
            message    = self._call_llm()
            final_text = message.content or "Diagnosis incomplete — please provide more data."
            if verbose:
                _print_step("FINAL DIAGNOSIS (forced)", final_text, color="green")

        return final_text


# ─── Pretty-print helper ──────────────────────────────────────────────────────
_COLOR_CODES = {
    "cyan":    "\033[96m",
    "yellow":  "\033[93m",
    "green":   "\033[92m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "reset":   "\033[0m",
    "bold":    "\033[1m",
}

def _safe_print(text: str) -> None:
    """Print text, replacing unencodable characters on narrow Windows consoles."""
    import sys
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(
            sys.stdout.encoding or "utf-8"
        ))


def _print_step(label: str, content: str, color: str = "reset") -> None:
    c  = _COLOR_CODES.get(color, "")
    r  = _COLOR_CODES["reset"]
    b  = _COLOR_CODES["bold"]
    sep = "-" * 70
    _safe_print(f"\n{c}{b}{'[' + label + ']':=<73}{r}")
    # Truncate very long content for readability
    display = content if len(content) <= 1200 else content[:1200] + "\n... [truncated for display]"
    _safe_print(display)
    _safe_print(f"{c}{sep}{r}")
