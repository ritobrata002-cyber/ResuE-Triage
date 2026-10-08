"""
Crisis Scenario Presets & Mock Data Generator for RescuE-Triage.
Generates realistic multi-factor disaster scenarios: Floods, Earthquakes, Fires, Gas Leaks.
"""

import time
import random
from typing import List, Dict, Any
from core.data_models import DistressCall, VulnerabilityProfile


DISASTER_PRESETS = {
    "urban_flood": {
        "title": "Severe Urban Monsoon Flood (Ward 7 & 8)",
        "description": "Rapidly rising river inundation. Ground floor homes submerged up to 2 meters.",
        "calls": [
            {
                "caller_name": "Dr. Sarah Sen",
                "phone": "+91-98301-11223",
                "location": "Sector 5, Riverside Lowlands, House 42",
                "coordinates": (22.5801, 88.4120),
                "medical_urgency": 9,
                "environmental_hazard": 9,
                "vulnerability": VulnerabilityProfile(elderly_count=2, disabled_count=1),
                "wait_offset_mins": 25,
                "disaster_type": "Urban Flood",
                "description": "Water rising above chest level; 78yo bedridden grandfather experiencing hypothermia and shortness of breath."
            },
            {
                "caller_name": "Rohan Verma",
                "phone": "+91-98312-33445",
                "location": "North Barrack Road, Apt 3B",
                "coordinates": (22.5860, 88.4080),
                "medical_urgency": 4,
                "environmental_hazard": 8,
                "vulnerability": VulnerabilityProfile(infants_count=1, pregnant_count=1),
                "wait_offset_mins": 18,
                "disaster_type": "Urban Flood",
                "description": "Trapped on terrace with 4-month-old infant and 8-month pregnant wife. No clean drinking water."
            },
            {
                "caller_name": "Amina Khatun",
                "phone": "+91-98320-55667",
                "location": "Bridge Approach Lane, Shop #12",
                "coordinates": (22.5740, 88.4200),
                "medical_urgency": 2,
                "environmental_hazard": 5,
                "vulnerability": VulnerabilityProfile(children_count=1),
                "wait_offset_mins": 55, # Demonstrates starvation aging!
                "disaster_type": "Urban Flood",
                "description": "Knee deep water, safe on concrete counter. Waiting for food packet and evacuation guidance."
            },
            {
                "caller_name": "Inspector Ghosh",
                "phone": "+91-98300-99881",
                "location": "Ring Road Underpass Junction",
                "coordinates": (22.5690, 88.3950),
                "medical_urgency": 10,
                "environmental_hazard": 10,
                "vulnerability": VulnerabilityProfile(children_count=2, elderly_count=1),
                "wait_offset_mins": 4,
                "disaster_type": "Urban Flood",
                "description": "Submerged school bus swept towards canal. Water nearing roof line. Immediate swift-water rescue needed!"
            },
            {
                "caller_name": "Bikram Patel",
                "phone": "+91-98305-66778",
                "location": "Greenwood Enclave, Block D",
                "coordinates": (22.5910, 88.4250),
                "medical_urgency": 6,
                "environmental_hazard": 4,
                "vulnerability": VulnerabilityProfile(elderly_count=1),
                "wait_offset_mins": 40,
                "disaster_type": "Urban Flood",
                "description": "Diabetic medication washed away, elderly mother showing signs of ketoacidosis."
            }
        ]
    },
    "earthquake": {
        "title": "Magnitude 6.8 Earthquake Structural Collapse",
        "description": "Multi-structure collapse, active gas leaks, trapped victims under debris.",
        "calls": [
            {
                "caller_name": "Sunita Rao",
                "phone": "+91-98741-22334",
                "location": "Heritage Mall, Pillar 14 Collapse",
                "coordinates": (22.5620, 88.3560),
                "medical_urgency": 10,
                "environmental_hazard": 8,
                "vulnerability": VulnerabilityProfile(children_count=1),
                "wait_offset_mins": 12,
                "disaster_type": "Earthquake",
                "description": "Crush syndrome: 8yo child pinned under reinforced concrete slab with severe pelvic trauma."
            },
            {
                "caller_name": "Debashis Roy",
                "phone": "+91-98742-33445",
                "location": "Old Town Commercial Complex, Fl 2",
                "coordinates": (22.5580, 88.3510),
                "medical_urgency": 7,
                "environmental_hazard": 9,
                "vulnerability": VulnerabilityProfile(disabled_count=1),
                "wait_offset_mins": 30,
                "disaster_type": "Earthquake",
                "description": "Stairwell collapsed, smell of natural gas leak spreading rapidly. Wheelchair user unable to evacuate."
            },
            {
                "caller_name": "Pooja Banerjee",
                "phone": "+91-98745-66778",
                "location": "Metro Station Gate 3 Entrance",
                "coordinates": (22.5645, 88.3610),
                "medical_urgency": 3,
                "environmental_hazard": 3,
                "vulnerability": VulnerabilityProfile(),
                "wait_offset_mins": 62,
                "disaster_type": "Earthquake",
                "description": "Minor lacerations from shattered storefront glass. Mild hysteria. Stable."
            },
            {
                "caller_name": "Kavita Nair",
                "phone": "+91-98749-88990",
                "location": "St. Jude Hospital Annex",
                "coordinates": (22.5510, 88.3490),
                "medical_urgency": 9,
                "environmental_hazard": 6,
                "vulnerability": VulnerabilityProfile(infants_count=3),
                "wait_offset_mins": 15,
                "disaster_type": "Earthquake",
                "description": "Neonatal ICU power backup failure following generator fuel leak. 3 premature infants on oxygen."
            }
        ]
    },
    "highrise_fire": {
        "title": "Industrial High-Rise Tower Fire (Tower B)",
        "description": "Blaze spreading between 7th and 11th floors. Heavy toxic smoke in emergency staircases.",
        "calls": [
            {
                "caller_name": "Security Desk Tower B",
                "phone": "+91-98200-11229",
                "location": "Cyber Heights Tower B, Floor 9",
                "coordinates": (22.5710, 88.4320),
                "medical_urgency": 9,
                "environmental_hazard": 10,
                "vulnerability": VulnerabilityProfile(pregnant_count=1),
                "wait_offset_mins": 8,
                "disaster_type": "Urban Fire",
                "description": "Multiple workers trapped in conference room. Smoke density extreme, 2 unconscious from smoke inhalation."
            },
            {
                "caller_name": "Tanya Sengupta",
                "phone": "+91-98205-44332",
                "location": "Cyber Heights Tower B, Floor 14 Roof",
                "coordinates": (22.5712, 88.4322),
                "medical_urgency": 5,
                "environmental_hazard": 7,
                "vulnerability": VulnerabilityProfile(elderly_count=1),
                "wait_offset_mins": 22,
                "disaster_type": "Urban Fire",
                "description": "12 people gathered on rooftop helipad. Smoke billowing upward, breathing difficulties."
            },
            {
                "caller_name": "Arjun Singha",
                "phone": "+91-98209-77881",
                "location": "Ground Floor Lobby East Exit",
                "coordinates": (22.5708, 88.4318),
                "medical_urgency": 2,
                "environmental_hazard": 2,
                "vulnerability": VulnerabilityProfile(),
                "wait_offset_mins": 50,
                "disaster_type": "Urban Fire",
                "description": "Safely evacuated outside. Minor cough from smoke, requests triage check when teams free."
            }
        ]
    }
}


def load_preset_scenario(preset_key: str, reference_time: float = None) -> List[DistressCall]:
    """Instantiates DistressCall objects from scenario preset with relative timestamps."""
    if preset_key not in DISASTER_PRESETS:
        preset_key = "urban_flood"

    now = reference_time or time.time()
    preset = DISASTER_PRESETS[preset_key]
    calls = []

    for raw in preset["calls"]:
        created_ts = now - (raw["wait_offset_mins"] * 60.0)
        call = DistressCall(
            caller_name=raw["caller_name"],
            phone=raw["phone"],
            location=raw["location"],
            coordinates=raw["coordinates"],
            medical_urgency=raw["medical_urgency"],
            environmental_hazard=raw["environmental_hazard"],
            vulnerability=raw["vulnerability"],
            created_timestamp=created_ts,
            disaster_type=raw["disaster_type"],
            description=raw["description"],
            status="QUEUED"
        )
        calls.append(call)

    return calls
