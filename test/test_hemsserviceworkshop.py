from datetime import datetime
import unittest
from dots_infrastructure.DataClasses import SimulatorConfiguration, TimeStepInformation
from esdl.esdl_handler import EnergySystemHandler
import helics as h

from dots_infrastructure import CalculationServiceHelperFunctions

from HemsServiceWorkshop.hems_service_workshop import HemsServiceWorkshop

BROKER_TEST_PORT = 23404
START_DATE_TIME = datetime(2024, 1, 1, 0, 0, 0)
SIMULATION_DURATION_IN_SECONDS = 960
TEST_ID = "5c19dcff-b004-4644-99b9-f42d15a34f3a"

def simulator_environment_e_connection():
    return SimulatorConfiguration("EConnection", [TEST_ID], "Mock-Econnection", "127.0.0.1", BROKER_TEST_PORT, "test-id", SIMULATION_DURATION_IN_SECONDS, START_DATE_TIME, "test-host", "test-port", "test-username", "test-password", "test-database-name", h.HelicsLogLevel.DEBUG, ["PVInstallation", "EConnection"])

class Test(unittest.TestCase):

    def setUp(self):
        CalculationServiceHelperFunctions.get_simulator_configuration_from_environment = simulator_environment_e_connection
        esh = EnergySystemHandler()
        # Use path relative to test file location for CI compatibility
        import os
        test_dir = os.path.dirname(os.path.abspath(__file__))
        esdl_path = os.path.join(test_dir, "test.esdl")
        esh.load_file(esdl_path)
        self.energy_system = esh.get_energy_system()

    def test_when_pv_can_fully_cover_demand_active_power_is_zero_and_battery_is_charged(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 108.0,
            "pv_active_power": 110,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1,24), TEST_ID, self.energy_system)

        print(f"\n--- Test 1: PV covers demand ---")
        print(f"Input: PV={param_dict['pv_active_power']}W, Demand={param_dict['current_active_power']}W")
        print(f"Output: aggregated_active_power={output.aggregated_active_power}, active_power_to_charge={output.active_power_to_charge}W")
        
        self.assertListEqual(output.aggregated_active_power, [0,0,0])
        self.assertEqual(output.active_power_to_charge, 2)

    def test_when_pv_cannot_fully_cover_demand_active_power_is_evenly_divided(self):
        param_dict = {
            "current_reactive_power": 3,
            "current_active_power": 108.0,
            "pv_active_power": 108,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1,24), TEST_ID, self.energy_system)

        print(f"\n--- Test 2: PV equals demand ---")
        print(f"Input: PV={param_dict['pv_active_power']}W, Demand={param_dict['current_active_power']}W")
        print(f"Output: aggregated_active_power={output.aggregated_active_power}, active_power_to_charge={output.active_power_to_charge}W")
        
        self.assertListEqual(output.aggregated_active_power, [36,36,36])
        self.assertListEqual(output.aggregated_reactive_power, [1,1,1])

    def test_when_market_price_is_high_battery_discharges_to_sell(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 108.0,
            "pv_active_power": 110,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
            "market_price": 0.15,  # High price (> 0.01 threshold)
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1,24), TEST_ID, self.energy_system)

        print(f"\n--- Test 3: High market price ---")
        print(f"Input: PV={param_dict['pv_active_power']}W, Demand={param_dict['current_active_power']}W, Market Price={param_dict['market_price']} EUR/kWh")
        print(f"Output: aggregated_active_power={output.aggregated_active_power}, active_power_to_charge={output.active_power_to_charge}W")
        print(f"Result: Battery discharges at max rate to sell power to grid during high prices")
        
        self.assertEqual(output.active_power_to_charge, -8)

    def test_when_market_price_is_moderate_battery_discharges_to_sell(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 108.0,
            "pv_active_power": 110,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
            "market_price": 0.02,  # Moderate but above threshold (> 0.01)
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1,24), TEST_ID, self.energy_system)

        print(f"\n--- Test 3b: Moderate market price (realistic) ---")
        print(f"Input: PV={param_dict['pv_active_power']}W, Demand={param_dict['current_active_power']}W, Market Price={param_dict['market_price']} EUR/kWh")
        print(f"Output: aggregated_active_power={output.aggregated_active_power}, active_power_to_charge={output.active_power_to_charge}W")
        print(f"Result: Battery discharges even at moderate prices above 0.01 EUR/kWh threshold")
        
        self.assertEqual(output.active_power_to_charge, -8)

    def test_when_excess_solar_exceeds_battery_capacity_feed_back_to_grid(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 100.0,
            "pv_active_power": 120,  # 20W surplus
            "max_charge_active_power": 10,  # Can only charge 10W
            "max_discharge_active_power": -8,
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1,24), TEST_ID, self.energy_system)

        print(f"\n--- Test 4: Excess solar exceeds battery capacity ---")
        print(f"Input: PV={param_dict['pv_active_power']}W, Demand={param_dict['current_active_power']}W, Max Charge={param_dict['max_charge_active_power']}W")
        print(f"Surplus: {param_dict['pv_active_power'] - param_dict['current_active_power']}W, Battery can only take {param_dict['max_charge_active_power']}W")
        print(f"Output: aggregated_active_power={output.aggregated_active_power}, active_power_to_charge={output.active_power_to_charge}W")
        print(f"Result: Battery charges at max rate, remaining {param_dict['pv_active_power'] - param_dict['current_active_power'] - param_dict['max_charge_active_power']}W fed back to grid")
        
        self.assertEqual(output.active_power_to_charge, 10)
        # 10W excess should be fed back to grid (negative values)
        self.assertAlmostEqual(output.aggregated_active_power[0], -10/3, places=2)

    def test_market_price_input_is_retrieved_correctly(self):
        # Test with no market_price parameter (should default to 0)
        param_dict_no_price = {
            "current_reactive_power": 0,
            "current_active_power": 100.0,
            "pv_active_power": 100,
            "max_charge_active_power": 10,
            "max_discharge_active_power": -8,
        }

        # Test with market_price parameter
        param_dict_with_price = {
            "current_reactive_power": 0,
            "current_active_power": 100.0,
            "pv_active_power": 100,
            "max_charge_active_power": 10,
            "max_discharge_active_power": -8,
            "market_price": 0.2,  # Above threshold
        }

        hems_service = HemsServiceWorkshop()
        
        # Without market price (should behave normally)
        output1 = hems_service.optimize_consumption(param_dict_no_price, START_DATE_TIME, TimeStepInformation(1,24), TEST_ID, self.energy_system)
        
        # With high market price (should discharge)
        output2 = hems_service.optimize_consumption(param_dict_with_price, START_DATE_TIME, TimeStepInformation(1,24), TEST_ID, self.energy_system)

        print(f"\n--- Test 5: Market price input verification ---")
        print(f"Without market_price: active_power_to_charge={output1.active_power_to_charge}W (normal behavior)")
        print(f"With market_price=0.2: active_power_to_charge={output2.active_power_to_charge}W (should discharge)")
        print(f"Market price input retrieval: {'✓ WORKING' if output2.active_power_to_charge == -8 else '✗ NOT WORKING'}")
        
        # Without price, no charging/discharging needed (PV matches demand)
        self.assertEqual(output1.active_power_to_charge, 0)
        
        # With high price, should discharge at max rate
        self.assertEqual(output2.active_power_to_charge, -8)

if __name__ == '__main__':
    unittest.main()
