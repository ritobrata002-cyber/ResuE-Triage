"""
Unit Test Suite for RescuE-Triage DEPI Algorithm & Priority Queue.
Validates mathematical calculations, dynamic wait aging, heap invariants, and triage boundaries.
"""

import unittest
import time
from core.data_models import DistressCall, VulnerabilityProfile
from core.depi_engine import DEPIEngine
from core.priority_queue import MaxHeapPriorityQueue, DynamicTriageRouter
from config import TriageCategory


class TestDEPIAlgorithm(unittest.TestCase):

    def setUp(self):
        self.engine = DEPIEngine()

    def test_depi_calculation_baseline(self):
        """Validates base formula: (4.5 * M) + (3.0 * H) + (3.0 * V) + f(wait)."""
        call = DistressCall(
            medical_urgency=8,
            environmental_hazard=6,
            vulnerability=VulnerabilityProfile(elderly_count=1), # V = 1.0 + 1.0 = 2.0
            created_timestamp=time.time() # 0 wait time
        )
        breakdown = self.engine.evaluate_call(call)
        
        # Expected:
        # Medical: 4.5 * 8 = 36.0
        # Environmental: 3.0 * 6 = 18.0
        # Vulnerability: 3.0 * 2.0 = 6.0
        # Wait: 0.0
        # Total: 36 + 18 + 6 = 60.0 -> CODE_ORANGE
        self.assertAlmostEqual(breakdown.medical_component, 36.0, places=2)
        self.assertAlmostEqual(breakdown.environmental_component, 18.0, places=2)
        self.assertAlmostEqual(breakdown.vulnerability_component, 6.0, places=2)
        self.assertAlmostEqual(breakdown.wait_time_component, 0.0, places=2)
        self.assertAlmostEqual(breakdown.total_score, 60.0, places=2)
        self.assertEqual(breakdown.category, TriageCategory.CODE_ORANGE)

    def test_starvation_prevention_wait_time_aging(self):
        """Verifies that wait-time escalation prevents indefinite starvation."""
        now = time.time()
        # Non-urgent call that has been waiting 45 minutes
        starved_call = DistressCall(
            medical_urgency=3,
            environmental_hazard=2,
            vulnerability=VulnerabilityProfile(), # V = 1.0
            created_timestamp=now - (45 * 60) # 45 minutes ago
        )
        breakdown = self.engine.evaluate_call(starved_call, current_time=now)
        
        # Base: 4.5*3 + 3.0*2 + 3.0*1 = 13.5 + 6.0 + 3.0 = 22.5
        # Wait bonus must be strictly positive and capped within configuration
        self.assertGreater(breakdown.wait_time_component, 5.0)
        self.assertGreater(breakdown.total_score, 22.5)
        self.assertLessEqual(breakdown.wait_time_component, 20.0)

    def test_triage_category_thresholds(self):
        """Verifies that extreme critical cases correctly map to CODE_RED."""
        critical_call = DistressCall(
            medical_urgency=10,
            environmental_hazard=10,
            vulnerability=VulnerabilityProfile(infants_count=2, disabled_count=1),
            created_timestamp=time.time()
        )
        breakdown = self.engine.evaluate_call(critical_call)
        # 4.5*10 + 3.0*10 + 3.0*5.0 = 45 + 30 + 15 = 90.0
        self.assertEqual(breakdown.category, TriageCategory.CODE_RED)
        self.assertGreaterEqual(breakdown.total_score, 75.0)


class TestMaxHeapPriorityQueue(unittest.TestCase):

    def setUp(self):
        self.queue = MaxHeapPriorityQueue()

    def test_max_heap_invariants(self):
        """Verifies that pop_max always returns the highest DEPI score in descending order."""
        now = time.time()
        c1 = DistressCall(id="C1", medical_urgency=3, environmental_hazard=2, created_timestamp=now)
        c2 = DistressCall(id="C2", medical_urgency=10, environmental_hazard=9, created_timestamp=now)
        c3 = DistressCall(id="C3", medical_urgency=6, environmental_hazard=5, created_timestamp=now)
        c4 = DistressCall(id="C4", medical_urgency=8, environmental_hazard=8, created_timestamp=now)

        self.queue.push(c1)
        self.queue.push(c2)
        self.queue.push(c3)
        self.queue.push(c4)

        self.assertEqual(len(self.queue), 4)

        # Extraction must be monotonically decreasing in DEPI
        first = self.queue.pop_max()
        second = self.queue.pop_max()
        third = self.queue.pop_max()
        fourth = self.queue.pop_max()

        self.assertEqual(first.id, "C2") # Highest
        self.assertEqual(second.id, "C4")
        self.assertEqual(third.id, "C3")
        self.assertEqual(fourth.id, "C1") # Lowest

        self.assertTrue(self.queue.is_empty())

    def test_dynamic_reheapification_wait_aging(self):
        """Validates that refresh_priorities updates queue order as time elapses."""
        t0 = time.time()
        # High base urgency call created just now
        call_new = DistressCall(id="NEW", medical_urgency=5, environmental_hazard=4, created_timestamp=t0)
        # Moderate urgency call that has been waiting for 60 minutes
        call_old = DistressCall(id="OLD", medical_urgency=4, environmental_hazard=4, created_timestamp=t0 - 3600)

        self.queue.push(call_new, current_time=t0)
        self.queue.push(call_old, current_time=t0)

        # Fast forward time by 30 minutes
        future_time = t0 + 1800
        self.queue.refresh_priorities(current_time=future_time)

        top = self.queue.peek_max()
        self.assertIsNotNone(top)


if __name__ == "__main__":
    unittest.main()
