"""
Data models for RescuE-Triage Decision Support System.
Encapsulates distress calls, triage assessment metrics, and DEPI score breakdown.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid
import time

from config import TriageCategory


@dataclass
class VulnerabilityProfile:
    """Breakdown of vulnerable individuals present at incident scene."""
    infants_count: int = 0
    children_count: int = 0
    elderly_count: int = 0
    disabled_count: int = 0
    pregnant_count: int = 0

    def compute_factor(self) -> float:
        """
        Calculates normalized vulnerability multiplier [1.0 to 5.0].
        Standard base = 1.0 (independent adults)
        Infants/Disabled: +1.5 each
        Elderly/Pregnant/Children: +1.0 each
        """
        score = 1.0
        score += self.infants_count * 1.5
        score += self.disabled_count * 1.5
        score += self.elderly_count * 1.0
        score += self.pregnant_count * 1.0
        score += self.children_count * 0.8
        return min(5.0, round(score, 2))

    def summary(self) -> str:
        parts = []
        if self.infants_count: parts.append(f"{self.infants_count} Infant(s)")
        if self.children_count: parts.append(f"{self.children_count} Child(ren)")
        if self.elderly_count: parts.append(f"{self.elderly_count} Elderly")
        if self.disabled_count: parts.append(f"{self.disabled_count} Disabled")
        if self.pregnant_count: parts.append(f"{self.pregnant_count} Pregnant")
        return ", ".join(parts) if parts else "Adults only"


@dataclass
class DEPIBreakdown:
    """Transparent algorithmic breakdown of the DEPI score for review defense."""
    medical_component: float
    environmental_component: float
    vulnerability_component: float
    wait_time_minutes: float
    wait_time_component: float
    total_score: float
    category: TriageCategory
    formula_expression: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "medical_component": round(self.medical_component, 2),
            "environmental_component": round(self.environmental_component, 2),
            "vulnerability_component": round(self.vulnerability_component, 2),
            "wait_time_minutes": round(self.wait_time_minutes, 1),
            "wait_time_component": round(self.wait_time_component, 2),
            "total_score": round(self.total_score, 2),
            "category": self.category.value,
            "formula_expression": self.formula_expression,
        }


@dataclass
class DistressCall:
    """Represents an emergency distress call logged into the triage router."""
    id: str = field(default_factory=lambda: f"CALL-{uuid.uuid4().hex[:6].upper()}")
    caller_name: str = "Anonymous"
    phone: str = "N/A"
    location: str = "Central District"
    coordinates: tuple = (22.5726, 88.3639) # Default geo-coordinates (Lat, Lon)
    
    # 4 Key DEPI variables as specified in the Abstract
    medical_urgency: int = 5         # Scale 1-10 (10 = cardiac arrest / asphyxiation)
    environmental_hazard: int = 5    # Scale 1-10 (10 = rising floodwaters / active chemical fire)
    vulnerability: VulnerabilityProfile = field(default_factory=VulnerabilityProfile)
    created_timestamp: float = field(default_factory=time.time)
    
    # Incident Narrative
    disaster_type: str = "General Emergency"
    description: str = ""
    
    # Dispatch & Operational State
    status: str = "QUEUED"           # QUEUED, DISPATCHED, RESOLVED, CANCELLED
    assigned_unit: Optional[str] = None
    dispatched_at: Optional[float] = None
    resolved_at: Optional[float] = None
    
    # Computed Dynamic Priority
    current_depi: float = 0.0
    depi_breakdown: Optional[DEPIBreakdown] = None

    def get_wait_time_minutes(self, current_time: Optional[float] = None) -> float:
        """Returns elapsed wait time in minutes since the call arrived."""
        if self.status != "QUEUED" and self.dispatched_at is not None:
            reference_time = self.dispatched_at
        else:
            reference_time = current_time if current_time is not None else time.time()
        elapsed_seconds = max(0.0, reference_time - self.created_timestamp)
        return elapsed_seconds / 60.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "caller_name": self.caller_name,
            "phone": self.phone,
            "location": self.location,
            "coordinates": self.coordinates,
            "medical_urgency": self.medical_urgency,
            "environmental_hazard": self.environmental_hazard,
            "vulnerability": self.vulnerability.summary(),
            "vulnerability_score": self.vulnerability.compute_factor(),
            "created_time": datetime.fromtimestamp(self.created_timestamp).strftime("%H:%M:%S"),
            "wait_time_minutes": round(self.get_wait_time_minutes(), 1),
            "disaster_type": self.disaster_type,
            "description": self.description,
            "status": self.status,
            "assigned_unit": self.assigned_unit or "None",
            "current_depi": round(self.current_depi, 2),
            "category": self.depi_breakdown.category.value if self.depi_breakdown else "CODE_YELLOW",
            "breakdown": self.depi_breakdown.to_dict() if self.depi_breakdown else {}
        }
