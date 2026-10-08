# RescuE-Triage: Dynamic Risk-Weighted Triage Router in Python

### **Project Title**
**Algorithmic Prioritization System for Emergency Response: A Dynamic Risk-Weighted Triage Router in Python**  
**Short Name / Project Code:** `RescuE-Triage`  
**Course:** Python Programming Laboratory (Project Review 2)  
**Team Size:** 3 Members  

---

## 📌 Abstract
During severe natural disasters such as floods, earthquakes, and urban fires, emergency response centers experience sudden spikes in concurrent distress calls. Conventional manual dispatching often leads to operational bottlenecks, subjective triage decisions, and critical delays in deploying aid to high-risk victims.

This project presents **RescuE-Triage**, an automated decision-support system developed in Python that calculates real-time priority queues for emergency dispatchers. Using a proprietary multi-factor algorithm—the **Dynamic Emergency Priority Index (DEPI)**—the system evaluates incoming distress requests based on four key variables:
1. **Medical Urgency** ($M \in [1, 10]$)
2. **Immediate Environmental Hazard Level** ($H \in [1, 10]$)
3. **Presence of Vulnerable Individuals** ($V \in [1.0, 5.0]$: infants, children, pregnant, elderly, disabled)
4. **Cumulative Wait Time** ($W(\Delta t)$)

By incorporating dynamic wait-time scaling, the system prevents low-risk cases from suffering indefinite delays (queue starvation) while still routing immediate life-threatening cases to the top of the queue. Implemented using lightweight Python data structures (dictionaries, dynamic arrays, and custom binary heaps), the project provides a scalable, computationally efficient solution accessible on low-cost hardware.

---

## 🚀 Quick Start / How to Run the Executable App

### Option 1: Double-Click the Windows Launcher (Easiest)
Simply double-click:
```
run_app.bat
```
This opens an interactive menu allowing you to launch:
- **[1] Desktop GUI Application** (Tkinter Modern Dark Mode)
- **[2] Web Command Center Dashboard** (`http://127.0.0.1:8080`)
- **[3] Algorithmic Performance Benchmark** ($\mathcal{O}(\log N)$ proof)
- **[4] Automated Unit Test Suite**

### Option 2: Run the Standalone Windows Executable
A compiled, zero-installation executable is located at:
```
dist/RescuE-Triage.exe
```
Double-click `RescuE-Triage.exe` to run on any 64-bit Windows machine without needing Python installed!

### Option 3: Command Line (Developer Mode)
```bash
# Launch Desktop GUI (Default)
python main.py

# Launch Web Command Center Dashboard in Browser
python main.py --web

# Run Empirical Benchmark (Max-Heap vs Naive Array)
python main.py --benchmark

# Run Automated Test Suite
python main.py --test
```

---

## 🧮 Mathematical Engine: The DEPI Algorithm

The **Dynamic Emergency Priority Index (DEPI)** is computed via:

$$DEPI(t) = (w_m \cdot M) + (w_h \cdot H) + (w_v \cdot V) + W(\Delta t)$$

Where:
- $w_m = 4.5$: Weight for Medical Urgency ($M \in [1, 10]$). Max: $45.0$ pts.
- $w_h = 3.0$: Weight for Environmental Hazard ($H \in [1, 10]$). Max: $30.0$ pts.
- $w_v = 3.0$: Weight for Vulnerability Factor ($V \in [1.0, 5.0]$). Max: $15.0$ pts.
- $W(\Delta t) = \min(20.0, 0.35 \cdot (\Delta t)^{1.15})$: Dynamic wait-time aging function that escalates waiting tickets over time to prevent starvation.

### Triage Classification Tiers
| Tier | Score Range | Clinical Meaning | Target Response Action |
| :--- | :--- | :--- | :--- |
| **CODE RED** | $75.0 - 100.0$ | Immediate Life Threat / Cardiac / Entrapment | Immediate ALS Ambulance / Medevac dispatch |
| **CODE ORANGE** | $55.0 - 74.9$ | Severe Trauma / Structural Hazard | Rapid deployment (Fire, Boat, BLS) |
| **CODE YELLOW** | $35.0 - 54.9$ | Moderate Injury / Stable Vitals | Monitored queue with dynamic aging |
| **CODE GREEN** | $< 35.0$ | Minor Injury / Safe High Ground | Low-priority delayed care |

---

## ⚡ Computational Complexity & Performance

| Operation | Custom Max-Heap | Naive Unsorted List | Full Array Sort (TimSort) |
| :--- | :--- | :--- | :--- |
| **Enqueue Distress Call** | $\mathcal{O}(\log N)$ | $\mathcal{O}(1)$ | $\mathcal{O}(1)$ |
| **Extract Top Dispatch** | $\mathcal{O}(\log N)$ | $\mathcal{O}(N)$ | $\mathcal{O}(N \log N)$ |
| **ID Lookup** | $\mathcal{O}(1)$ (via index map) | $\mathcal{O}(N)$ | $\mathcal{O}(N)$ |
| **Dynamic Wait Aging** | $\mathcal{O}(N)$ (Bottom-up Heapify) | $\mathcal{O}(N)$ | $\mathcal{O}(N \log N)$ |

### Benchmark Results (Measured on Windows 11, Python 3.14):
- **$N = 500$ Calls:** Max-Heap extraction is **3.9x faster** than naive linear scan.
- **$N = 2,000$ Calls:** Max-Heap extraction is **18.3x faster**.
- **$N = 5,000$ Calls:** Max-Heap extraction is **29.8x faster**!

---

## 📂 Repository Directory Layout

```
RescuE-Triage/
├── run_app.bat                      # One-click Windows Launcher
├── main.py                          # Unified Application Entry Point
├── config.py                        # DEPI Weights, Tiers & Fleet Definitions
│
├── core/                            # [Team Member 1: Core Algorithm & Data Structures]
│   ├── data_models.py               # DistressCall, VulnerabilityProfile, DEPIBreakdown
│   ├── depi_engine.py               # DEPI Mathematical Formulation & Wait Aging
│   ├── priority_queue.py            # Custom Max-Heap Priority Queue & Inverted Map
│   └── benchmark.py                 # Algorithmic Stress-Test & Complexity Proof
│
├── simulation/                      # [Team Member 2: Scenarios & Dispatch Units]
│   ├── scenario_generator.py        # Urban Flood, 6.8M Earthquake, Tower Fire Presets
│   ├── dispatch_router.py           # Unit Fleet Matching (Ambulance, Boat, Helicopter)
│   └── live_call_stream.py          # Real-time Inbound Distress Call Generator
│
├── ui/                              # [Team Member 3: Interactive Visual Interfaces]
│   ├── gui_app.py                   # Desktop Tkinter Dark Mode Application
│   ├── web_server.py                # Zero-dependency Python HTTP/REST Server
│   └── web/                         # Rich Web Command Center Dashboard
│       ├── index.html               # Semantic HTML5 Interface with Modals
│       ├── styles.css               # Glassmorphism, Neon Tiers & Grid Layout
│       └── app.js                   # Live Polling, Radar Canvas & Web Audio Siren
│
├── storage/                         # Persistence & Auditing
│   └── persistence.py               # CSV & JSON Audit Trail Exporter
│
├── tests/                           # Quality Assurance Suite
│   └── test_depi_algorithm.py       # Automated Unit Tests
│
├── docs/                            # Academic Defense Documents
│   ├── REVIEW_2_PRESENTATION_GUIDE.md # 3-Person Presentation Script & Viva Q&A
│   └── ALGORITHM_SPECIFICATION.md   # Mathematical Formulations & Proofs
│
└── dist/
    └── RescuE-Triage.exe            # Standalone Windows Executable
```

---

## 👥 Team Roles for Review 2 Evaluation
- **Student 1 (Algorithmic Modeling):** Explains DEPI mathematical formulation, multi-factor weights, and starvation prevention mechanism.
- **Student 2 (Data Structures & Benchmarks):** Explains custom binary max-heap, bottom-up heapify $\mathcal{O}(N)$, and live speedup benchmarks.
- **Student 3 (Application & Dispatcher Operations):** Demonstrates Desktop GUI, Web Command Center radar, disaster scenario presets, and CSV audit exports.
