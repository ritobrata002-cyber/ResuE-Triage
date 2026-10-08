"""
RescuE-Triage: Dynamic Risk-Weighted Triage Router
Main Application Unified Entry Point.

Usage:
  python main.py             # Launches Desktop GUI (Tkinter Dark Theme)
  python main.py --web       # Launches Web Command Center on http://127.0.0.1:8080
  python main.py --benchmark # Runs Computational Performance Benchmark (O(log N) vs O(N))
  python main.py --test      # Runs Unit Test Suite
"""

import sys
import os
import argparse
import webbrowser
import threading
import time

# Ensure root directory is on python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def run_tests():
    import unittest
    print("=" * 65)
    print("  Running RescuE-Triage Automated Test Suite...")
    print("=" * 65)
    loader = unittest.TestLoader()
    suite = loader.discover("tests")
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


def run_benchmark():
    from core.benchmark import run_algorithmic_benchmark
    print("=" * 65)
    print("  RescuE-Triage Computational Performance Benchmark")
    print("  Evaluating Max-Heap (O(log N)) vs Naive Dynamic Array (O(N))")
    print("=" * 65)
    results = run_algorithmic_benchmark([500, 2000, 5000])
    for size_key, val in results.items():
        print(f"\nDataset: {size_key}")
        print(f"  Heap Push Time (N calls):       {val['Heap_Insert_Total_Sec']:.5f} s")
        print(f"  Heap Pop-100 Time:              {val['Heap_Extract100_Sec']:.5f} s")
        print(f"  Naive Linear Scan Pop-100:      {val['Naive_Extract100_Sec']:.5f} s")
        print(f"  Speedup Factor:                 {val['Heap_Speedup_Factor']:.1f}x faster!")
    print("\n" + "=" * 65)


def run_web(port: int = 8080):
    from ui.web_server import start_web_server

    def open_browser():
        time.sleep(1.2)
        webbrowser.open(f"http://127.0.0.1:{port}")

    threading.Thread(target=open_browser, daemon=True).start()
    start_web_server(port)


def run_gui():
    from ui.gui_app import launch_gui
    launch_gui()


def main():
    parser = argparse.ArgumentParser(description="RescuE-Triage Emergency Dispatch Decision-Support System")
    parser.add_argument("--gui", action="store_true", help="Launch Tkinter Desktop GUI (Default)")
    parser.add_argument("--web", action="store_true", help="Launch Web Command Center Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Web server port (default 8080)")
    parser.add_argument("--benchmark", action="store_true", help="Run algorithmic performance benchmark")
    parser.add_argument("--test", action="store_true", help="Run automated test suite")

    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.benchmark:
        run_benchmark()
    elif args.web:
        run_web(args.port)
    else:
        # Default to Desktop GUI
        run_gui()


if __name__ == "__main__":
    main()
