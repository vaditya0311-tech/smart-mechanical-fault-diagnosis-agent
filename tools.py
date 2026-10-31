# ─────────────────────────────────────────────────────────────────────────────
#  Smart Mechanical Fault Diagnosis Agent — Diagnostic Tools
#  Each tool is a standalone Python function the agent can call.
# ─────────────────────────────────────────────────────────────────────────────

import json
import math
from knowledge_base import (
    FAULT_KNOWLEDGE_BASE,
    SEVERITY_WEIGHTS,
    ISO_10816_ZONES,
)


# ─── Tool 1: Frequency Analyzer ───────────────────────────────────────────────
def analyze_frequency_spectrum(
    dominant_frequencies: list[float],
    shaft_rpm: float,
    component_type: str,
    extra_params: dict | None = None,
) -> dict:
    """
    Analyze dominant vibration frequencies and match them to known fault patterns.

    Args:
        dominant_frequencies: list of dominant frequencies in Hz (up to 10)
        shaft_rpm: shaft rotational speed in RPM
        component_type: one of 'bearing', 'gear', 'motor', 'shaft', 'pump', 'compressor'
        extra_params: optional dict with keys like 'n_balls', 'pitch_diameter',
                      'ball_diameter', 'contact_angle', 'n_teeth', 'n_blades',
                      'slip_fraction', 'supply_freq'
    """
    extra_params = extra_params or {}
    shaft_freq = shaft_rpm / 60.0
    results = {"shaft_freq_hz": shaft_freq, "matches": [], "calculated_fault_freqs": {}}

    # ── Bearing fault frequencies ──────────────────────────────────────────
    if component_type in ("bearing", "all"):
        N = extra_params.get("n_balls", 8)
        d = extra_params.get("ball_diameter", 10)       # mm
        D = extra_params.get("pitch_diameter", 40)      # mm
        alpha = math.radians(extra_params.get("contact_angle_deg", 0))
        ratio = (d / D) * math.cos(alpha)

        bpfo = (N / 2) * shaft_freq * (1 - ratio)
        bpfi = (N / 2) * shaft_freq * (1 + ratio)
        bsf  = (D / (2 * d)) * shaft_freq * (1 - ratio**2)
        ftf  = 0.5 * shaft_freq * (1 - ratio)

        results["calculated_fault_freqs"]["BPFO"] = round(bpfo, 2)
        results["calculated_fault_freqs"]["BPFI"] = round(bpfi, 2)
        results["calculated_fault_freqs"]["BSF"]  = round(bsf,  2)
        results["calculated_fault_freqs"]["FTF"]  = round(ftf,  2)

        tolerance = 0.10  # 10% tolerance
        for freq in dominant_frequencies:
            for label, ref_freq in [("BPFO", bpfo), ("BPFI", bpfi), ("BSF", bsf), ("FTF", ftf)]:
                for harmonic in range(1, 5):
                    if abs(freq - ref_freq * harmonic) / (ref_freq * harmonic + 1e-9) < tolerance:
                        results["matches"].append({
                            "frequency_hz": freq,
                            "matched_to": f"{harmonic}×{label}",
                            "fault_type": {
                                "BPFO": "bearing_outer_race",
                                "BPFI": "bearing_inner_race",
                                "BSF":  "bearing_rolling_element",
                                "FTF":  "bearing_outer_race",  # cage fault
                            }[label],
                        })

    # ── Gear mesh frequencies ──────────────────────────────────────────────
    if component_type in ("gear", "all"):
        n_teeth = extra_params.get("n_teeth", 30)
        gmf = n_teeth * shaft_freq
        results["calculated_fault_freqs"]["GMF"] = round(gmf, 2)
        for freq in dominant_frequencies:
            for harmonic in range(1, 4):
                if abs(freq - gmf * harmonic) / (gmf * harmonic + 1e-9) < 0.08:
                    results["matches"].append({
                        "frequency_hz": freq,
                        "matched_to": f"{harmonic}×GMF",
                        "fault_type": "gear_tooth_wear",
                    })

    # ── Motor / rotor bar ──────────────────────────────────────────────────
    if component_type in ("motor", "all"):
        fs  = extra_params.get("supply_freq", 50)
        slip = extra_params.get("slip_fraction", 0.03)
        frb_lo = (1 - 2 * slip) * fs
        frb_hi = (1 + 2 * slip) * fs
        results["calculated_fault_freqs"]["RB_lower_sideband"] = round(frb_lo, 2)
        results["calculated_fault_freqs"]["RB_upper_sideband"] = round(frb_hi, 2)
        for freq in dominant_frequencies:
            if abs(freq - frb_lo) / (frb_lo + 1e-9) < 0.05 or \
               abs(freq - frb_hi) / (frb_hi + 1e-9) < 0.05:
                results["matches"].append({
                    "frequency_hz": freq,
                    "matched_to": "Rotor bar sideband",
                    "fault_type": "rotor_bar_broken",
                })

    # ── Shaft harmonics ────────────────────────────────────────────────────
    for freq in dominant_frequencies:
        for harmonic in range(1, 5):
            if abs(freq - shaft_freq * harmonic) / (shaft_freq * harmonic + 1e-9) < 0.05:
                fault = "shaft_unbalance" if harmonic == 1 else "shaft_misalignment"
                existing = [m for m in results["matches"] if m["frequency_hz"] == freq]
                if not existing:
                    results["matches"].append({
                        "frequency_hz": freq,
                        "matched_to": f"{harmonic}× shaft frequency",
                        "fault_type": fault,
                    })

    results["total_matches"] = len(results["matches"])
    return results


# ─── Tool 2: Severity Assessor ────────────────────────────────────────────────
def assess_fault_severity(
    vibration_rms_mm_s: float,
    temperature_rise_c: float,
    noise_level_db: float,
    oil_contamination_ppm: float,
    component_class: str = "medium",  # 'small', 'medium', 'large'
) -> dict:
    """
    Compute an overall severity score (0–100) and ISO 10816 zone classification.

    Args:
        vibration_rms_mm_s:  RMS vibration velocity in mm/s
        temperature_rise_c:  Temperature rise above baseline in °C
        noise_level_db:      Noise level in dB(A)
        oil_contamination_ppm: Metal particle concentration in lube oil (ppm)
        component_class:     Machine size class: 'small', 'medium', 'large'
    """
    # ISO 10816 zone
    iso_zone = "Zone D"
    iso_desc = ISO_10816_ZONES["Zone D"][2]
    for zone, (lo, hi, desc) in ISO_10816_ZONES.items():
        if lo <= vibration_rms_mm_s < hi:
            iso_zone = zone
            iso_desc = desc
            break

    # Normalised subscores (0–100)
    vib_limits  = {"small": 7.1, "medium": 11.2, "large": 18.0}
    vib_limit   = vib_limits.get(component_class, 11.2)
    vib_score   = min(vibration_rms_mm_s / vib_limit * 100, 100)
    temp_score  = min(temperature_rise_c / 30.0 * 100, 100)   # 30 °C rise = 100
    noise_score = min(max(noise_level_db - 60, 0) / 40.0 * 100, 100)  # 100 dB = 100
    oil_score   = min(oil_contamination_ppm / 200.0 * 100, 100)       # 200 ppm = 100

    overall = (
        vib_score   * SEVERITY_WEIGHTS["vibration_rms"]
        + temp_score  * SEVERITY_WEIGHTS["temperature_rise"]
        + noise_score * SEVERITY_WEIGHTS["noise_level"]
        + oil_score   * SEVERITY_WEIGHTS["oil_contamination"]
    )

    if overall < 25:
        severity_label, urgency = "LOW",      "Monitor — next scheduled maintenance"
    elif overall < 55:
        severity_label, urgency = "MEDIUM",   "Plan repair within 2–4 weeks"
    elif overall < 75:
        severity_label, urgency = "HIGH",     "Repair within 1 week"
    else:
        severity_label, urgency = "CRITICAL", "⚠  Immediate shutdown recommended"

    return {
        "overall_score":     round(overall, 1),
        "severity_label":    severity_label,
        "urgency":           urgency,
        "iso_10816_zone":    iso_zone,
        "iso_description":   iso_desc,
        "subscores": {
            "vibration":         round(vib_score, 1),
            "temperature":       round(temp_score, 1),
            "noise":             round(noise_score, 1),
            "oil_contamination": round(oil_score, 1),
        },
    }


# ─── Tool 3: Fault Knowledge Lookup ───────────────────────────────────────────
def lookup_fault_knowledge(fault_type: str) -> dict:
    """
    Retrieve detailed knowledge for a specific fault type from the knowledge base.

    Args:
        fault_type: key from FAULT_KNOWLEDGE_BASE (e.g. 'bearing_outer_race',
                    'gear_tooth_wear', 'shaft_misalignment', 'pump_cavitation', etc.)
    """
    if fault_type in FAULT_KNOWLEDGE_BASE:
        return {"found": True, "fault_type": fault_type, **FAULT_KNOWLEDGE_BASE[fault_type]}
    # fuzzy fallback — search by keyword
    matches = []
    for key, info in FAULT_KNOWLEDGE_BASE.items():
        if any(word in key for word in fault_type.lower().split("_")):
            matches.append(key)
    if matches:
        return {
            "found": False,
            "message": f"Exact key '{fault_type}' not found. Did you mean: {matches}?",
        }
    return {
        "found": False,
        "message": f"No knowledge found for '{fault_type}'.",
        "available_faults": list(FAULT_KNOWLEDGE_BASE.keys()),
    }


# ─── Tool 4: Maintenance Recommender ──────────────────────────────────────────
def generate_maintenance_plan(
    fault_types: list[str],
    severity_score: float,
    equipment_criticality: str = "medium",  # 'low', 'medium', 'high', 'critical'
    days_to_next_shutdown: int = 30,
) -> dict:
    """
    Generate a prioritised maintenance plan given detected faults and severity.

    Args:
        fault_types:             list of detected fault type keys
        severity_score:          overall severity score (0–100)
        equipment_criticality:   operational criticality of the equipment
        days_to_next_shutdown:   days until next planned maintenance window
    """
    priority_matrix = {
        ("LOW",      "low"):      "Corrective — next major overhaul",
        ("LOW",      "medium"):   "Corrective — next planned shutdown",
        ("LOW",      "high"):     "Preventive — schedule within 60 days",
        ("LOW",      "critical"): "Preventive — schedule within 30 days",
        ("MEDIUM",   "low"):      "Preventive — schedule within 30 days",
        ("MEDIUM",   "medium"):   "Preventive — schedule within 14 days",
        ("MEDIUM",   "high"):     "Urgent — schedule within 7 days",
        ("MEDIUM",   "critical"): "Urgent — schedule within 3 days",
        ("HIGH",     "low"):      "Urgent — within 7 days",
        ("HIGH",     "medium"):   "Urgent — within 3 days",
        ("HIGH",     "high"):     "Emergency — within 24 hours",
        ("HIGH",     "critical"): "⚠  Immediate shutdown",
        ("CRITICAL", "low"):      "Emergency — within 24 hours",
        ("CRITICAL", "medium"):   "⚠  Immediate shutdown",
        ("CRITICAL", "high"):     "⚠  Immediate shutdown",
        ("CRITICAL", "critical"): "⚠  STOP MACHINE NOW",
    }

    if severity_score < 25:
        sev_label = "LOW"
    elif severity_score < 55:
        sev_label = "MEDIUM"
    elif severity_score < 75:
        sev_label = "HIGH"
    else:
        sev_label = "CRITICAL"

    priority_key  = (sev_label, equipment_criticality)
    priority_text = priority_matrix.get(priority_key, "Assess manually")

    actions = []
    spares  = []
    for ft in fault_types:
        info = FAULT_KNOWLEDGE_BASE.get(ft, {})
        actions.extend(info.get("recommended_actions", []))
        component = info.get("component", "")
        if component and component not in spares:
            spares.append(component)

    # Deduplicate actions
    seen, unique_actions = set(), []
    for a in actions:
        if a not in seen:
            seen.add(a)
            unique_actions.append(a)

    can_defer = days_to_next_shutdown <= 14 and sev_label in ("LOW", "MEDIUM")

    return {
        "priority":               priority_text,
        "severity_label":         sev_label,
        "equipment_criticality":  equipment_criticality,
        "can_defer_to_shutdown":  can_defer,
        "days_to_next_shutdown":  days_to_next_shutdown,
        "recommended_actions":    unique_actions or ["Perform detailed inspection"],
        "spare_parts_needed":     spares or ["Consult OEM for specific spare list"],
        "monitoring_interval":    {
            "LOW":      "Monthly vibration survey",
            "MEDIUM":   "Weekly vibration + daily temperature check",
            "HIGH":     "Continuous online monitoring",
            "CRITICAL": "Shutdown — do not operate",
        }[sev_label],
    }


# ─── Tool 5: Signal Statistics Calculator ────────────────────────────────────
def calculate_signal_statistics(time_series: list[float], sample_rate_hz: float) -> dict:
    """
    Compute key statistical indicators from a raw vibration time-series.

    Args:
        time_series:     list of acceleration values (g or m/s²)
        sample_rate_hz:  sampling frequency in Hz
    """
    import statistics

    n = len(time_series)
    if n < 4:
        return {"error": "Need at least 4 samples"}

    mean_val = sum(time_series) / n
    # RMS
    rms = math.sqrt(sum(x**2 for x in time_series) / n)
    # Peak
    peak = max(abs(x) for x in time_series)
    # Crest factor
    crest_factor = peak / rms if rms > 1e-9 else 0
    # Kurtosis (4th statistical moment)
    std = statistics.stdev(time_series)
    if std > 1e-9:
        kurtosis = sum(((x - mean_val) / std) ** 4 for x in time_series) / n
    else:
        kurtosis = 0
    # Skewness
    if std > 1e-9:
        skewness = sum(((x - mean_val) / std) ** 3 for x in time_series) / n
    else:
        skewness = 0
    # Peak-to-peak
    p2p = max(time_series) - min(time_series)

    # Interpretation
    fault_indicators = []
    if kurtosis > 6:
        fault_indicators.append("High kurtosis -> impulsive fault (bearing/gear defect likely)")
    if crest_factor > 4:
        fault_indicators.append("High crest factor -> impulsive events present")
    if kurtosis > 3 and crest_factor > 3:
        fault_indicators.append("Both kurtosis & crest factor elevated -> early-stage bearing fault")

    return {
        "n_samples":       n,
        "sample_rate_hz":  sample_rate_hz,
        "duration_s":      round(n / sample_rate_hz, 4),
        "mean":            round(mean_val, 6),
        "rms":             round(rms, 6),
        "peak":            round(peak, 6),
        "peak_to_peak":    round(p2p, 6),
        "crest_factor":    round(crest_factor, 3),
        "kurtosis":        round(kurtosis, 3),
        "skewness":        round(skewness, 3),
        "std_dev":         round(std, 6),
        "fault_indicators": fault_indicators,
    }


# ─── Tool Registry (for the agent) ────────────────────────────────────────────
TOOL_REGISTRY: dict[str, callable] = {
    "analyze_frequency_spectrum":  analyze_frequency_spectrum,
    "assess_fault_severity":       assess_fault_severity,
    "lookup_fault_knowledge":      lookup_fault_knowledge,
    "generate_maintenance_plan":   generate_maintenance_plan,
    "calculate_signal_statistics": calculate_signal_statistics,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_frequency_spectrum",
            "description": (
                "Analyze dominant vibration frequencies from a spectrum and match them to "
                "known mechanical fault patterns (bearing faults, gear mesh, shaft harmonics, "
                "rotor bar sidebands). Returns matched fault types and calculated reference frequencies."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dominant_frequencies": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "List of dominant frequencies in Hz found in the vibration spectrum.",
                    },
                    "shaft_rpm": {
                        "type": "number",
                        "description": "Shaft rotational speed in RPM.",
                    },
                    "component_type": {
                        "type": "string",
                        "enum": ["bearing", "gear", "motor", "shaft", "pump", "compressor", "all"],
                        "description": "Type of mechanical component being analyzed.",
                    },
                    "extra_params": {
                        "type": "object",
                        "description": (
                            "Optional parameters: n_balls, ball_diameter, pitch_diameter, "
                            "contact_angle_deg (bearing); n_teeth (gear); "
                            "supply_freq, slip_fraction (motor); n_blades (pump)."
                        ),
                    },
                },
                "required": ["dominant_frequencies", "shaft_rpm", "component_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "assess_fault_severity",
            "description": (
                "Compute an overall fault severity score (0–100) and ISO 10816 vibration zone "
                "classification from multi-parameter sensor readings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vibration_rms_mm_s": {
                        "type": "number",
                        "description": "RMS vibration velocity in mm/s.",
                    },
                    "temperature_rise_c": {
                        "type": "number",
                        "description": "Temperature rise above ambient/baseline in °C.",
                    },
                    "noise_level_db": {
                        "type": "number",
                        "description": "Noise level in dB(A).",
                    },
                    "oil_contamination_ppm": {
                        "type": "number",
                        "description": "Metal particle concentration in lubricating oil in ppm.",
                    },
                    "component_class": {
                        "type": "string",
                        "enum": ["small", "medium", "large"],
                        "description": "Machine size class for ISO 10816 limit selection.",
                        "default": "medium",
                    },
                },
                "required": [
                    "vibration_rms_mm_s", "temperature_rise_c",
                    "noise_level_db", "oil_contamination_ppm",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_fault_knowledge",
            "description": (
                "Look up detailed information about a specific mechanical fault type: symptoms, "
                "severity indicators, root causes, recommended actions, and diagnostic formulae."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fault_type": {
                        "type": "string",
                        "description": (
                            "Fault type key, one of: bearing_outer_race, bearing_inner_race, "
                            "bearing_rolling_element, gear_tooth_wear, gear_tooth_crack, "
                            "rotor_bar_broken, stator_winding_fault, motor_imbalance, "
                            "shaft_misalignment, shaft_unbalance, pump_cavitation, "
                            "pump_wear_ring, compressor_surge."
                        ),
                    },
                },
                "required": ["fault_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_maintenance_plan",
            "description": (
                "Generate a prioritised maintenance plan with urgency, actions, spare parts, "
                "and monitoring intervals based on detected faults and severity."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "fault_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of detected fault type keys.",
                    },
                    "severity_score": {
                        "type": "number",
                        "description": "Overall severity score from assess_fault_severity (0–100).",
                    },
                    "equipment_criticality": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Operational criticality of the equipment.",
                        "default": "medium",
                    },
                    "days_to_next_shutdown": {
                        "type": "integer",
                        "description": "Days until the next planned maintenance shutdown.",
                        "default": 30,
                    },
                },
                "required": ["fault_types", "severity_score"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_signal_statistics",
            "description": (
                "Compute RMS, peak, crest factor, kurtosis, and skewness from a raw vibration "
                "time-series to identify impulsive fault signatures."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "time_series": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "List of acceleration values (g or m/s²).",
                    },
                    "sample_rate_hz": {
                        "type": "number",
                        "description": "Sampling frequency of the sensor in Hz.",
                    },
                },
                "required": ["time_series", "sample_rate_hz"],
            },
        },
    },
]
