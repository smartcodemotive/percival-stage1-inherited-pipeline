import unittest
from datetime import date
from pathlib import Path

from read.figures import build
from read.load import load_room
from read.rules import annual_value, live_status

ROOM = Path(__file__).parent.parent / "room"
AS_OF = date(2026, 6, 30)


class RoomA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.room = load_room(ROOM)
        cls.results = build(cls.room, AS_OF)
        cls.figures = cls.results["figures"]
        cls.by_line = {l["line_id"]: l for l in cls.results["lines"]}

    def line(self, line_id):
        return next(l for l in self.room.lines if l.line_id == line_id)

    def test_cadences(self):
        self.assertEqual(annual_value(self.line("L001")), 180000)
        self.assertEqual(annual_value(self.line("L003")), 120000)
        self.assertEqual(annual_value(self.line("L012")), 180000)

    def test_usage_minimum_annualises(self):
        self.assertEqual(annual_value(self.line("L020")), 18000)
        self.assertEqual(self.by_line["L020"]["live_status"], "live")

    def test_contracted_is_scoped_by_the_missing_price(self):
        c = self.figures["contracted"]
        self.assertEqual(c["status"], "scoped")
        self.assertEqual(c["known"], 1472000)
        self.assertEqual(c["unknown_lines"], ["L011"])

    def test_future_start(self):
        self.assertEqual(self.figures["future_start"]["known"], 60000)

    def test_amendment_replaces_superseded_line(self):
        self.assertEqual(self.figures["live_by_customer"]["A03"]["known"], 200000)
        self.assertNotIn("L004", self.by_line)
        self.assertEqual(self.by_line["L005"]["live_status"], "live")

    def test_partly_live_contract_is_not_prorated(self):
        b = self.figures["live_by_customer"]["A04"]
        self.assertEqual((b["status"], b["low"], b["high"]), ("range", 20000, 140000))
        self.assertEqual(self.by_line["L006"]["live_status"], "unknown")

    def test_parent_grouping(self):
        self.assertEqual(self.figures["live_by_customer"]["P01"]["known"], 300000)

    def test_unmapped_account_is_kept(self):
        self.assertEqual(self.figures["live_by_customer"]["A12"]["known"], 130000)
        self.assertFalse(self.figures["live_by_customer"]["A12"]["mapped"])

    def test_pinecrest_without_go_live_is_unknown(self):
        # L018 has a contract start but no activation row. Rule 11: not live.
        self.assertEqual(self.by_line["L018"]["live_status"], "unknown")
        a11 = self.figures["live_by_customer"]["A11"]
        self.assertEqual(a11["status"], "range")
        self.assertEqual(a11["known"], 0)
        self.assertEqual(a11["high"], 48000)
        # management figure stays separate (rule 3)
        self.assertEqual(self.room.management["Pinecrest Schools"], 48000)

    def test_live_range(self):
        live = self.figures["live"]
        # known live excludes L018 (no evidence) and L006 (partly live)
        self.assertEqual(live["status"], "range")
        self.assertEqual(live["known"], 1244000)
        self.assertEqual(live["low"], 1244000)
        self.assertEqual(live["high"], 1412000)
        self.assertEqual(live["unknown_lines"], ["L006", "L018"])

    def test_exclusions(self):
        reasons = {e["line_id"] for e in self.results["excluded"]}
        self.assertEqual(reasons, {"L002", "L004", "L014", "L015", "L017"})

    def test_top3_withheld_when_live_incomplete(self):
        top = self.figures["top3_share_pct"]
        self.assertEqual(top["status"], "scoped")
        self.assertIsNone(top["value"])

    def test_start_date_is_not_live_evidence(self):
        self.assertEqual(live_status(self.line("L018"), self.room, AS_OF), "unknown")

    def test_calculation_records_present(self):
        records = self.results["records"]
        self.assertTrue(records)
        names = {r["figure"] for r in records}
        self.assertIn("contracted", names)
        self.assertIn("live", names)
        for r in records:
            self.assertIn(r["checks"]["citation"]["status"], {"pass", "fail", "not possible"})
            self.assertIn(r["checks"]["completeness"]["status"], {"pass", "fail", "not possible"})
        # on room A both checks should pass
        self.assertEqual(records[0]["checks"]["citation"]["status"], "pass")
        self.assertEqual(records[0]["checks"]["completeness"]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
