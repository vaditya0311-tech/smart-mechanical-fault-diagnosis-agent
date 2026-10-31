# ─────────────────────────────────────────────────────────────────────────────
#  Smart Mechanical Fault Diagnosis Agent — Knowledge Base
#  Covers: bearings, gears, motors, pumps, compressors, shafts
# ─────────────────────────────────────────────────────────────────────────────

FAULT_KNOWLEDGE_BASE = {
    # ── BEARING FAULTS ────────────────────────────────────────────────────────
    "bearing_outer_race": {
        "name": "Bearing Outer Race Defect",
        "component": "Rolling Element Bearing",
        "symptoms": [
            "Periodic vibration at BPFO (Ball Pass Frequency Outer race)",
            "High-frequency envelope spectrum peak",
            "Elevated temperature at bearing housing",
            "Metallic debris in lubrication oil",
        ],
        "severity_indicators": {
            "low": "BPFO harmonic visible, RMS vibration 1–3× baseline",
            "medium": "Multiple BPFO harmonics, RMS 3–6× baseline, slight temperature rise (+5 °C)",
            "high": "Sidebands around BPFO, RMS >6× baseline, temperature rise >10 °C, audible noise",
        },
        "possible_causes": [
            "Overloading", "Misalignment", "Contaminated lubrication",
            "Electrical fluting", "Improper installation",
        ],
        "recommended_actions": [
            "Schedule bearing replacement within 2 weeks (medium severity)",
            "Immediate shutdown and replacement (high severity)",
            "Inspect lubrication quality and quantity",
            "Check alignment and load conditions",
        ],
        "diagnostic_formula": "BPFO = (N/2) × RPM/60 × (1 - d/D × cos(α))",
    },
    "bearing_inner_race": {
        "name": "Bearing Inner Race Defect",
        "component": "Rolling Element Bearing",
        "symptoms": [
            "Periodic vibration at BPFI (Ball Pass Frequency Inner race)",
            "Sidebands at BPFI ± shaft frequency (modulation)",
            "Elevated vibration in axial direction",
            "Grease discoloration",
        ],
        "severity_indicators": {
            "low": "BPFI harmonic visible, minimal sidebands",
            "medium": "Multiple sidebands around BPFI, RMS 3–5× baseline",
            "high": "Heavy sideband forest, temperature >80 °C, audible grinding",
        },
        "possible_causes": [
            "Heavy radial load", "Shaft misalignment", "Contamination",
            "Fretting corrosion", "Fatigue spalling",
        ],
        "recommended_actions": [
            "Plan replacement at next maintenance window",
            "Apply condition-based monitoring intervals",
            "Verify shaft-to-bore fit tolerances",
        ],
        "diagnostic_formula": "BPFI = (N/2) × RPM/60 × (1 + d/D × cos(α))",
    },
    "bearing_rolling_element": {
        "name": "Rolling Element (Ball/Roller) Defect",
        "component": "Rolling Element Bearing",
        "symptoms": [
            "Vibration at BSF (Ball Spin Frequency) and 2×BSF",
            "High kurtosis value (>4) in time-domain signal",
            "Impulsive bursts in time waveform",
            "Noise at twice the ball spin rate",
        ],
        "severity_indicators": {
            "low": "BSF visible, kurtosis 4–6",
            "medium": "2×BSF present, kurtosis 6–10, intermittent noise",
            "high": "Multiple BSF harmonics, kurtosis >10, continuous vibration",
        },
        "possible_causes": [
            "Inadequate lubrication", "Overload", "Spalling fatigue", "Debris ingression",
        ],
        "recommended_actions": [
            "Inspect and relubricate immediately",
            "Replace rolling elements at next opportunity",
            "Install better seals to prevent contamination",
        ],
        "diagnostic_formula": "BSF = (D/2d) × RPM/60 × (1 - (d/D × cos(α))²)",
    },

    # ── GEAR FAULTS ───────────────────────────────────────────────────────────
    "gear_tooth_wear": {
        "name": "Gear Tooth Wear",
        "component": "Gear Train",
        "symptoms": [
            "Elevated GMF (Gear Mesh Frequency) amplitude",
            "Sidebands at GMF ± shaft frequency",
            "Increased noise floor in spectrum",
            "Metal particles in oil analysis",
        ],
        "severity_indicators": {
            "low": "GMF slightly elevated, clean spectrum sidebands",
            "medium": "Sidebands 20–30 dB above noise floor at GMF",
            "high": "Heavy sideband family, ghost frequencies, high noise floor",
        },
        "possible_causes": [
            "Abrasive wear", "Incorrect lubrication viscosity",
            "Overloading", "Misalignment", "Pitting",
        ],
        "recommended_actions": [
            "Perform oil analysis for metal content",
            "Adjust lubrication and check backlash",
            "Replace gear set if high severity",
        ],
        "diagnostic_formula": "GMF = N_teeth × RPM / 60",
    },
    "gear_tooth_crack": {
        "name": "Gear Tooth Crack / Breakage",
        "component": "Gear Train",
        "symptoms": [
            "High kurtosis and crest factor in time waveform",
            "Impulsive once-per-revolution events",
            "Sidebands with non-uniform spacing",
            "Rapid degradation trend in oil debris",
        ],
        "severity_indicators": {
            "low": "Once-per-rev impulse, kurtosis 3–5",
            "medium": "Impulse amplitude 5× RMS, visible crack in borescope",
            "high": "Broken tooth, sudden spike in vibration, immediate failure risk",
        },
        "possible_causes": [
            "Fatigue cracking", "Impact overload", "Subsurface inclusions",
            "Thermal shock", "Stress concentration at root",
        ],
        "recommended_actions": [
            "Immediate shutdown — high risk of catastrophic failure",
            "Borescope inspection at next opportunity",
            "Reduce load if continued operation is necessary",
        ],
        "diagnostic_formula": "Crest Factor = Peak / RMS  (>6 indicates impulse fault)",
    },

    # ── MOTOR / ELECTRICAL FAULTS ─────────────────────────────────────────────
    "rotor_bar_broken": {
        "name": "Broken Rotor Bar (Induction Motor)",
        "component": "Electric Motor",
        "symptoms": [
            "Sidebands at line frequency ± 2×slip×supply_freq",
            "Oscillating torque at 2×slip frequency",
            "Elevated stator current at (1±2s)×fs sidebands",
            "Thermal hotspot on rotor",
        ],
        "severity_indicators": {
            "low": "Sidebands –40 dB below fundamental, slip slightly elevated",
            "medium": "Sidebands –20 to –30 dB, visible torque oscillation",
            "high": "Sidebands > –20 dB, overheating, current unbalance",
        },
        "possible_causes": [
            "Thermal stress cycling", "Mechanical fatigue",
            "Porosity in casting", "Frequent starts/stops",
        ],
        "recommended_actions": [
            "Motor Current Signature Analysis (MCSA)",
            "Plan motor rewind or replacement",
            "Reduce start frequency",
        ],
        "diagnostic_formula": "f_rb = (1 ± 2s) × fs  where s = slip, fs = supply frequency",
    },
    "stator_winding_fault": {
        "name": "Stator Winding Insulation Fault",
        "component": "Electric Motor",
        "symptoms": [
            "Elevated winding temperature",
            "Unbalanced phase currents",
            "Partial discharge activity",
            "Insulation resistance drop (<1 MΩ)",
        ],
        "severity_indicators": {
            "low": "IR 1–5 MΩ, slight current unbalance (<2%)",
            "medium": "IR 0.1–1 MΩ, current unbalance 2–5%, increased heat",
            "high": "IR <0.1 MΩ, phase-to-ground fault risk, trip on thermal overload",
        },
        "possible_causes": [
            "Thermal aging", "Moisture ingress", "Voltage surges",
            "Overloading", "Chemical contamination",
        ],
        "recommended_actions": [
            "Megger test all three phases",
            "Dry out windings in oven if moisture ingress",
            "Rewind or replace motor if high severity",
        ],
        "diagnostic_formula": "Polarization Index (PI) = IR_10min / IR_1min  (PI < 2 = suspect)",
    },
    "motor_imbalance": {
        "name": "Rotor Mass Imbalance",
        "component": "Electric Motor / Rotating Machinery",
        "symptoms": [
            "Dominant 1× RPM vibration in radial direction",
            "High vibration amplitude at running speed",
            "Minimal axial component",
            "Stable phase angle under similar loads",
        ],
        "severity_indicators": {
            "low": "1× slightly above baseline, ISO 10816 Zone A",
            "medium": "1× dominant, ISO 10816 Zone B/C",
            "high": "1× > 7 mm/s RMS, ISO 10816 Zone D, bearing damage risk",
        },
        "possible_causes": [
            "Material buildup on rotor", "Missing balance weight",
            "Repair welding without rebalancing", "Thermal bow",
        ],
        "recommended_actions": [
            "Dynamic balancing (in-situ or in balancing machine)",
            "Inspect rotor for material deposits or damage",
            "Check thermal gradients across rotor",
        ],
        "diagnostic_formula": "Residual imbalance U = e × m  (ISO 1940 balance grade G)",
    },

    # ── SHAFT / COUPLING FAULTS ───────────────────────────────────────────────
    "shaft_misalignment": {
        "name": "Shaft Misalignment (Angular / Parallel)",
        "component": "Shaft / Coupling",
        "symptoms": [
            "High 1× and 2× RPM vibration in axial direction",
            "2× or 3× RPM dominant for angular misalignment",
            "High coupling temperature",
            "180° phase reversal across the coupling",
        ],
        "severity_indicators": {
            "low": "2× slightly elevated, axial vibration <30% of radial",
            "medium": "2× dominant, axial 30–80% of radial",
            "high": "Multiple harmonics (1×, 2×, 3×), coupling damage, bearing wear",
        },
        "possible_causes": [
            "Soft foot", "Thermal growth not compensated",
            "Pipe strain", "Foundation settlement", "Improper alignment procedure",
        ],
        "recommended_actions": [
            "Laser alignment — correct to manufacturer's tolerance",
            "Check and correct soft foot before alignment",
            "Allow for thermal growth offsets",
        ],
        "diagnostic_formula": "Alignment tolerance: typically ±0.05 mm offset, ±0.05 mm/100 mm angularity",
    },
    "shaft_unbalance": {
        "name": "Shaft / Impeller Unbalance",
        "component": "Shaft",
        "symptoms": [
            "Strong 1× RPM vibration",
            "Consistent phase angle across measurements",
            "Higher vibration at higher speeds",
            "Low axial component",
        ],
        "severity_indicators": {
            "low": "1× < 2× baseline",
            "medium": "1× 2–5× baseline",
            "high": "1× > 5× baseline, visible wobble, bearing overheating",
        },
        "possible_causes": [
            "Erosion of impeller blades", "Deposit buildup",
            "Loss of balance weight", "Rotor repair without balancing",
        ],
        "recommended_actions": [
            "In-situ dynamic balancing using influence coefficient method",
            "Inspect impeller/rotor for damage or deposits",
        ],
        "diagnostic_formula": "Balance grade: G = e × ω  (ISO 1940)",
    },

    # ── PUMP / HYDRAULIC FAULTS ───────────────────────────────────────────────
    "pump_cavitation": {
        "name": "Pump Cavitation",
        "component": "Centrifugal Pump",
        "symptoms": [
            "Broadband noise / random vibration (300 Hz–3 kHz)",
            "Flow and pressure fluctuations",
            "Crackling or popping sound",
            "Erosion pitting on impeller",
        ],
        "severity_indicators": {
            "low": "Slight broadband elevation, occasional bubbles",
            "medium": "Broadband 3–6 dB above baseline, flow instability",
            "high": "Severe broadband, impeller damage, head drop >5%",
        },
        "possible_causes": [
            "Low NPSH (Net Positive Suction Head)",
            "High fluid temperature", "Blocked suction strainer",
            "Operation far from BEP", "Recirculation",
        ],
        "recommended_actions": [
            "Increase suction pressure / lower fluid temperature",
            "Clear suction strainer",
            "Throttle discharge to move to BEP",
            "Inspect and replace impeller",
        ],
        "diagnostic_formula": "NPSH_available > NPSH_required + 0.5 m safety margin",
    },
    "pump_wear_ring": {
        "name": "Pump Wear Ring Clearance Loss",
        "component": "Centrifugal Pump",
        "symptoms": [
            "Reduced pump efficiency and flow",
            "Elevated 1× and BPF (Blade Pass Frequency) vibration",
            "Increased recirculation noise",
            "Higher motor current for same output",
        ],
        "severity_indicators": {
            "low": "Efficiency drop <3%, clearance within 1.5× OEM",
            "medium": "Efficiency drop 3–8%, clearance 2× OEM",
            "high": "Efficiency drop >8%, clearance >3× OEM, cavitation risk",
        },
        "possible_causes": [
            "Abrasive particles in fluid", "Cavitation erosion",
            "Corrosion", "Misalignment causing rub",
        ],
        "recommended_actions": [
            "Measure wear ring clearance against OEM specification",
            "Replace wear rings at next maintenance outage",
            "Install better filtration upstream",
        ],
        "diagnostic_formula": "BPF = N_blades × RPM / 60",
    },

    # ── COMPRESSOR FAULTS ─────────────────────────────────────────────────────
    "compressor_surge": {
        "name": "Compressor Surge",
        "component": "Centrifugal Compressor",
        "symptoms": [
            "Violent flow reversal — loud bang/rumble",
            "Rapid oscillation in discharge pressure",
            "Axial shaft movement (thrust bearing damage)",
            "Temperature spike at discharge",
        ],
        "severity_indicators": {
            "low": "Mild stall — slight flow oscillation, recovers quickly",
            "medium": "Repeated surge cycles, rotor rubs possible",
            "high": "Deep surge, shaft damage, seal damage, catastrophic risk",
        },
        "possible_causes": [
            "Operation beyond surge line (low flow / high pressure ratio)",
            "Fouled impeller blades", "Anti-surge valve malfunction",
            "Process upset",
        ],
        "recommended_actions": [
            "Open anti-surge valve / increase suction flow",
            "Check and recalibrate surge control system",
            "Inspect impeller for fouling or damage",
        ],
        "diagnostic_formula": "Surge margin = (Q_surge_line - Q_operating) / Q_operating × 100%",
    },
}

# ── Severity scoring weights ──────────────────────────────────────────────────
SEVERITY_WEIGHTS = {
    "vibration_rms":     0.35,
    "temperature_rise":  0.25,
    "noise_level":       0.20,
    "oil_contamination": 0.20,
}

ISO_10816_ZONES = {
    "Zone A": (0.0, 2.3,  "New machinery — acceptable"),
    "Zone B": (2.3, 4.5,  "Normal long-term operation"),
    "Zone C": (4.5, 7.1,  "Alarm — plan maintenance"),
    "Zone D": (7.1, 999,  "Danger — shutdown recommended"),
}
