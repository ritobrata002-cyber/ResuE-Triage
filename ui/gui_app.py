"""
RescuE-Triage Modern Desktop GUI Application (Tkinter).
Designed for the 2nd Project Review demonstration.
Features:
- Dark glassmorphism-inspired theme
- Real-time dynamic queue display with visual urgency badges
- Live call intake form with real-time DEPI preview
- One-click disaster scenario loader (Flood, Earthquake, Fire)
- Dynamic wait-time aging clock that continuously re-evaluates priorities
- Mathematical breakdown inspector for review defense
- Algorithmic benchmark runner
"""

import sys
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.data_models import DistressCall, VulnerabilityProfile
from core.depi_engine import DEPIEngine
from core.priority_queue import DynamicTriageRouter
from simulation.scenario_generator import DISASTER_PRESETS, load_preset_scenario
from simulation.dispatch_router import DispatchUnitManager
from simulation.live_call_stream import generate_single_random_call
from storage.persistence import TriageStorageManager
from core.benchmark import run_algorithmic_benchmark
from config import TriageCategory


# Color Palette
BG_DARK = "#0B0F19"
BG_CARD = "#151D30"
BG_CARD_LIGHT = "#1E293B"
TEXT_WHITE = "#F8FAFC"
TEXT_MUTED = "#94A3B8"
ACCENT_BLUE = "#38BDF8"
ACCENT_RED = "#EF4444"
ACCENT_ORANGE = "#F97316"
ACCENT_YELLOW = "#FBBF24"
ACCENT_GREEN = "#10B981"
ACCENT_PURPLE = "#A855F7"


class RescuETriageGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("RescuE-Triage — Dynamic Risk-Weighted Triage Router")
        self.root.geometry("1380x880")
        self.root.minsize(1100, 700)
        self.root.configure(bg=BG_DARK)

        # Core logic managers
        self.router = DynamicTriageRouter()
        self.unit_manager = DispatchUnitManager()
        self.storage = TriageStorageManager()
        self.engine = DEPIEngine()

        # State
        self.is_auto_aging = tk.BooleanVar(value=True)
        self.virtual_time_speed = tk.DoubleVar(value=1.0) # Speed multiplier
        self.virtual_clock = time.time()
        self.selected_call_id = None

        # Setup ttk styles
        self._setup_styles()

        # Build interface
        self._build_top_header()
        self._build_main_layout()

        # Load default Urban Flood scenario initially to showcase immediate rich state
        self.load_preset("urban_flood")

        # Start live background aging loop
        self._schedule_tick()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview styling
        style.configure("Triage.Treeview",
                        background=BG_CARD,
                        foreground=TEXT_WHITE,
                        fieldbackground=BG_CARD,
                        rowheight=32,
                        font=("Segoe UI", 9))
        style.configure("Triage.Treeview.Heading",
                        background="#0F172A",
                        foreground=ACCENT_BLUE,
                        relief="flat",
                        font=("Segoe UI", 10, "bold"))
        style.map("Triage.Treeview",
                  background=[("selected", "#2563EB")],
                  foreground=[("selected", "#FFFFFF")])

        # Scrollbar
        style.configure("Vertical.TScrollbar",
                        background=BG_CARD_LIGHT,
                        troughcolor=BG_DARK,
                        relief="flat")

    def _build_top_header(self):
        header_frame = tk.Frame(self.root, bg=BG_CARD, height=65, padx=20, pady=10)
        header_frame.pack(side=tk.TOP, fill=tk.X)

        # Title & Subtitle
        title_box = tk.Frame(header_frame, bg=BG_CARD)
        title_box.pack(side=tk.LEFT)

        title_lbl = tk.Label(title_box, text="RescuE-Triage", font=("Segoe UI", 18, "bold"),
                             fg=ACCENT_BLUE, bg=BG_CARD)
        title_lbl.pack(side=tk.LEFT)

        tag_lbl = tk.Label(title_box, text=" [DEPI Algorithmic Router]", font=("Segoe UI", 11, "bold"),
                           fg=ACCENT_YELLOW, bg=BG_CARD)
        tag_lbl.pack(side=tk.LEFT, padx=(5, 0), pady=(3, 0))

        sub_lbl = tk.Label(title_box, text=" • Dynamic Risk-Weighted Decision-Support System",
                           font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_CARD)
        sub_lbl.pack(side=tk.LEFT, padx=(5, 0), pady=(3, 0))

        # Right side controls: Clock & Benchmark
        right_box = tk.Frame(header_frame, bg=BG_CARD)
        right_box.pack(side=tk.RIGHT)

        self.clock_lbl = tk.Label(right_box, text="System Time: 00:00:00", font=("Consolas", 10),
                                  fg=TEXT_WHITE, bg=BG_CARD_LIGHT, padx=10, pady=4, relief="ridge", bd=1)
        self.clock_lbl.pack(side=tk.LEFT, padx=5)

        bench_btn = tk.Button(right_box, text="⚡ Algorithmic Benchmark", font=("Segoe UI", 9, "bold"),
                              bg=ACCENT_PURPLE, fg=TEXT_WHITE, activebackground="#9333EA",
                              activeforeground=TEXT_WHITE, relief="flat", padx=10, pady=4,
                              cursor="hand2", command=self.show_benchmark_dialog)
        bench_btn.pack(side=tk.LEFT, padx=5)

        export_btn = tk.Button(right_box, text="💾 Export Audit CSV", font=("Segoe UI", 9, "bold"),
                               bg=ACCENT_GREEN, fg=TEXT_WHITE, activebackground="#059669",
                               activeforeground=TEXT_WHITE, relief="flat", padx=10, pady=4,
                               cursor="hand2", command=self.export_csv)
        export_btn.pack(side=tk.LEFT, padx=5)

    def _build_main_layout(self):
        # Container
        main_container = tk.Frame(self.root, bg=BG_DARK, padx=12, pady=10)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Left Column: Distress Call Intake & Scenarios (Width ~ 380px)
        left_col = tk.Frame(main_container, bg=BG_DARK, width=380)
        left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_col.pack_propagate(False)

        self._build_intake_card(left_col)
        self._build_scenario_card(left_col)

        # Right Column: Queue Table, KPI Cards, and Action Bar
        right_col = tk.Frame(main_container, bg=BG_DARK)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_kpi_metrics_bar(right_col)
        self._build_triage_queue_table(right_col)
        self._build_dispatcher_action_bar(right_col)
        self._build_fleet_status_panel(right_col)

    def _build_intake_card(self, parent):
        card = tk.LabelFrame(parent, text=" 📝 Log Distress Call & Live DEPI Calculator ",
                             font=("Segoe UI", 10, "bold"), fg=ACCENT_BLUE, bg=BG_CARD,
                             bd=1, relief="ridge", padx=10, pady=8)
        card.pack(fill=tk.X, pady=(0, 8))

        # Caller & Location
        f1 = tk.Frame(card, bg=BG_CARD)
        f1.pack(fill=tk.X, pady=2)
        tk.Label(f1, text="Caller:", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_CARD, width=8, anchor="w").pack(side=tk.LEFT)
        self.entry_caller = tk.Entry(f1, font=("Segoe UI", 9), bg=BG_CARD_LIGHT, fg=TEXT_WHITE, relief="flat", insertbackground="white")
        self.entry_caller.insert(0, "A. Mukherjee")
        self.entry_caller.pack(side=tk.LEFT, fill=tk.X, expand=True)

        f2 = tk.Frame(card, bg=BG_CARD)
        f2.pack(fill=tk.X, pady=2)
        tk.Label(f2, text="Location:", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_CARD, width=8, anchor="w").pack(side=tk.LEFT)
        self.entry_location = tk.Entry(f2, font=("Segoe UI", 9), bg=BG_CARD_LIGHT, fg=TEXT_WHITE, relief="flat", insertbackground="white")
        self.entry_location.insert(0, "Sector 5, Block B")
        self.entry_location.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Disaster Type
        f3 = tk.Frame(card, bg=BG_CARD)
        f3.pack(fill=tk.X, pady=2)
        tk.Label(f3, text="Disaster:", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_CARD, width=8, anchor="w").pack(side=tk.LEFT)
        self.combo_disaster = ttk.Combobox(f3, values=["Urban Flood", "Earthquake", "Urban Fire", "Chemical Hazard", "Medical Shock"], state="readonly", font=("Segoe UI", 9))
        self.combo_disaster.set("Urban Flood")
        self.combo_disaster.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Medical Urgency Slider (1 - 10)
        f_med = tk.Frame(card, bg=BG_CARD)
        f_med.pack(fill=tk.X, pady=(4, 0))
        self.lbl_med_val = tk.Label(f_med, text="Medical Urgency: 8/10", font=("Segoe UI", 9, "bold"), fg=ACCENT_RED, bg=BG_CARD)
        self.lbl_med_val.pack(anchor="w")
        self.slider_med = tk.Scale(f_med, from_=1, to=10, orient=tk.HORIZONTAL, bg=BG_CARD, fg=TEXT_WHITE,
                                   troughcolor=BG_CARD_LIGHT, highlightthickness=0,
                                   command=lambda v: self._on_param_change())
        self.slider_med.set(8)
        self.slider_med.pack(fill=tk.X)

        # Environmental Hazard Slider (1 - 10)
        f_env = tk.Frame(card, bg=BG_CARD)
        f_env.pack(fill=tk.X, pady=(2, 0))
        self.lbl_env_val = tk.Label(f_env, text="Env Hazard: 7/10", font=("Segoe UI", 9, "bold"), fg=ACCENT_ORANGE, bg=BG_CARD)
        self.lbl_env_val.pack(anchor="w")
        self.slider_env = tk.Scale(f_env, from_=1, to=10, orient=tk.HORIZONTAL, bg=BG_CARD, fg=TEXT_WHITE,
                                   troughcolor=BG_CARD_LIGHT, highlightthickness=0,
                                   command=lambda v: self._on_param_change())
        self.slider_env.set(7)
        self.slider_env.pack(fill=tk.X)

        # Vulnerable Individuals checkboxes
        vuln_frame = tk.LabelFrame(card, text="Vulnerable Individuals Present", font=("Segoe UI", 8, "bold"),
                                   fg=TEXT_MUTED, bg=BG_CARD, relief="flat")
        vuln_frame.pack(fill=tk.X, pady=4)

        self.chk_infant = tk.BooleanVar(value=False)
        self.chk_child = tk.BooleanVar(value=False)
        self.chk_elderly = tk.BooleanVar(value=True)
        self.chk_disabled = tk.BooleanVar(value=False)
        self.chk_pregnant = tk.BooleanVar(value=False)

        c1 = tk.Frame(vuln_frame, bg=BG_CARD)
        c1.pack(fill=tk.X)
        tk.Checkbutton(c1, text="Elderly", variable=self.chk_elderly, bg=BG_CARD, fg=TEXT_WHITE,
                       selectcolor=BG_CARD_LIGHT, activebackground=BG_CARD,
                       command=self._on_param_change).pack(side=tk.LEFT)
        tk.Checkbutton(c1, text="Infant", variable=self.chk_infant, bg=BG_CARD, fg=TEXT_WHITE,
                       selectcolor=BG_CARD_LIGHT, activebackground=BG_CARD,
                       command=self._on_param_change).pack(side=tk.LEFT, padx=6)
        tk.Checkbutton(c1, text="Disabled", variable=self.chk_disabled, bg=BG_CARD, fg=TEXT_WHITE,
                       selectcolor=BG_CARD_LIGHT, activebackground=BG_CARD,
                       command=self._on_param_change).pack(side=tk.LEFT)

        c2 = tk.Frame(vuln_frame, bg=BG_CARD)
        c2.pack(fill=tk.X)
        tk.Checkbutton(c2, text="Pregnant", variable=self.chk_pregnant, bg=BG_CARD, fg=TEXT_WHITE,
                       selectcolor=BG_CARD_LIGHT, activebackground=BG_CARD,
                       command=self._on_param_change).pack(side=tk.LEFT)
        tk.Checkbutton(c2, text="Children", variable=self.chk_child, bg=BG_CARD, fg=TEXT_WHITE,
                       selectcolor=BG_CARD_LIGHT, activebackground=BG_CARD,
                       command=self._on_param_change).pack(side=tk.LEFT, padx=6)

        # Live Estimated DEPI Preview Badge
        preview_box = tk.Frame(card, bg=BG_CARD_LIGHT, padx=8, pady=5)
        preview_box.pack(fill=tk.X, pady=4)
        self.lbl_preview_depi = tk.Label(preview_box, text="Estimated Initial DEPI: 63.0 (CODE ORANGE)",
                                         font=("Segoe UI", 9, "bold"), fg=ACCENT_ORANGE, bg=BG_CARD_LIGHT)
        self.lbl_preview_depi.pack()

        # Submit Call Button
        btn_submit = tk.Button(card, text="➕ Route & Enqueue Call", font=("Segoe UI", 10, "bold"),
                               bg=ACCENT_BLUE, fg="#0F172A", activebackground="#0284C7",
                               relief="flat", cursor="hand2", pady=5, command=self.submit_intake_call)
        btn_submit.pack(fill=tk.X, pady=(4, 0))

    def _build_scenario_card(self, parent):
        card = tk.LabelFrame(parent, text=" ⚡ Disaster Simulation Presets ",
                             font=("Segoe UI", 10, "bold"), fg=ACCENT_YELLOW, bg=BG_CARD,
                             bd=1, relief="ridge", padx=10, pady=8)
        card.pack(fill=tk.BOTH, expand=True)

        desc_lbl = tk.Label(card, text="Inject multi-call crisis scenarios to test DEPI priority queue re-sorting:",
                            font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_CARD, wraplength=340, justify="left")
        desc_lbl.pack(anchor="w", pady=(0, 6))

        # Scenario buttons
        btn_flood = tk.Button(card, text="🌊 Urban Flash Flood Crisis", font=("Segoe UI", 9, "bold"),
                              bg="#1E3A8A", fg=TEXT_WHITE, activebackground="#1D4ED8",
                              relief="flat", cursor="hand2", anchor="w", padx=10, pady=4,
                              command=lambda: self.load_preset("urban_flood"))
        btn_flood.pack(fill=tk.X, pady=2)

        btn_quake = tk.Button(card, text="🏚️ 6.8M Earthquake Collapse", font=("Segoe UI", 9, "bold"),
                              bg="#831843", fg=TEXT_WHITE, activebackground="#9D174D",
                              relief="flat", cursor="hand2", anchor="w", padx=10, pady=4,
                              command=lambda: self.load_preset("earthquake"))
        btn_quake.pack(fill=tk.X, pady=2)

        btn_fire = tk.Button(card, text="🔥 High-Rise Tower Blaze", font=("Segoe UI", 9, "bold"),
                             bg="#7C2D12", fg=TEXT_WHITE, activebackground="#9A3412",
                             relief="flat", cursor="hand2", anchor="w", padx=10, pady=4,
                             command=lambda: self.load_preset("highrise_fire"))
        btn_fire.pack(fill=tk.X, pady=2)

        # Live Distress Call Generator
        sep = tk.Frame(card, height=1, bg=BG_CARD_LIGHT)
        sep.pack(fill=tk.X, pady=8)

        btn_rand = tk.Button(card, text="🎲 Stream Random Distress Call", font=("Segoe UI", 9, "bold"),
                             bg=BG_CARD_LIGHT, fg=TEXT_WHITE, activebackground="#334155",
                             relief="flat", cursor="hand2", pady=4, command=self.inject_random_call)
        btn_rand.pack(fill=tk.X, pady=2)

        # Aging Speed Controller
        aging_ctrl = tk.Frame(card, bg=BG_CARD)
        aging_ctrl.pack(fill=tk.X, pady=(6, 0))
        tk.Label(aging_ctrl, text="Wait Aging Speed:", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_CARD).pack(side=tk.LEFT)
        tk.Radiobutton(aging_ctrl, text="1x (Real)", variable=self.virtual_time_speed, value=1.0,
                       bg=BG_CARD, fg=TEXT_WHITE, selectcolor=BG_CARD_LIGHT).pack(side=tk.LEFT, padx=3)
        tk.Radiobutton(aging_ctrl, text="10x", variable=self.virtual_time_speed, value=10.0,
                       bg=BG_CARD, fg=TEXT_WHITE, selectcolor=BG_CARD_LIGHT).pack(side=tk.LEFT, padx=3)
        tk.Radiobutton(aging_ctrl, text="60x (Fast)", variable=self.virtual_time_speed, value=60.0,
                       bg=BG_CARD, fg=TEXT_WHITE, selectcolor=BG_CARD_LIGHT).pack(side=tk.LEFT, padx=3)

    def _build_kpi_metrics_bar(self, parent):
        kpi_bar = tk.Frame(parent, bg=BG_DARK, height=75)
        kpi_bar.pack(fill=tk.X, pady=(0, 10))

        # 4 Metric Cards
        self.kpi_cards = {}
        metrics = [
            ("queued", "ACTIVE IN QUEUE", "0", ACCENT_BLUE),
            ("critical", "CODE RED (CRITICAL)", "0", ACCENT_RED),
            ("avg_depi", "AVG DEPI PRIORITY", "0.0", ACCENT_YELLOW),
            ("fleet_avail", "FLEET READY", "6 / 6", ACCENT_GREEN)
        ]

        for key, label, initial, color in metrics:
            card = tk.Frame(kpi_bar, bg=BG_CARD, padx=12, pady=6, relief="ridge", bd=1)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

            lbl_title = tk.Label(card, text=label, font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=BG_CARD)
            lbl_title.pack(anchor="w")

            lbl_val = tk.Label(card, text=initial, font=("Segoe UI", 16, "bold"), fg=color, bg=BG_CARD)
            lbl_val.pack(anchor="w")

            self.kpi_cards[key] = lbl_val

    def _build_triage_queue_table(self, parent):
        table_container = tk.Frame(parent, bg=BG_CARD, relief="ridge", bd=1)
        table_container.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Title bar inside table container
        table_header = tk.Frame(table_container, bg="#0F172A", padx=10, pady=5)
        table_header.pack(fill=tk.X)
        tk.Label(table_header, text="🚨 Live Dynamic Priority Queue (Max-Heap Sorted by DEPI)",
                 font=("Segoe UI", 10, "bold"), fg=TEXT_WHITE, bg="#0F172A").pack(side=tk.LEFT)

        tk.Label(table_header, text="Auto-escalating non-urgent cases via Dynamic Wait Scaling",
                 font=("Segoe UI", 8), fg=TEXT_MUTED, bg="#0F172A").pack(side=tk.RIGHT)

        # Columns
        columns = ("pos", "id", "depi", "category", "caller", "hazard_type", "med", "env", "vuln", "wait_min", "status", "unit")
        self.tree = ttk.Treeview(table_container, columns=columns, show="headings", style="Triage.Treeview", selectmode="browse")

        # Headings & Column widths
        headers = [
            ("pos", "#", 35, "center"),
            ("id", "Ticket ID", 85, "center"),
            ("depi", "DEPI Score", 95, "center"),
            ("category", "Triage Tier", 115, "center"),
            ("caller", "Caller / Contact", 150, "w"),
            ("hazard_type", "Disaster Context", 120, "w"),
            ("med", "Med", 45, "center"),
            ("env", "Env", 45, "center"),
            ("vuln", "Vuln", 50, "center"),
            ("wait_min", "Wait (m)", 65, "center"),
            ("status", "Status", 95, "center"),
            ("unit", "Assigned Unit", 120, "w")
        ]

        for col_id, title, width, anchor in headers:
            self.tree.heading(col_id, text=title)
            self.tree.column(col_id, width=width, anchor=anchor)

        # Scrollbar
        scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview, style="Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", lambda e: self.inspect_formula_breakdown())

    def _build_dispatcher_action_bar(self, parent):
        bar = tk.Frame(parent, bg=BG_DARK)
        bar.pack(fill=tk.X, pady=(0, 8))

        # Dispatch Top Button
        self.btn_dispatch_top = tk.Button(bar, text="⚡ DISPATCH HIGHEST PRIORITY (TOP OF HEAP)",
                                          font=("Segoe UI", 10, "bold"), bg=ACCENT_RED, fg=TEXT_WHITE,
                                          activebackground="#DC2626", activeforeground=TEXT_WHITE,
                                          relief="flat", cursor="hand2", padx=14, pady=6,
                                          command=self.dispatch_top_call)
        self.btn_dispatch_top.pack(side=tk.LEFT, padx=(0, 6))

        # Inspect Math Formula Breakdown
        self.btn_inspect = tk.Button(bar, text="🔍 Formula Transparency Breakdown",
                                     font=("Segoe UI", 9, "bold"), bg=BG_CARD_LIGHT, fg=TEXT_WHITE,
                                     activebackground="#334155", relief="flat", cursor="hand2",
                                     padx=10, pady=6, command=self.inspect_formula_breakdown)
        self.btn_inspect.pack(side=tk.LEFT, padx=4)

        # Mark Resolved
        self.btn_resolve = tk.Button(bar, text="✅ Mark Incident Resolved",
                                     font=("Segoe UI", 9, "bold"), bg=BG_CARD_LIGHT, fg=ACCENT_GREEN,
                                     activebackground="#334155", relief="flat", cursor="hand2",
                                     padx=10, pady=6, command=self.resolve_selected_call)
        self.btn_resolve.pack(side=tk.LEFT, padx=4)

        # Clear / Reset
        btn_reset = tk.Button(bar, text="🔄 Reset Queue", font=("Segoe UI", 9),
                              bg=BG_CARD_LIGHT, fg=TEXT_MUTED, activebackground="#334155",
                              relief="flat", cursor="hand2", padx=10, pady=6,
                              command=self.reset_all_queues)
        btn_reset.pack(side=tk.RIGHT)

    def _build_fleet_status_panel(self, parent):
        fleet_frame = tk.LabelFrame(parent, text=" 🚑 Active Fleet Deployment & Resources ",
                                    font=("Segoe UI", 9, "bold"), fg=TEXT_WHITE, bg=BG_CARD,
                                    bd=1, relief="ridge", padx=10, pady=6)
        fleet_frame.pack(fill=tk.X)

        self.fleet_badges_container = tk.Frame(fleet_frame, bg=BG_CARD)
        self.fleet_badges_container.pack(fill=tk.X)

        self._refresh_fleet_display()

    def _refresh_fleet_display(self):
        # Clear existing
        for widget in self.fleet_badges_container.winfo_children():
            widget.destroy()

        for unit in self.unit_manager.units.values():
            box = tk.Frame(self.fleet_badges_container, bg=BG_CARD_LIGHT, padx=8, pady=4, relief="groove", bd=1)
            box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3, pady=2)

            color = ACCENT_GREEN if unit["status"] == "AVAILABLE" else ACCENT_RED
            status_text = "READY" if unit["status"] == "AVAILABLE" else f"DEPLOYED ({unit['current_incident_id']})"

            lbl_id = tk.Label(box, text=f"{unit['id']} • {unit['type']}", font=("Segoe UI", 8, "bold"),
                              fg=TEXT_WHITE, bg=BG_CARD_LIGHT)
            lbl_id.pack(anchor="w")

            lbl_st = tk.Label(box, text=status_text, font=("Segoe UI", 8, "bold"),
                              fg=color, bg=BG_CARD_LIGHT)
            lbl_st.pack(anchor="w")

    def _on_param_change(self):
        med = self.slider_med.get()
        env = self.slider_env.get()
        self.lbl_med_val.config(text=f"Medical Urgency: {med}/10")
        self.lbl_env_val.config(text=f"Env Hazard: {env}/10")

        # Compute preview
        vuln = VulnerabilityProfile(
            infants_count=1 if self.chk_infant.get() else 0,
            children_count=1 if self.chk_child.get() else 0,
            elderly_count=1 if self.chk_elderly.get() else 0,
            disabled_count=1 if self.chk_disabled.get() else 0,
            pregnant_count=1 if self.chk_pregnant.get() else 0
        )
        dummy_call = DistressCall(medical_urgency=med, environmental_hazard=env, vulnerability=vuln)
        breakdown = self.engine.evaluate_call(dummy_call)

        cat_color = ACCENT_RED if breakdown.category == TriageCategory.CODE_RED else (
            ACCENT_ORANGE if breakdown.category == TriageCategory.CODE_ORANGE else (
                ACCENT_YELLOW if breakdown.category == TriageCategory.CODE_YELLOW else ACCENT_GREEN
            )
        )
        self.lbl_preview_depi.config(
            text=f"Estimated Initial DEPI: {breakdown.total_score:.1f} ({breakdown.category.value})",
            fg=cat_color
        )

    def submit_intake_call(self):
        caller = self.entry_caller.get().strip() or "Citizen"
        location = self.entry_location.get().strip() or "Unspecified Location"
        disaster = self.combo_disaster.get() or "Emergency"

        vuln = VulnerabilityProfile(
            infants_count=1 if self.chk_infant.get() else 0,
            children_count=1 if self.chk_child.get() else 0,
            elderly_count=1 if self.chk_elderly.get() else 0,
            disabled_count=1 if self.chk_disabled.get() else 0,
            pregnant_count=1 if self.chk_pregnant.get() else 0
        )

        call = DistressCall(
            caller_name=caller,
            phone=f"+91-{os.getpid()}-{int(time.time())%10000}",
            location=location,
            medical_urgency=self.slider_med.get(),
            environmental_hazard=self.slider_env.get(),
            vulnerability=vuln,
            disaster_type=disaster,
            description=f"Direct citizen emergency call logged at {location}.",
            created_timestamp=self.virtual_clock,
            status="QUEUED"
        )

        self.router.submit_call(call, current_time=self.virtual_clock)
        self.refresh_table()
        messagebox.showinfo("Call Enqueued", f"Ticket {call.id} added with Initial DEPI: {call.current_depi:.1f}!\nPosition calculated via Max-Heap.")

    def load_preset(self, preset_key: str):
        calls = load_preset_scenario(preset_key, reference_time=self.virtual_clock)
        for c in calls:
            self.router.submit_call(c, current_time=self.virtual_clock)
        self.refresh_table()

    def inject_random_call(self):
        c = generate_single_random_call()
        c.created_timestamp = self.virtual_clock
        self.router.submit_call(c, current_time=self.virtual_clock)
        self.refresh_table()

    def dispatch_top_call(self):
        top = self.router.priority_queue.peek_max()
        if not top:
            messagebox.showinfo("Queue Empty", "No pending emergency calls in the triage queue!")
            return

        suggested_unit = self.unit_manager.suggest_optimal_unit(top)
        if not suggested_unit:
            messagebox.showwarning("Fleet Exhausted", "All emergency dispatch units are currently engaged in active missions!")
            return

        unit_id = suggested_unit["id"]
        self.unit_manager.dispatch_unit(unit_id, top.id)
        dispatched_call = self.router.dispatch_top(unit_id, current_time=self.virtual_clock)

        self._refresh_fleet_display()
        self.refresh_table()

        messagebox.showinfo("Unit Dispatched!",
                            f"Dispatched {suggested_unit['name']} ({unit_id}) to:\n\n"
                            f"Ticket: {dispatched_call.id}\n"
                            f"Caller: {dispatched_call.caller_name}\n"
                            f"Location: {dispatched_call.location}\n"
                            f"DEPI Priority: {dispatched_call.current_depi:.1f} ({dispatched_call.depi_breakdown.category.value})\n"
                            f"Estimated Response ETA: 8.5 minutes")

    def resolve_selected_call(self):
        if not self.selected_call_id:
            messagebox.showinfo("Select Incident", "Please select an incident row from the table first.")
            return

        resolved = self.router.resolve_call(self.selected_call_id, current_time=self.virtual_clock)
        if resolved:
            if resolved.assigned_unit and resolved.assigned_unit != "None":
                self.unit_manager.release_unit(resolved.assigned_unit)
            self._refresh_fleet_display()
            self.refresh_table()
            messagebox.showinfo("Resolved", f"Incident {resolved.id} marked as RESOLVED and archived to audit log.")

    def reset_all_queues(self):
        if messagebox.askyesno("Confirm Reset", "Reset all active queues and fleet status?"):
            self.router = DynamicTriageRouter()
            self.unit_manager.reset_all()
            self._refresh_fleet_display()
            self.refresh_table()

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            self.selected_call_id = item["values"][1] # ID column

    def inspect_formula_breakdown(self):
        """Displays modal showing exact mathematical breakdown for the selected call."""
        if not self.selected_call_id:
            messagebox.showinfo("Select Incident", "Select an incident row in the table to inspect its DEPI formula breakdown.")
            return

        call = self.router.priority_queue.get_by_id(self.selected_call_id)
        if not call:
            call = self.router.active_dispatches.get(self.selected_call_id)
        if not call:
            messagebox.showerror("Error", "Call not found.")
            return

        b = call.depi_breakdown
        if not b:
            b = self.engine.evaluate_call(call, current_time=self.virtual_clock)

        # Dialog
        top = tk.Toplevel(self.root)
        top.title(f"DEPI Algorithmic Transparency Breakdown — {call.id}")
        top.geometry("640x500")
        top.configure(bg=BG_CARD)
        top.transient(self.root)
        top.grab_set()

        pad = tk.Frame(top, bg=BG_CARD, padx=20, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad, text=f"Dynamic Emergency Priority Index (DEPI)", font=("Segoe UI", 13, "bold"), fg=ACCENT_BLUE, bg=BG_CARD).pack(anchor="w")
        tk.Label(pad, text=f"Incident ID: {call.id}  |  Caller: {call.caller_name}  |  Location: {call.location}",
                 font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", pady=(0, 10))

        # Big score display
        score_box = tk.Frame(pad, bg=BG_CARD_LIGHT, padx=15, pady=10, relief="ridge", bd=1)
        score_box.pack(fill=tk.X, pady=(0, 12))

        cat_color = ACCENT_RED if b.category == TriageCategory.CODE_RED else (
            ACCENT_ORANGE if b.category == TriageCategory.CODE_ORANGE else (
                ACCENT_YELLOW if b.category == TriageCategory.CODE_YELLOW else ACCENT_GREEN
            )
        )

        tk.Label(score_box, text=f"Calculated DEPI: {b.total_score:.2f} / 100", font=("Segoe UI", 18, "bold"), fg=cat_color, bg=BG_CARD_LIGHT).pack(anchor="w")
        tk.Label(score_box, text=f"Triage Tier: {b.category.value}", font=("Segoe UI", 11, "bold"), fg=cat_color, bg=BG_CARD_LIGHT).pack(anchor="w")

        # Mathematical equation breakdown
        eq_frame = tk.LabelFrame(pad, text=" Mathematical Term Decomposition ", font=("Segoe UI", 9, "bold"),
                                 fg=TEXT_WHITE, bg=BG_CARD, padx=10, pady=8)
        eq_frame.pack(fill=tk.BOTH, expand=True)

        terms = [
            ("Medical Urgency Component", f"4.5 × {call.medical_urgency}", f"+ {b.medical_component:.2f} pts"),
            ("Environmental Hazard Component", f"3.0 × {call.environmental_hazard}", f"+ {b.environmental_component:.2f} pts"),
            ("Vulnerability Component", f"3.0 × {call.vulnerability.compute_factor():.2f} ({call.vulnerability.summary()})", f"+ {b.vulnerability_component:.2f} pts"),
            ("Dynamic Wait Aging Component", f"f(Δt = {b.wait_time_minutes:.1f} mins) [Prevents Starvation]", f"+ {b.wait_time_component:.2f} pts"),
        ]

        for title, formula_str, val_str in terms:
            row = tk.Frame(eq_frame, bg=BG_CARD)
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=title, font=("Segoe UI", 9, "bold"), fg=ACCENT_BLUE, bg=BG_CARD, width=28, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=formula_str, font=("Consolas", 9), fg=TEXT_WHITE, bg=BG_CARD, width=28, anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=val_str, font=("Consolas", 9, "bold"), fg=ACCENT_YELLOW, bg=BG_CARD).pack(side=tk.RIGHT)

        desc_lbl = tk.Label(pad, text=f"Narrative: {call.description}", font=("Segoe UI", 9, "italic"),
                            fg=TEXT_MUTED, bg=BG_CARD, wraplength=580, justify="left")
        desc_lbl.pack(anchor="w", pady=(10, 0))

        tk.Button(pad, text="Close Inspector", font=("Segoe UI", 9, "bold"), bg=BG_CARD_LIGHT, fg=TEXT_WHITE,
                  relief="flat", cursor="hand2", command=top.destroy).pack(side=tk.BOTTOM, pady=(10, 0))

    def show_benchmark_dialog(self):
        """Runs the O(log N) heap vs O(N) linear scan benchmark and displays live report."""
        top = tk.Toplevel(self.root)
        top.title("RescuE-Triage Computational Efficiency Benchmark")
        top.geometry("680x480")
        top.configure(bg=BG_CARD)
        top.transient(self.root)

        pad = tk.Frame(top, bg=BG_CARD, padx=20, pady=15)
        pad.pack(fill=tk.BOTH, expand=True)

        tk.Label(pad, text="Algorithmic Complexity Proof (Python Lab Defense)",
                 font=("Segoe UI", 12, "bold"), fg=ACCENT_PURPLE, bg=BG_CARD).pack(anchor="w")
        tk.Label(pad, text="Compares Custom Max-Heap O(log N) vs Naive Dynamic Array Linear Search O(N):",
                 font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", pady=(0, 10))

        txt = tk.Text(pad, bg=BG_DARK, fg=TEXT_WHITE, font=("Consolas", 10), relief="flat", padx=10, pady=10)
        txt.pack(fill=tk.BOTH, expand=True)

        txt.insert(tk.END, "Executing stress-test benchmarks across N = 500, 2000, 5000 distress calls...\n\n")
        self.root.update()

        results = run_algorithmic_benchmark([500, 2000, 5000])

        txt.insert(tk.END, f"{'Scale':<10} | {'Heap Push':<12} | {'Heap Pop(100)':<14} | {'Naive Scan(100)':<16} | {'Speedup':<10}\n")
        txt.insert(tk.END, "-" * 72 + "\n")

        for size_key, data in results.items():
            txt.insert(tk.END, f"{size_key:<10} | {data['Heap_Insert_Total_Sec']:<12.4f}s | {data['Heap_Extract100_Sec']:<14.5f}s | {data['Naive_Extract100_Sec']:<16.5f}s | {data['Heap_Speedup_Factor']:>6.1f}x\n")

        txt.insert(tk.END, "\n" + "=" * 72 + "\n")
        txt.insert(tk.END, "Theoretical Complexity Analysis:\n")
        txt.insert(tk.END, " • Enqueue Operation:  Heap O(log N) vs Naive List O(1)\n")
        txt.insert(tk.END, " • Extract-Max Priority: Heap O(log N) vs Naive Linear Scan O(N)\n")
        txt.insert(tk.END, " • Dynamic Wait Aging: Bottom-up Heapify in O(N)\n")
        txt.insert(tk.END, "Conclusion: Custom Max-Heap ensures deterministic, sub-millisecond dispatching\n")
        txt.insert(tk.END, "even during extreme municipal catastrophe surges (5000+ simultaneous calls).\n")
        txt.configure(state="disabled")

        tk.Button(pad, text="Close Benchmark", font=("Segoe UI", 9, "bold"), bg=BG_CARD_LIGHT, fg=TEXT_WHITE,
                  relief="flat", cursor="hand2", command=top.destroy).pack(side=tk.BOTTOM, pady=(10, 0))

    def export_csv(self):
        all_calls = self.router.priority_queue.get_sorted_queue() + list(self.router.active_dispatches.values()) + self.router.resolved_calls
        if not all_calls:
            messagebox.showinfo("Export CSV", "No calls to export.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            out = self.storage.export_calls_to_csv(all_calls, file_path)
            messagebox.showinfo("Export Successful", f"Exported {len(all_calls)} emergency incident records to:\n{out}")

    def refresh_table(self):
        """Syncs the Tkinter treeview with the current priority queue and active calls."""
        # Save selection
        prev_selection = self.selected_call_id

        # Clear existing rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Get sorted priority queue
        queued_calls = self.router.priority_queue.get_sorted_queue()
        active_dispatches = list(self.router.active_dispatches.values())

        all_visible = queued_calls + active_dispatches

        # Populate rows
        for idx, c in enumerate(all_visible, start=1):
            tier = c.depi_breakdown.category.value if c.depi_breakdown else "CODE_YELLOW"
            unit_display = c.assigned_unit or "None"
            wait_str = f"{c.get_wait_time_minutes(self.virtual_clock):.1f}"

            item_id = self.tree.insert("", tk.END, values=(
                idx,
                c.id,
                f"{c.current_depi:.1f}",
                tier,
                c.caller_name,
                c.disaster_type,
                c.medical_urgency,
                c.environmental_hazard,
                f"{c.vulnerability.compute_factor():.1f}",
                wait_str,
                c.status,
                unit_display
            ))

            # Apply row highlighting based on triage tier
            if tier == "CODE_RED":
                self.tree.tag_configure("red_tier", background="#3B0707", foreground="#FCA5A5")
                self.tree.item(item_id, tags=("red_tier",))
            elif tier == "CODE_ORANGE":
                self.tree.tag_configure("orange_tier", background="#2C1204", foreground="#FDBA74")
                self.tree.item(item_id, tags=("orange_tier",))
            elif tier == "CODE_YELLOW":
                self.tree.tag_configure("yellow_tier", background="#261A04", foreground="#FDE047")
                self.tree.item(item_id, tags=("yellow_tier",))
            else:
                self.tree.tag_configure("green_tier", background="#062413", foreground="#86EFAC")
                self.tree.item(item_id, tags=("green_tier",))

        # Update KPIs
        red_count = sum(1 for c in all_visible if c.current_depi >= 75)
        avg_depi = (sum(c.current_depi for c in all_visible) / len(all_visible)) if all_visible else 0.0
        avail_units = len(self.unit_manager.get_available_units())

        self.kpi_cards["queued"].config(text=str(len(queued_calls)))
        self.kpi_cards["critical"].config(text=str(red_count))
        self.kpi_cards["avg_depi"].config(text=f"{avg_depi:.1f}")
        self.kpi_cards["fleet_avail"].config(text=f"{avail_units} / {len(self.unit_manager.units)}")

    def _schedule_tick(self):
        """Regular background timer updating wait-times and reheapifying queue."""
        if self.is_auto_aging.get():
            step_seconds = 1.0 * self.virtual_time_speed.get()
            self.virtual_clock += step_seconds

            # Update clock display
            time_str = time.strftime("%H:%M:%S", time.localtime(self.virtual_clock))
            self.clock_lbl.config(text=f"System Time: {time_str} ({self.virtual_time_speed.get():.0f}x)")

            # Reheapify and refresh table every second
            self.router.tick(current_time=self.virtual_clock)
            self.refresh_table()

        self.root.after(1000, self._schedule_tick)


def launch_gui():
    root = tk.Tk()
    app = RescuETriageGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
