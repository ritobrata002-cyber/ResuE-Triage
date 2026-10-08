"""
Emergency Resource Dispatch Router & Unit Management.
Allocates emergency service vehicles based on DEPI severity and disaster type.
Tracks dispatch status, ETAs, and unit availability.
"""

from typing import List, Dict, Optional, Any
import time
from config import AVAILABLE_UNITS
from core.data_models import DistressCall


class DispatchUnitManager:
    """Manages the status and assignment of emergency response fleet."""

    def __init__(self, unit_definitions: List[Dict[str, Any]] = None):
        self.units: Dict[str, Dict[str, Any]] = {}
        for u in (unit_definitions or AVAILABLE_UNITS):
            self.units[u["id"]] = {
                "id": u["id"],
                "name": u["name"],
                "type": u["type"],
                "status": "AVAILABLE", # AVAILABLE, DISPATCHED, RETURNING
                "current_incident_id": None,
                "dispatched_at": None,
                "eta_minutes": None
            }

    def get_available_units(self, filter_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns list of units currently ready for dispatch."""
        available = [u for u in self.units.values() if u["status"] == "AVAILABLE"]
        if filter_type:
            available = [u for u in available if filter_type.lower() in u["type"].lower()]
        return available

    def suggest_optimal_unit(self, call: DistressCall) -> Optional[Dict[str, Any]]:
        """
        Heuristic rule-based unit recommendation based on disaster nature and DEPI.
        """
        available = self.get_available_units()
        if not available:
            return None

        disaster_type = call.disaster_type.lower()
        depi = call.current_depi

        # 1. Swift Water / Flood -> Boat first
        if "flood" in disaster_type or "water" in disaster_type:
            boat = next((u for u in available if "boat" in u["type"].lower() or "water" in u["type"].lower()), None)
            if boat: return boat

        # 2. Fire / Collapse -> Fire or SAR
        if "fire" in disaster_type:
            fire = next((u for u in available if "fire" in u["type"].lower()), None)
            if fire: return fire

        if "earthquake" in disaster_type or "collapse" in disaster_type:
            sar = next((u for u in available if "sar" in u["type"].lower() or "collapse" in u["type"].lower()), None)
            if sar: return sar

        # 3. Critical Trauma (DEPI >= 80) -> Heli or ALS Ambulance
        if depi >= 80.0:
            heli = next((u for u in available if "heli" in u["type"].lower() or "air" in u["type"].lower()), None)
            if heli: return heli
            als = next((u for u in available if "advanced" in u["name"].lower() or "als" in u["name"].lower()), None)
            if als: return als

        # Default: First available medical or general unit
        return available[0]

    def dispatch_unit(self, unit_id: str, incident_id: str, eta_minutes: float = 8.5) -> bool:
        """Marks unit as dispatched to an incident."""
        if unit_id not in self.units:
            return False
        unit = self.units[unit_id]
        if unit["status"] != "AVAILABLE":
            return False

        unit["status"] = "DISPATCHED"
        unit["current_incident_id"] = incident_id
        unit["dispatched_at"] = time.time()
        unit["eta_minutes"] = eta_minutes
        return True

    def release_unit(self, unit_id: str) -> bool:
        """Returns unit to available pool."""
        if unit_id not in self.units:
            return False
        unit = self.units[unit_id]
        unit["status"] = "AVAILABLE"
        unit["current_incident_id"] = None
        unit["dispatched_at"] = None
        unit["eta_minutes"] = None
        return True

    def reset_all(self) -> None:
        """Resets all fleet units to available."""
        for u in self.units.values():
            u["status"] = "AVAILABLE"
            u["current_incident_id"] = None
            u["dispatched_at"] = None
            u["eta_minutes"] = None
