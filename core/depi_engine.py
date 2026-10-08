"""
Dynamic Emergency Priority Index (DEPI) Algorithmic Engine.
Implements the multi-factor prioritization formula, dynamic wait-time scaling,
and triage category classification.
"""

import math
from typing import Optional
from config import DEPI_WEIGHTS, WAIT_TIME_CONFIG, TriageCategory
from core.data_models import DistressCall, DEPIBreakdown


class DEPIEngine:
    """
    Computes real-time dynamic risk-weighted triage scores based on:
    1. Medical Urgency (M): [1, 10]
    2. Environmental Hazard Level (H): [1, 10]
    3. Vulnerability Factor (V): [1.0, 5.0]
    4. Dynamic Cumulative Wait Time (W): Scaled non-linearly over minutes
    """

    def __init__(self, weights: dict = None, wait_config: dict = None):
        self.weights = weights or DEPI_WEIGHTS
        self.wait_config = wait_config or WAIT_TIME_CONFIG

    def calculate_wait_time_bonus(self, wait_minutes: float) -> float:
        """
        Calculates dynamic wait-time scaling factor f(Δt).
        Incorporates sub-linear/polynomial aging to prevent queue starvation:
        f(Δt) = min(W_max, λ * (Δt)^γ)
        """
        if wait_minutes <= 0.0:
            return 0.0

        rate = self.wait_config["aging_rate_per_min"]
        exp = self.wait_config["acceleration_exponent"]
        max_bonus = self.wait_config["max_wait_bonus"]

        # Scaled aging formula
        bonus = rate * math.pow(wait_minutes, exp)
        return min(max_bonus, bonus)

    def evaluate_call(self, call: DistressCall, current_time: Optional[float] = None) -> DEPIBreakdown:
        """
        Calculates full DEPI score and transparent breakdown for an emergency call.
        """
        # 1. Medical Component
        m_val = max(1, min(10, call.medical_urgency))
        med_score = self.weights["medical"] * m_val

        # 2. Environmental Hazard Component
        h_val = max(1, min(10, call.environmental_hazard))
        env_score = self.weights["environmental"] * h_val

        # 3. Vulnerability Component
        v_factor = call.vulnerability.compute_factor()
        vuln_score = self.weights["vulnerability"] * v_factor

        # 4. Dynamic Wait-Time Scaling
        wait_min = call.get_wait_time_minutes(current_time)
        wait_score = self.calculate_wait_time_bonus(wait_min)

        # Total Aggregated DEPI
        total_depi = med_score + env_score + vuln_score + wait_score

        # Categorization based on thresholds
        if total_depi >= 75.0:
            category = TriageCategory.CODE_RED
        elif total_depi >= 55.0:
            category = TriageCategory.CODE_ORANGE
        elif total_depi >= 35.0:
            category = TriageCategory.CODE_YELLOW
        else:
            category = TriageCategory.CODE_GREEN

        formula_repr = (
            f"DEPI = ({self.weights['medical']}×{m_val}) + "
            f"({self.weights['environmental']}×{h_val}) + "
            f"({self.weights['vulnerability']}×{v_factor}) + "
            f"f({wait_min:.1f}m) = {total_depi:.2f}"
        )

        breakdown = DEPIBreakdown(
            medical_component=med_score,
            environmental_component=env_score,
            vulnerability_component=vuln_score,
            wait_time_minutes=wait_min,
            wait_time_component=wait_score,
            total_score=total_depi,
            category=category,
            formula_expression=formula_repr,
        )

        # Update call object state
        call.current_depi = total_depi
        call.depi_breakdown = breakdown

        return breakdown
