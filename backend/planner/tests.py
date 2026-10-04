from datetime import datetime, timezone
from django.test import SimpleTestCase
from planner.services import plan_hos, build_daily_logs

class HosPlannerTests(SimpleTestCase):
    def test_short_trip_has_pickup_drive_dropoff(self):
        events, _ = plan_hos(100, 2, 0, "Pickup", "Dropoff")
        labels = [e.label for e in events]
        self.assertIn("Pickup / loading", labels)
        self.assertIn("Driving", labels)
        self.assertIn("Drop-off / unloading", labels)

    def test_break_after_eight_hours(self):
        events, _ = plan_hos(600, 10, 0, "Pickup", "Dropoff")
        self.assertTrue(any(e.label == "30-minute rest break" for e in events))

    def test_long_trip_has_daily_rest(self):
        events, _ = plan_hos(1000, 18, 0, "Pickup", "Dropoff")
        self.assertTrue(any(e.label == "10-hour off-duty rest" for e in events))

    def test_cycle_restart_when_cycle_is_full(self):
        events, _ = plan_hos(100, 2, 70, "Pickup", "Dropoff")
        self.assertTrue(any(e.label == "34-hour cycle restart" for e in events))

    def test_daily_logs_total_24_hours(self):
        events, _ = plan_hos(600, 10, 0, "Pickup", "Dropoff")
        logs = build_daily_logs(events)
        for log in logs:
            self.assertAlmostEqual(sum(log["totals"].values()), 24, places=2)
