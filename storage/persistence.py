"""
Audit Trail & Incident Persistence for RescuE-Triage.
Saves and loads emergency call states to JSON and CSV formats for post-crisis analysis.
"""

import json
import csv
import os
import time
from typing import List, Dict, Any, Optional
from core.data_models import DistressCall, VulnerabilityProfile, DEPIBreakdown
from config import TriageCategory


class TriageStorageManager:
    """Handles persistent storage of distress calls and dispatch audit logs."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.audit_file = os.path.join(self.data_dir, "triage_audit_log.json")
        self.csv_export_file = os.path.join(self.data_dir, "dispatched_records.csv")

    def export_calls_to_csv(self, calls: List[DistressCall], file_path: Optional[str] = None) -> str:
        """Exports a list of distress calls to CSV."""
        path = file_path or self.csv_export_file
        fieldnames = [
            "ID", "Caller Name", "Phone", "Location", "Disaster Type",
            "Medical Urgency (1-10)", "Env Hazard (1-10)", "Vulnerability Score",
            "Wait Time (Mins)", "Final DEPI Score", "Triage Category", "Status",
            "Assigned Unit", "Created Time", "Description"
        ]

        with open(path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for c in calls:
                writer.writerow({
                    "ID": c.id,
                    "Caller Name": c.caller_name,
                    "Phone": c.phone,
                    "Location": c.location,
                    "Disaster Type": c.disaster_type,
                    "Medical Urgency (1-10)": c.medical_urgency,
                    "Env Hazard (1-10)": c.environmental_hazard,
                    "Vulnerability Score": c.vulnerability.compute_factor(),
                    "Wait Time (Mins)": round(c.get_wait_time_minutes(), 1),
                    "Final DEPI Score": round(c.current_depi, 2),
                    "Triage Category": c.depi_breakdown.category.value if c.depi_breakdown else "N/A",
                    "Status": c.status,
                    "Assigned Unit": c.assigned_unit or "None",
                    "Created Time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(c.created_timestamp)),
                    "Description": c.description
                })

        return path

    def generate_executive_summary(self, queued: List[DistressCall], dispatched: List[DistressCall], resolved: List[DistressCall]) -> Dict[str, Any]:
        """Calculates real-time KPIs and audit metrics for the control room."""
        all_calls = queued + dispatched + resolved
        total = len(all_calls)

        code_red = sum(1 for c in all_calls if c.current_depi >= 75)
        code_orange = sum(1 for c in all_calls if 55 <= c.current_depi < 75)
        code_yellow = sum(1 for c in all_calls if 35 <= c.current_depi < 55)
        code_green = sum(1 for c in all_calls if c.current_depi < 35)

        avg_depi = (sum(c.current_depi for c in all_calls) / total) if total > 0 else 0.0
        avg_wait = (sum(c.get_wait_time_minutes() for c in queued) / len(queued)) if queued else 0.0

        return {
            "total_incidents": total,
            "queued_count": len(queued),
            "dispatched_count": len(dispatched),
            "resolved_count": len(resolved),
            "code_red_critical": code_red,
            "code_orange_urgent": code_orange,
            "code_yellow_delayed": code_yellow,
            "code_green_minor": code_green,
            "avg_depi_score": round(avg_depi, 2),
            "avg_queue_wait_mins": round(avg_wait, 1),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
