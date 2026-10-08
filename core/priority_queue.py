"""
Custom Max-Heap Priority Queue & Queue Management for RescuE-Triage.
Implemented in pure Python to demonstrate data structure design for Python Lab.
Features:
- O(log N) insert and extract-max operations
- O(1) ID lookup using an inverted dictionary index
- Dynamic reheapification for real-time wait-time escalation
"""

from typing import List, Optional, Dict
from core.data_models import DistressCall
from core.depi_engine import DEPIEngine


class MaxHeapPriorityQueue:
    """
    Max-Heap data structure optimized for emergency dispatch triage.
    Higher DEPI scores bubble to index 0 (Root).
    Maintains an internal dictionary mapping call_id -> heap_index for O(1) tracking.
    """

    def __init__(self, depi_engine: Optional[DEPIEngine] = None):
        self.heap: List[DistressCall] = []
        self.index_map: Dict[str, int] = {}  # call_id -> index in self.heap
        self.engine = depi_engine or DEPIEngine()

    def __len__(self) -> int:
        return len(self.heap)

    def is_empty(self) -> bool:
        return len(self.heap) == 0

    def _swap(self, i: int, j: int) -> None:
        """Swaps elements at indices i and j, updating the internal index map."""
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.index_map[self.heap[i].id] = i
        self.index_map[self.heap[j].id] = j

    def _sift_up(self, index: int) -> None:
        """Restores heap invariant upward from the given index (O(log N))."""
        parent = (index - 1) // 2
        while index > 0 and self.heap[index].current_depi > self.heap[parent].current_depi:
            self._swap(index, parent)
            index = parent
            parent = (index - 1) // 2

    def _sift_down(self, index: int) -> None:
        """Restores heap invariant downward from the given index (O(log N))."""
        size = len(self.heap)
        while True:
            largest = index
            left = 2 * index + 1
            right = 2 * index + 2

            if left < size and self.heap[left].current_depi > self.heap[largest].current_depi:
                largest = left
            if right < size and self.heap[right].current_depi > self.heap[largest].current_depi:
                largest = right

            if largest != index:
                self._swap(index, largest)
                index = largest
            else:
                break

    def push(self, call: DistressCall, current_time: Optional[float] = None) -> None:
        """
        Inserts a new distress call into the priority queue in O(log N) time.
        Evaluates DEPI score before placement.
        """
        # Ensure fresh DEPI score
        self.engine.evaluate_call(call, current_time=current_time)
        
        index = len(self.heap)
        self.heap.append(call)
        self.index_map[call.id] = index
        self._sift_up(index)

    def pop_max(self) -> Optional[DistressCall]:
        """
        Extracts the highest-priority distress call (O(log N)).
        Returns None if queue is empty.
        """
        if not self.heap:
            return None

        if len(self.heap) == 1:
            call = self.heap.pop()
            del self.index_map[call.id]
            return call

        # Root holds the highest priority
        max_call = self.heap[0]
        # Move last element to root and sift down
        self.heap[0] = self.heap.pop()
        self.index_map[self.heap[0].id] = 0
        del self.index_map[max_call.id]
        
        self._sift_down(0)
        return max_call

    def peek_max(self) -> Optional[DistressCall]:
        """Returns the highest-priority call without removing it (O(1))."""
        return self.heap[0] if self.heap else None

    def remove(self, call_id: str) -> Optional[DistressCall]:
        """
        Removes a call by ID in O(log N) time using index map.
        Useful when a call is cancelled or dispatched directly.
        """
        if call_id not in self.index_map:
            return None

        index = self.index_map[call_id]
        removed_call = self.heap[index]

        if index == len(self.heap) - 1:
            self.heap.pop()
            del self.index_map[call_id]
            return removed_call

        # Swap with last element and adjust heap
        last_call = self.heap.pop()
        del self.index_map[call_id]

        self.heap[index] = last_call
        self.index_map[last_call.id] = index

        # Restore heap property
        parent = (index - 1) // 2
        if index > 0 and self.heap[index].current_depi > self.heap[parent].current_depi:
            self._sift_up(index)
        else:
            self._sift_down(index)

        return removed_call

    def get_by_id(self, call_id: str) -> Optional[DistressCall]:
        """Returns call object by ID in O(1) time."""
        if call_id in self.index_map:
            return self.heap[self.index_map[call_id]]
        return None

    def refresh_priorities(self, current_time: Optional[float] = None) -> None:
        """
        Re-evaluates DEPI for all queued calls with updated wait times,
        then reconstructs heap invariant in O(N) using Bottom-Up Heapify.
        """
        for call in self.heap:
            self.engine.evaluate_call(call, current_time=current_time)

        # Bottom-up heapify in O(N)
        for i in range((len(self.heap) // 2) - 1, -1, -1):
            self._sift_down(i)

        # Sync index map
        for idx, call in enumerate(self.heap):
            self.index_map[call.id] = idx

    def get_sorted_queue(self) -> List[DistressCall]:
        """
        Returns a snapshot of queued calls sorted by priority descending.
        Does not mutate the internal heap.
        """
        return sorted(self.heap, key=lambda c: c.current_depi, reverse=True)


class DynamicTriageRouter:
    """
    High-level triage manager coordinating priority queues, active dispatches,
    and history records.
    """

    def __init__(self):
        self.engine = DEPIEngine()
        self.priority_queue = MaxHeapPriorityQueue(depi_engine=self.engine)
        self.active_dispatches: Dict[str, DistressCall] = {}
        self.resolved_calls: List[DistressCall] = []

    def submit_call(self, call: DistressCall, current_time: Optional[float] = None) -> DistressCall:
        call.status = "QUEUED"
        self.priority_queue.push(call, current_time=current_time)
        return call

    def dispatch_top(self, unit_id: str, current_time: Optional[float] = None) -> Optional[DistressCall]:
        call = self.priority_queue.pop_max()
        if call:
            call.status = "DISPATCHED"
            call.assigned_unit = unit_id
            call.dispatched_at = current_time or DistressCall().created_timestamp
            self.active_dispatches[call.id] = call
        return call

    def dispatch_call_by_id(self, call_id: str, unit_id: str, current_time: Optional[float] = None) -> Optional[DistressCall]:
        call = self.priority_queue.remove(call_id)
        if call:
            call.status = "DISPATCHED"
            call.assigned_unit = unit_id
            call.dispatched_at = current_time or DistressCall().created_timestamp
            self.active_dispatches[call.id] = call
        return call

    def resolve_call(self, call_id: str, current_time: Optional[float] = None) -> Optional[DistressCall]:
        call = self.active_dispatches.pop(call_id, None)
        if not call:
            call = self.priority_queue.remove(call_id)
        if call:
            call.status = "RESOLVED"
            call.resolved_at = current_time or DistressCall().created_timestamp
            self.resolved_calls.append(call)
        return call

    def tick(self, current_time: Optional[float] = None) -> None:
        """Aging cycle: updates cumulative wait times and re-balances priority queue."""
        self.priority_queue.refresh_priorities(current_time=current_time)
