"""
RescuE-Triage Configuration & Algorithm Parameters
Defines DEPI weights, thresholds, aging coefficients, and triage categories.
"""

from enum import Enum
from dataclasses import dataclass


class TriageCategory(str, Enum):
    CODE_RED = "CODE_RED"          # Critical / Immediate Life Threat (DEPI >= 75)
    CODE_ORANGE = "CODE_ORANGE"    # Severe / Urgent Attention (DEPI 55 - 74.9)
    CODE_YELLOW = "CODE_YELLOW"    # Moderate / Delayed Care (DEPI 35 - 54.9)
    CODE_GREEN = "CODE_GREEN"      # Minor / Walking Wounded (DEPI < 35)


# Weight coefficients for Dynamic Emergency Priority Index (DEPI)
# Normalized to ensure high discrimination across multi-hazard crises
DEPI_WEIGHTS = {
    "medical": 4.5,         # Medical Urgency (Scale 1-10) -> Max 45 pts
    "environmental": 3.0,   # Environmental Hazard (Scale 1-10) -> Max 30 pts
    "vulnerability": 3.0,   # Vulnerability Factor (Scale 1-5) -> Max 15 pts
    # Base Max Score = 45 + 30 + 15 = 90 pts
}

# Dynamic Wait-Time Scaling Parameters
# Prevents low-urgency starvation without eclipsing acute trauma
WAIT_TIME_CONFIG = {
    "aging_rate_per_min": 0.35,     # Points added per minute of waiting
    "max_wait_bonus": 20.0,         # Maximum dynamic escalation cap (prevents overflow)
    "acceleration_exponent": 1.15,  # Non-linear aging factor: wait_time^exponent
    "critical_escalation_thresh": 60 # Minutes after which non-urgent cases escalate a tier
}

# Emergency Response Dispatch Units
AVAILABLE_UNITS = [
    {"id": "AMB-01", "name": "Advanced Life Support Ambulance", "type": "Medical", "status": "AVAILABLE"},
    {"id": "AMB-02", "name": "Basic Life Support Ambulance", "type": "Medical", "status": "AVAILABLE"},
    {"id": "FIRE-01", "name": "Heavy Fire & Rescue Engine", "type": "Fire/Hazmat", "status": "AVAILABLE"},
    {"id": "BOAT-01", "name": "Zodiac Flood Rescue Boat", "type": "Water Rescue", "status": "AVAILABLE"},
    {"id": "HELI-01", "name": "Air Ambulance Evacuation Helicopter", "type": "Air Medevac", "status": "AVAILABLE"},
    {"id": "SAR-01", "name": "Urban Search & Rescue Squad", "type": "Collapse/SAR", "status": "AVAILABLE"},
]
