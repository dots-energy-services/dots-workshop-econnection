from datetime import datetime
import helics as h
from dots_infrastructure.DataClasses import TimeStepInformation, EsdlId
from dots_infrastructure.CalculationServiceHelperFunctions import get_single_param_with_name

from esdl import EnergySystem

from HemsServiceWorkshop.hems_service_workshop_base import HemsServiceWorkshopBase
from HemsServiceWorkshop.hems_service_workshop_dataclasses import OptimizeConsumptionOutput

class HemsServiceWorkshop(HemsServiceWorkshopBase): 

    def init_calculation_service(self, energy_system: EnergySystem):
        super().init_calculation_service(energy_system)

    def optimize_consumption(self, param_dict : dict, simulation_time : datetime, time_step_number : TimeStepInformation, esdl_id : EsdlId, energy_system : EnergySystem):
        current_reactive_power  = get_single_param_with_name(param_dict, "current_reactive_power")
        current_active_power  = get_single_param_with_name(param_dict, "current_active_power")
        pv_active_power  = get_single_param_with_name(param_dict, "pv_active_power")
        if pv_active_power == None:
            pv_active_power = 0
        max_charge_active_power  = get_single_param_with_name(param_dict, "max_charge_active_power")
        max_discharge_active_power  = get_single_param_with_name(param_dict, "max_discharge_active_power")
        market_price = get_single_param_with_name(param_dict, "market_price")
        if market_price == None:
            market_price = 0

        active_power_to_charge = 0
        aggregated_active_power_1phase = current_active_power / 3
        aggregated_reactive_power_1phase = current_reactive_power / 3
        aggregated_active_power = [aggregated_active_power_1phase, aggregated_active_power_1phase, aggregated_active_power_1phase]
        aggregated_reactive_power = [aggregated_reactive_power_1phase, aggregated_reactive_power_1phase, aggregated_reactive_power_1phase]
        active_power_to_charge = 0
        
        # If market price is above 0.1, maximize discharge and sell to grid
        if market_price > 0.1:
            active_power_to_charge = max_discharge_active_power
            # Discharge battery and feed everything (PV + battery) back to grid
            # Negative value means feeding back to grid
            total_power_to_sell = pv_active_power - max_discharge_active_power - current_active_power
            power_per_phase = total_power_to_sell / 3
            aggregated_active_power = [power_per_phase, power_per_phase, power_per_phase]
        # If there is a deficit in power, discharge the battery to cover it
        elif 0 > pv_active_power - current_active_power > max_discharge_active_power:
            active_power_to_charge = pv_active_power - current_active_power
            aggregated_active_power = [0,0,0]
        # If there is surplus PV power, use it to charge the battery
        elif 0 < pv_active_power - current_active_power < max_charge_active_power:
            active_power_to_charge = 2*(pv_active_power - current_active_power)
            aggregated_active_power = [0,0,0]

        return OptimizeConsumptionOutput(aggregated_active_power, aggregated_reactive_power, active_power_to_charge)


if __name__ == "__main__":

    helics_simulation_executor = HemsServiceWorkshop()
    helics_simulation_executor.start_simulation()
    helics_simulation_executor.stop_simulation()