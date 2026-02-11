from dataclasses import dataclass
from typing import List

@dataclass
class OptimizeConsumptionOutput:
    aggregated_active_power : float | None = None
    aggregated_reactive_power : float | None = None

