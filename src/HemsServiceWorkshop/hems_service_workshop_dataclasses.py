from dataclasses import dataclass
from typing import List

@dataclass
class OptimizeConsumptionOutput:
    aggregated_active_power : List | None = None
    aggregated_reactive_power : List | None = None
    active_power_to_charge : float | None = None

