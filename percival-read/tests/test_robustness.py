"""Fixtures that mimic messy exports — the kind of thing hidden rooms may throw at us."""
import tempfile
import unittest
from datetime import date
from pathlib import Path

from read.figures import build
from read.load import load_room, parse_date, parse_number
from read.rules import annual_value

AS_OF = date(2026, 6, 30)


def _write_room(dirpath: Path, contracts: str, go_live: str, customers: str, management: str) -> Path:
    (dirpath / "contracts.csv").write_text(contracts, encoding="utf-8")
    (dirpath / "go_live.csv").write_text(go_live, encoding="utf-8")
    (dirpath / "customers.csv").write_text(customers, encoding="utf-8")
    (dirpath / "management_arr_summary.csv").write_text(management, encoding="utf-8")
    return dirpath


class ParseHelpers(unittest.TestCase):
    def test_numbers(self):
        self.assertEqual(parse_number("$1,500.00"), 1500.0)
        self.assertEqual(parse_number("1.500,00"), 1500.0)
        self.assertEqual(parse_number("(200)"), -200.0)
        self.assertIsNone(parse_number("TBD"))
        self.assertIsNone(parse_number(""))

    def test_dates(self):
        self.assertEqual(parse_date("2026-06-30"), date(2026, 6, 30))
        self.assertEqual(parse_date("30/06/2026"), date(2026, 6, 30))
        self.assertEqual(parse_date("30-Jun-2026"), date(2026, 6, 30))
        self.assertIsNone(parse_date("n/a"))


class MessyRoom(unittest.TestCase):
    def test_alias_columns_and_formats(self):
        contracts = "\n".join(
            [
                "Line ID,Contract,Account,Product,Type,Amount,Frequency,Term (months),Signed,Start,End,Supersedes,Cancelled,Sites,Notes",
                "X1,C1,Acme,Platform,Subscription,\"$10,000\",Monthly,12,01/15/2025,2025-02-01,2027-01-31,,,1,",
                "X2,C1,Acme,Setup,one-off,5000,once,,01/15/2025,2025-02-01,,,,1,",
                "X3,C2,Beta,Platform,recurring,£24000,quarterly,24,2025-03-01,2025-04-01,2027-03-31,,,1,",
            ]
        )
        go_live = "\n".join(
            [
                "line_id,site,activation_date,evidence",
                "X1,,2025-02-01,log",
            ]
        )
        customers = "\n".join(
            [
                "account_id,legal_name,parent_id,parent_name",
                "Acme,Acme Corp,,",
                "Beta,Beta Ltd,,",
            ]
        )
        management = "\n".join(
            [
                "customer,reported_arr",
                "Acme Corp,120000",
                "Total,120000",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            room_path = _write_room(Path(tmp), contracts, go_live, customers, management)
            room = load_room(room_path)
            results = build(room, AS_OF)

        by_id = {l.line_id: l for l in room.lines}
        self.assertEqual(annual_value(by_id["X1"]), 120000)
        self.assertEqual(annual_value(by_id["X3"]), 96000)
        excl = {e["line_id"] for e in results["excluded"]}
        self.assertIn("X2", excl)
        # X3 has no go-live → unknown, not silently live
        line_status = {l["line_id"]: l["live_status"] for l in results["lines"]}
        self.assertEqual(line_status["X1"], "live")
        self.assertEqual(line_status["X3"], "unknown")
        # run must produce the output shape even when currency looks like GBP
        self.assertIn(results["currency"], {"USD", "GBP"})
        self.assertEqual(results["figures"]["contracted"]["status"], "complete")

    def test_term_fee_without_term_months_is_unknown_not_crash(self):
        contracts = "\n".join(
            [
                "line_id,contract_id,account_id,product,line_type,price,cadence,term_months,signed_date,start_date,end_date,supersedes_line_id,cancel_effective_date,sites_in_scope,notes",
                "T1,C,A,Platform,recurring,90000,term,,2025-01-01,2025-02-01,2027-01-31,,,1,",
            ]
        )
        go_live = "line_id,site,live_date,evidence\nT1,,2025-02-01,x\n"
        customers = "account_id,legal_name,parent_id,parent_name\nA,A,,\n"
        management = "customer,reported_arr\nTotal,0\n"
        with tempfile.TemporaryDirectory() as tmp:
            room = load_room(_write_room(Path(tmp), contracts, go_live, customers, management))
            results = build(room, AS_OF)
        self.assertIsNone(results["lines"][0]["annual_value"])
        self.assertEqual(results["figures"]["contracted"]["status"], "scoped")
        self.assertEqual(results["figures"]["contracted"]["unknown_lines"], ["T1"])

    def test_does_not_crash_on_empty_optional_fields(self):
        contracts = "\n".join(
            [
                "line_id,contract_id,account_id,product,line_type,price,cadence,term_months,signed_date,start_date,end_date,supersedes_line_id,cancel_effective_date,sites_in_scope,notes",
                "Z1,C,A,Platform,recurring,1000,monthly,,,, ,,,,",
            ]
        )
        go_live = "line_id,site,live_date,evidence\n"
        customers = "account_id,legal_name,parent_id,parent_name\nA,A,,\n"
        management = "customer,reported_arr\nTotal,0\n"
        with tempfile.TemporaryDirectory() as tmp:
            results = build(load_room(_write_room(Path(tmp), contracts, go_live, customers, management)), AS_OF)
        # unsigned → excluded, not a crash
        self.assertTrue(any(e["line_id"] == "Z1" for e in results["excluded"]))


if __name__ == "__main__":
    unittest.main()
