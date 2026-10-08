"""
Lightweight Zero-Dependency Web Server for RescuE-Triage.
Built on Python's standard library http.server module (works out-of-the-box on any Python installation).
Provides REST endpoints and serves the modern Dispatch Command Center Web Dashboard.
"""

import sys
import os
import json
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.data_models import DistressCall, VulnerabilityProfile
from core.depi_engine import DEPIEngine
from core.priority_queue import DynamicTriageRouter
from simulation.scenario_generator import load_preset_scenario, DISASTER_PRESETS
from simulation.dispatch_router import DispatchUnitManager
from simulation.live_call_stream import generate_single_random_call
from storage.persistence import TriageStorageManager
from core.benchmark import run_algorithmic_benchmark

# Shared state
ROUTER = DynamicTriageRouter()
UNIT_MANAGER = DispatchUnitManager()
STORAGE_MGR = TriageStorageManager()
ENGINE = DEPIEngine()
VIRTUAL_CLOCK = time.time()

# Preload initial urban flood scenario
for call in load_preset_scenario("urban_flood", reference_time=VIRTUAL_CLOCK):
    ROUTER.submit_call(call, current_time=VIRTUAL_CLOCK)

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


class RescuETriageAPIHandler(SimpleHTTPRequestHandler):
    """Handles REST API requests and serves static web dashboard files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json_response(self, data: dict, status_code: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        global VIRTUAL_CLOCK
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Advance virtual clock slightly to simulate time progress
        VIRTUAL_CLOCK += 1.0
        ROUTER.tick(current_time=VIRTUAL_CLOCK)

        if path == "/api/status":
            queued = ROUTER.priority_queue.get_sorted_queue()
            dispatched = list(ROUTER.active_dispatches.values())
            summary = STORAGE_MGR.generate_executive_summary(queued, dispatched, ROUTER.resolved_calls)
            self._send_json_response({
                "summary": summary,
                "queued": [c.to_dict() for c in queued],
                "dispatched": [c.to_dict() for c in dispatched],
                "resolved": [c.to_dict() for c in ROUTER.resolved_calls[-10:]],
                "units": list(UNIT_MANAGER.units.values()),
                "clock": time.strftime("%H:%M:%S", time.localtime(VIRTUAL_CLOCK))
            })
            return

        elif path == "/api/benchmark":
            results = run_algorithmic_benchmark([500, 2000, 5000])
            self._send_json_response({"benchmark": results})
            return

        # Default: Serve static files
        super().do_GET()

    def do_POST(self):
        global VIRTUAL_CLOCK, ROUTER, UNIT_MANAGER
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(post_data)
        except Exception:
            payload = {}

        if path == "/api/call/new":
            caller = payload.get("caller_name", "Anonymous")
            location = payload.get("location", "Central Sector")
            med = int(payload.get("medical_urgency", 5))
            env = int(payload.get("environmental_hazard", 5))
            disaster = payload.get("disaster_type", "General Emergency")
            desc = payload.get("description", "")
            
            vuln_data = payload.get("vulnerability", {})
            vuln = VulnerabilityProfile(
                infants_count=int(vuln_data.get("infants", 0)),
                children_count=int(vuln_data.get("children", 0)),
                elderly_count=int(vuln_data.get("elderly", 0)),
                disabled_count=int(vuln_data.get("disabled", 0)),
                pregnant_count=int(vuln_data.get("pregnant", 0)),
            )

            call = DistressCall(
                caller_name=caller,
                phone=payload.get("phone", "+91-98000-00000"),
                location=location,
                medical_urgency=med,
                environmental_hazard=env,
                vulnerability=vuln,
                disaster_type=disaster,
                description=desc,
                created_timestamp=VIRTUAL_CLOCK,
                status="QUEUED"
            )
            ROUTER.submit_call(call, current_time=VIRTUAL_CLOCK)
            self._send_json_response({"status": "success", "call": call.to_dict()})
            return

        elif path == "/api/dispatch/top":
            top = ROUTER.priority_queue.peek_max()
            if not top:
                self._send_json_response({"error": "No calls in queue"}, 400)
                return

            unit = UNIT_MANAGER.suggest_optimal_unit(top)
            if not unit:
                self._send_json_response({"error": "All emergency units currently busy"}, 400)
                return

            UNIT_MANAGER.dispatch_unit(unit["id"], top.id)
            dispatched = ROUTER.dispatch_top(unit["id"], current_time=VIRTUAL_CLOCK)
            self._send_json_response({"status": "dispatched", "call": dispatched.to_dict(), "unit": unit})
            return

        elif path == "/api/scenario/load":
            preset_key = payload.get("preset", "urban_flood")
            calls = load_preset_scenario(preset_key, reference_time=VIRTUAL_CLOCK)
            for c in calls:
                ROUTER.submit_call(c, current_time=VIRTUAL_CLOCK)
            self._send_json_response({"status": "loaded", "count": len(calls), "preset": preset_key})
            return

        elif path == "/api/call/random":
            rand_call = generate_single_random_call()
            rand_call.created_timestamp = VIRTUAL_CLOCK
            ROUTER.submit_call(rand_call, current_time=VIRTUAL_CLOCK)
            self._send_json_response({"status": "random_added", "call": rand_call.to_dict()})
            return

        elif path == "/api/call/resolve":
            call_id = payload.get("call_id")
            resolved = ROUTER.resolve_call(call_id, current_time=VIRTUAL_CLOCK)
            if resolved and resolved.assigned_unit:
                UNIT_MANAGER.release_unit(resolved.assigned_unit)
            self._send_json_response({"status": "resolved", "call_id": call_id})
            return

        elif path == "/api/reset":
            ROUTER = DynamicTriageRouter()
            UNIT_MANAGER = DispatchUnitManager()
            self._send_json_response({"status": "reset"})
            return

        self._send_json_response({"error": "Not Found"}, 404)


def start_web_server(port: int = 8080):
    server = HTTPServer(("0.0.0.0", port), RescuETriageAPIHandler)
    print(f"\n=======================================================")
    print(f"  RescuE-Triage Web Command Center Running")
    print(f"  Access Dashboard at: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server.")
        server.server_close()


if __name__ == "__main__":
    start_web_server(8080)
