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
        esh.load_file("./test.esdl")
        self.energy_system = esh.get_energy_system()

    ##############
    # NO BATTERY #
    ##############
    def test_when_pv_is_equal_to_demand_active_power_is_zero(self):
        param_dict = {
            "current_reactive_power": 3,
            "current_active_power": 108.0,
            "pv_active_power": 108,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1,24), TEST_ID, self.energy_system)

        self.assertEqual(output.active_power_to_charge, 0)
        self.assertListEqual(output.aggregated_active_power, [0,0,0])
        self.assertListEqual(output.aggregated_reactive_power, [1,1,1])

    ############
    # CHARGING #
    ############
    def test_when_pv_can_fully_cover_demand_active_power_is_zero_and_battery_is_charged(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 108.0,
            "pv_active_power": 110,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
        }

        # difference: 110 - 108 = 2 (charging!) with 0 grid power

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1,24), TEST_ID, self.energy_system)

        self.assertListEqual(output.aggregated_active_power, [0,0,0])
        self.assertEqual(output.active_power_to_charge, 2)

    def test_when_pv_can_fully_cover_demand_active_power_is_not_zero_if_above_limit(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 108.0,
            "pv_active_power": 108 + 8 + 3,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1, 24), TEST_ID, self.energy_system)

        self.assertEqual(output.active_power_to_charge, 8)
        self.assertListEqual(output.aggregated_active_power, [-1, -1, -1])


    ###############
    # DISCHARGING #
    ###############
    def test_when_demand_more_than_pv_battery_is_charging_with_zero_grid_usage(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 105.0,
            "pv_active_power": 100,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
        }

        # difference: 110 - 108 = 2 (charging!) with 0 grid power

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1,24), TEST_ID, self.energy_system)

        self.assertListEqual(output.aggregated_active_power, [0,0,0])
        self.assertEqual(output.active_power_to_charge, -5)  # discharging

    def test_when_demand_more_than_pv_battery_is_charging_with_grid_usage_if_above_limit(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 111.0,
            "pv_active_power": 100,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1, 24), TEST_ID, self.energy_system)

        self.assertListEqual(output.aggregated_active_power, [1, 1, 1])
        self.assertEqual(output.active_power_to_charge, -8)  # discharging at max


    ################
    # ENERGY PRICE #
    ################
    def test_charge_when_price_is_low(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 107.0,
            "pv_active_power": 110,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
            "day_ahead_price": 0.01, # lower than 0.05 limit, cheap electricity = dont deliver to grid
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1, 24), TEST_ID, self.energy_system)

        self.assertListEqual(output.aggregated_active_power, [0, 0, 0])
        self.assertEqual(output.active_power_to_charge, 3)

    def test_dont_charge_when_price_is_high(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 107.0,
            "pv_active_power": 110,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
            "day_ahead_price": 0.1, # higher than 0.05 limit, expensive electricity = deliver to grid
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1, 24), TEST_ID, self.energy_system)

        self.assertListEqual(output.aggregated_active_power, [-1, -1, -1])
        self.assertEqual(output.active_power_to_charge, 0)

    def test_discharge_when_price_is_low(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 110.0,
            "pv_active_power": 107,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
            "day_ahead_price": 0.01, # lower than 0.05 limit, cheap electricity = use from grid
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1, 24), TEST_ID, self.energy_system)

        self.assertListEqual(output.aggregated_active_power, [1, 1, 1])
        self.assertEqual(output.active_power_to_charge, 0)

    def test_dont_charge_when_price_is_high(self):
        param_dict = {
            "current_reactive_power": 0,
            "current_active_power": 110.0,
            "pv_active_power": 107,
            "max_charge_active_power": 8,
            "max_discharge_active_power": -8,
            "day_ahead_price": 0.1, # higher than 0.05 limit, expensive electricity = dont use from grid
        }

        hems_service = HemsServiceWorkshop()
        output = hems_service.optimize_consumption(param_dict, START_DATE_TIME, TimeStepInformation(1, 24), TEST_ID, self.energy_system)

        self.assertListEqual(output.aggregated_active_power, [0, 0, 0])
        self.assertEqual(output.active_power_to_charge, -3)

if __name__ == '__main__':
    unittest.main()
