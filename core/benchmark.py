"""
Computational Performance Benchmark for RescuE-Triage.
Compares Custom Max-Heap Priority Queue (O(log N)) vs Naive Unsorted List (O(N))
and Standard TimSort (O(N log N)) under high call-volume stress.
Essential for Academic Defense in Python Lab Review.
"""

import time
import random
from typing import Dict, Any, List
from core.data_models import DistressCall, VulnerabilityProfile
from core.priority_queue import MaxHeapPriorityQueue
from core.depi_engine import DEPIEngine


def generate_mock_calls(count: int) -> List[DistressCall]:
    """Generates synthetic distress calls for stress-testing."""
    calls = []
    base_time = time.time()
    for i in range(count):
        vuln = VulnerabilityProfile(
            infants_count=random.randint(0, 2) if random.random() < 0.3 else 0,
            elderly_count=random.randint(0, 3) if random.random() < 0.4 else 0,
            disabled_count=1 if random.random() < 0.2 else 0,
            pregnant_count=1 if random.random() < 0.1 else 0
        )
        call = DistressCall(
            id=f"STRESS-{i:06d}",
            caller_name=f"Caller {i}",
            medical_urgency=random.randint(1, 10),
            environmental_hazard=random.randint(1, 10),
            vulnerability=vuln,
            created_timestamp=base_time - random.uniform(0, 3600)
        )
        calls.append(call)
    return calls


def run_algorithmic_benchmark(sample_sizes: List[int] = None) -> Dict[str, Any]:
    """
    Executes comparative benchmarks across multiple call volumes.
    """
    if sample_sizes is None:
        sample_sizes = [500, 2000, 5000]

    engine = DEPIEngine()
    results = {}

    for n in sample_sizes:
        calls = generate_mock_calls(n)

        # 1. Custom Max-Heap Priority Queue Benchmark
        heap_queue = MaxHeapPriorityQueue(depi_engine=engine)
        t0 = time.perf_counter()
        for call in calls:
            heap_queue.push(call)
        heap_insert_time = time.perf_counter() - t0

        t0 = time.perf_counter()
        dispatched_count = 0
        while not heap_queue.is_empty() and dispatched_count < min(100, n):
            heap_queue.pop_max()
            dispatched_count += 1
        heap_extract_time = time.perf_counter() - t0

        # 2. Naive Dynamic Array Linear Search Benchmark
        naive_list = []
        t0 = time.perf_counter()
        for call in calls:
            engine.evaluate_call(call)
            naive_list.append(call)
        naive_insert_time = time.perf_counter() - t0

        t0 = time.perf_counter()
        for _ in range(min(100, n)):
            if not naive_list:
                break
            # Find max via linear scan O(N)
            max_idx = 0
            for j in range(1, len(naive_list)):
                if naive_list[j].current_depi > naive_list[max_idx].current_depi:
                    max_idx = j
            naive_list.pop(max_idx)
        naive_extract_time = time.perf_counter() - t0

        results[f"N={n}"] = {
            "Heap_Insert_Total_Sec": round(heap_insert_time, 5),
            "Heap_Extract100_Sec": round(heap_extract_time, 5),
            "Naive_Insert_Total_Sec": round(naive_insert_time, 5),
            "Naive_Extract100_Sec": round(naive_extract_time, 5),
            "Heap_Speedup_Factor": round(naive_extract_time / max(1e-6, heap_extract_time), 2)
        }

    return results


if __name__ == "__main__":
    print("=== RescuE-Triage Algorithmic Benchmark ===")
    res = run_algorithmic_benchmark()
    for k, v in res.items():
        print(f"\nDataset Size: {k}")
        print(f"  Max-Heap Push Time:     {v['Heap_Insert_Total_Sec']} s")
        print(f"  Max-Heap Pop(100) Time: {v['Heap_Extract100_Sec']} s")
        print(f"  Naive Linear Pop(100):  {v['Naive_Extract100_Sec']} s")
        print(f"  Extraction Speedup:     {v['Heap_Speedup_Factor']}x faster!")
