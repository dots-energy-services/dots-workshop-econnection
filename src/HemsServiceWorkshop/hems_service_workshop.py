from datetime import datetime
import helics as h
from dots_infrastructure.DataClasses import TimeStepInformation, EsdlId, HelicsCalculationInformation, get_single_param_with_name
from dots_infrastructure.HelicsFederateHelpers import HelicsSimulationExecutor
from esdl import EnergySystem

class HemsServiceWorkshop(HemsServiceWorkshopBase): 

    def init_calculation_service(self, energy_system: EnergySystem):
        super().init_calculation_service(energy_system)

    def optimize_consumption(self, param_dict : dict, simulation_time : datetime, time_step_number : TimeStepInformation, esdl_id : EsdlId, energy_system : EnergySystem):
        current_reactive_power  = get_single_param_with_name(param_dict, "current_reactive_power")
        current_active_power  = get_single_param_with_name(param_dict, "current_active_power")
        aggregated_active_power = current_active_power*2
        aggregated_rective_power = current_reactive_power*2
        return {    
            "active_power_to_charge" : aggregated_active_power,
            "reactive_power_to_charge" : aggregated_rective_power
        }

if __name__ == "__main__":

    helics_simulation_executor = HemsServiceWorkshop()
    helics_simulation_executor.start_simulation()
    helics_simulation_executor.stop_simulation()