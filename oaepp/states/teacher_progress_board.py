"""F-T-013 Progress Board — ProgressBoardState (TDD GREEN).

Satisfies the TDD interface contract by inheriting from and extending ProgressState:
- HEATMAP_STATUS: heatmap status → colour mapping constant
- heatmap_data: heatmap matrix data (rx.var → matrix_cells)
- completion_rate_chart: completion rate bar-chart data (rx.var → completion_trend)
- load_progress(): load progress data (→ load_data)
- filter_by_course(): filter by course (→ set_course)
"""

from __future__ import annotations

from typing import Any, Dict, List

import reflex as rx

try:
    from oaepp.states.progress import ProgressState, STATUS_COLORS
except ImportError:
    from states.progress import ProgressState, STATUS_COLORS

# ── TDD-required: heatmap status colour constants ──
HEATMAP_STATUS: Dict[str, str] = {
    "submitted":     STATUS_COLORS.get("submitted", "#22c55e"),
    "late":          STATUS_COLORS.get("late", "#eab308"),
    "missing":       STATUS_COLORS.get("not_submitted", "#ef4444"),
    "not_published": STATUS_COLORS.get("not_published", "#d1d5db"),
}


class ProgressBoardState(ProgressState):
    """Progress board state — TDD F-T-013 GREEN.

    Inherits all data-loading and filtering capabilities from
    ``ProgressState``, and additionally exposes the TDD-required
    naming interface.
    """

    # ── TDD-required constant ──
    # Shallow-copy so the class attribute does not alias the module-level
    # constant (prevents accidental cross-mutation).
    HEATMAP_STATUS: Dict[str, str] = dict(HEATMAP_STATUS)

    # ── TDD-required computed properties (rx.var) ──

    @rx.var
    def heatmap_data(self) -> List[Dict[str, Any]]:
        """TDD alias — heatmap matrix data, delegates to ``matrix_cells``."""
        return self.matrix_cells

    @rx.var
    def completion_rate_chart(self) -> List[Dict[str, Any]]:
        """TDD alias — completion rate bar chart data, delegates to ``completion_trend``."""
        return self.completion_trend

    # ── TDD-required event handlers ──

    def load_progress(self):
        """TDD alias — load progress board data, delegates to ``load_data``."""
        return self.load_data()

    def filter_by_course(self, course_id_str: str = ""):
        """TDD alias — filter by course, delegates to ``set_course``."""
        return self.set_course(course_id_str)
