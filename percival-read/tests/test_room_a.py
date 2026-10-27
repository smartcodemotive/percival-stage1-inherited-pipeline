import unittest
from datetime import date
from pathlib import Path

from read.figures import build
from read.load import load_room
from read.rules import annual_value

ROOM = Path(__file__).parent.parent / "room"
AS_OF = date(2026, 6, 30)


class RoomA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.room = load_room(ROOM)
        cls.results = build(cls.room, AS_OF)
        cls.figures = cls.results["figures"]

    def line(self, line_id):
        return next(l for l in self.room.lines if l.line_id == line_id)

    def test_cadences(self):
        self.assertEqual(annual_value(self.line("L001")), 180000)
        self.assertEqual(annual_value(self.line("L003")), 120000)
        self.assertEqual(annual_value(self.line("L012")), 180000)

    def test_contracted_is_scoped_by_the_missing_price(self):
        c = self.figures["contracted"]
        self.assertEqual(c["status"], "scoped")
        self.assertEqual(c["known"], 1472000)
        self.assertEqual(c["unknown_lines"], ["L011"])

    def test_future_start(self):
        self.assertEqual(self.figures["future_start"]["known"], 60000)

    def test_amendment_replaces_superseded_line(self):
        self.assertEqual(self.figures["live_by_customer"]["A03"]["known"], 200000)

    def test_partly_live_contract_is_not_prorated(self):
        b = self.figures["live_by_customer"]["A04"]
        self.assertEqual((b["status"], b["low"], b["high"]), ("range", 20000, 140000))

    def test_parent_grouping(self):
        self.assertEqual(self.figures["live_by_customer"]["P01"]["known"], 300000)

    def test_unmapped_account_is_kept(self):
        self.assertEqual(self.figures["live_by_customer"]["A12"]["known"], 130000)
        self.assertFalse(self.figures["live_by_customer"]["A12"]["mapped"])

    def test_pinecrest_live_matches_management(self):
        self.assertEqual(self.figures["live_by_customer"]["A11"]["known"], 48000)
        self.assertEqual(self.room.management["Pinecrest Schools"], 48000)

    def test_live_range(self):
        live = self.figures["live"]
        self.assertEqual((live["low"], live["high"]), (1292000, 1412000))

    def test_exclusions(self):
        reasons = {e["line_id"] for e in self.results["excluded"]}
        self.assertEqual(reasons, {"L002", "L004", "L014", "L015", "L017"})

    def test_top3(self):
        self.assertAlmostEqual(self.figures["top3_share_pct"]["value"], 52.63, places=2)


if __name__ == "__main__":
    unittest.main()
