"""Token accounting and budget guardrails.

Every pipeline run tracks estimated tokens against a monthly budget
configured in units (roughly 1 unit = 1K blended tokens at list price).
The guard trips before spend, not after.
"""
from __future__ import annotations

from dataclasses import dataclass


def estimate_tokens(text: str) -> int:
    """Rough tokenizer: ~4 chars per token for English prose."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


@dataclass
class UsageRecord:
    input_tokens: int
    output_tokens: int

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


class BudgetExceeded(Exception):
    pass


class CostGuard:
    def __init__(self, monthly_budget_units: float, warn_fraction: float = 0.8,
                 input_price: float = 0.0015, output_price: float = 0.002):
        if monthly_budget_units <= 0:
            raise ValueError("budget must be positive")
        if not 0 < warn_fraction <= 1:
            raise ValueError("warn_fraction must be in (0, 1]")
        self.budget = monthly_budget_units
        self.warn_fraction = warn_fraction
        self.input_price = input_price
        self.output_price = output_price
        self._spent_units = 0.0
        self._records: list[UsageRecord] = []

    def _units(self, record: UsageRecord) -> float:
        return (record.input_tokens * self.input_price + record.output_tokens * self.output_price) / 1000.0

    def track(self, record: UsageRecord) -> dict:
        units = self._units(record)
        projected = self._spent_units + units
        if projected > self.budget:
            raise BudgetExceeded(
                f"budget exceeded: {projected:.3f} units > {self.budget:.3f} monthly budget")
        self._spent_units = projected
        self._records.append(record)
        return {
            "units": round(units, 6),
            "spent": round(self._spent_units, 6),
            "fraction": round(self._spent_units / self.budget, 4),
            "warning": self._spent_units >= self.warn_fraction * self.budget,
        }

    @property
    def spent_units(self) -> float:
        return self._spent_units

    @property
    def remaining_units(self) -> float:
        return max(0.0, self.budget - self._spent_units)

    def summary(self) -> dict:
        return {
            "budget_units": self.budget,
            "spent_units": round(self._spent_units, 6),
            "remaining_units": round(self.remaining_units, 6),
            "requests": len(self._records),
            "total_tokens": sum(r.total for r in self._records),
        }
