from dataclasses import dataclass
from typing import List

@dataclass
class TestThisCalculationOutput:
    aggregated_active_power : List | None = None
    aggregated_reactive_power : List | None = None
    aggregated_solar_irradiance : List | None = None

