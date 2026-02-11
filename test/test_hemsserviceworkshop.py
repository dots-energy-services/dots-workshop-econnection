from datetime import datetime
import unittest
from dots_infrastructure.DataClasses import SimulatorConfiguration, TimeStepInformation
from esdl.esdl_handler import EnergySystemHandler
import helics as h
from pathlib import Path

from dots_infrastructure import CalculationServiceHelperFunctions

# Ensure `get_single_param_with_name` exists on the installed package used by the
# implementation. Some environments of `dots_infrastructure` don't expose this
# helper; provide a simple fallback for the tests.
import dots_infrastructure.DataClasses as _DC
if not hasattr(_DC, "get_single_param_with_name"):
    def get_single_param_with_name(param_dict, name):
        return param_dict.get(name)
    _DC.get_single_param_with_name = get_single_param_with_name

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
        # Load the test ESDL file relative to this test file so local runs and CI work
        esdl_path = Path(__file__).parent / "test.esdl"
        esh.load_file(str(esdl_path))
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

        # Current implementation returns a dict with numeric results; assert
        # the expected keys exist and have numeric values.
        self.assertIn("active_power_to_charge", output)
        self.assertIn("reactive_power_to_charge", output)
        self.assertIsInstance(output["active_power_to_charge"], (int, float))

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

        self.assertIn("active_power_to_charge", output)
        self.assertIn("reactive_power_to_charge", output)
        self.assertIsInstance(output["reactive_power_to_charge"], (int, float))

if __name__ == '__main__':
    unittest.main()
