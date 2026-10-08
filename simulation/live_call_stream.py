"""
Live Distress Call Stream Simulator.
Simulates real-time incoming 911 / 112 distress calls during active crises.
"""

import time
import random
from typing import Generator
from core.data_models import DistressCall, VulnerabilityProfile

SAMPLE_CALLER_NAMES = [
    "Aniket Das", "Priya Chatterjee", "Sunil Malhotra", "Meera Krishnan",
    "Deepak Sharma", "Tanvi Agarwal", "Rajiv Sen", "Swati Nambiar",
    "Farhan Ali", "Smita Roy", "Karthik Menon", "Shreya Sengupta"
]

SAMPLE_LOCATIONS = [
    "Metro Corridor Pillar 48", "Riverside Embankment Block C", "City Hospital East Gate",
    "Industrial Estate Phase 2", "Old Market Square", "Lakeview Apartments Tower 3",
    "Southern Bypass Flyover", "Salt Lake Central Park Sector 3", "University North Hostel",
    "Port Terminal Gate 5"
]

SAMPLE_SCENARIOS = [
    ("Urban Flood", "Water entered living quarters, electrical panel sparking near water surface.", 7, 8),
    ("Structural Distress", "Ceiling plaster collapsing, loud cracking sound from main pillar.", 5, 8),
    ("Medical Emergency", "Severe chest pain radiating to left arm, victim collapsed on floor.", 9, 3),
    ("Chemical Fumes", "Strong chlorine smell spreading from nearby tanker, burning eyes and throat.", 8, 9),
    ("Trapped in Elevator", "Lift stalled between 4th and 5th floors with 4 people during power cut.", 4, 6),
    ("Thermal Injury", "Kitchen gas cylinder flash fire, deep second degree burns on hands and chest.", 9, 6),
    ("Minor Injury", "Twisted ankle while rushing downstairs, needs assistance walking.", 2, 2)
]


def generate_single_random_call() -> DistressCall:
    """Generates a realistic random incoming emergency call."""
    name = random.choice(SAMPLE_CALLER_NAMES)
    location = random.choice(SAMPLE_LOCATIONS)
    scenario_type, desc, base_med, base_env = random.choice(SAMPLE_SCENARIOS)

    # Add slight random variations
    med = max(1, min(10, base_med + random.randint(-1, 1)))
    env = max(1, min(10, base_env + random.randint(-1, 1)))

    # Randomized vulnerability
    has_elderly = 1 if random.random() < 0.35 else 0
    has_child = random.randint(1, 2) if random.random() < 0.30 else 0
    has_disabled = 1 if random.random() < 0.15 else 0
    has_pregnant = 1 if random.random() < 0.10 else 0

    vuln = VulnerabilityProfile(
        infants_count=1 if random.random() < 0.15 else 0,
        children_count=has_child,
        elderly_count=has_elderly,
        disabled_count=has_disabled,
        pregnant_count=has_pregnant
    )

    phone = f"+91-98{random.randint(100, 999)}-{random.randint(10000, 99999)}"

    # Generate slight coordinate jitter around city center (Kolkata lat/lon)
    lat = 22.5726 + random.uniform(-0.06, 0.06)
    lon = 88.3639 + random.uniform(-0.06, 0.06)

    return DistressCall(
        caller_name=name,
        phone=phone,
        location=location,
        coordinates=(round(lat, 4), round(lon, 4)),
        medical_urgency=med,
        environmental_hazard=env,
        vulnerability=vuln,
        disaster_type=scenario_type,
        description=desc,
        created_timestamp=time.time(),
        status="QUEUED"
    )
