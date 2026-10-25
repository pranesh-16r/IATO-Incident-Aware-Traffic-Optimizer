import unittest
from simulation import shortest_route, run_simulation

class IATOTests(unittest.TestCase):
    def test_same_origin_route(self):
        self.assertEqual(shortest_route("North", "North"), ["North"])

    def test_route_exists_without_closures(self):
        route = shortest_route("North", "South")
        self.assertIsNotNone(route)
        self.assertEqual(route[0], "North")
        self.assertEqual(route[-1], "South")

    def test_simulation_is_reproducible(self):
        a = run_simulation(20, 4, "Adaptive", "Normal traffic", 123, True)
        b = run_simulation(20, 4, "Adaptive", "Normal traffic", 123, True)
        self.assertEqual(a["vehicles_served"], b["vehicles_served"])
        self.assertEqual(a["data"].to_dict(), b["data"].to_dict())

    def test_vehicle_conservation(self):
        for controller in ["Fixed-time", "Adaptive"]:
            result = run_simulation(80, 5, controller, "North congestion", 123, True)
            self.assertEqual(
                result["total_arrivals"],
                result["vehicles_served"] + result["remaining_queue"]
            )
            self.assertTrue(result["data"]["Conservation check"].all())

    def test_invalid_controller_rejected(self):
        with self.assertRaises(ValueError):
            run_simulation(10, 2, "QuantumMagic")

if __name__ == "__main__":
    unittest.main()
