from datetime import datetime
import helics as h
from dots_infrastructure.DataClasses import TimeStepInformation, EsdlId, HelicsCalculationInformation
from dots_infrastructure.HelicsFederateHelpers import HelicsSimulationExecutor
from esdl import EnergySystem

class HemsServiceWorkshop(HemsServiceWorkshopBase): 

    def init_calculation_service(self, energy_system: EnergySystem):
        super().init_calculation_service(energy_system)

    def optimize_consumption(self, param_dict : dict, simulation_time : datetime, time_step_number : TimeStepInformation, esdl_id : EsdlId, energy_system : EnergySystem):
        pass

if __name__ == "__main__":

    helics_simulation_executor = HemsServiceWorkshop()
    helics_simulation_executor.start_simulation()
    helics_simulation_executor.stop_simulation()