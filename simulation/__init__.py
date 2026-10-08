"""Simulation module for RescuE-Triage."""
from simulation.scenario_generator import DISASTER_PRESETS, load_preset_scenario
from simulation.dispatch_router import DispatchUnitManager
from simulation.live_call_stream import generate_single_random_call

__all__ = [
    "DISASTER_PRESETS",
    "load_preset_scenario",
    "DispatchUnitManager",
    "generate_single_random_call"
]
