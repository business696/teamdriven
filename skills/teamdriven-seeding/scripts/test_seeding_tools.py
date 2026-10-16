"""Synthetic, offline regression checks; no real recipient data."""
import unittest
from pathlib import Path

from seeding_tools import audit_ledger, normalize_id, parse_time, render_message


def sent(account_id, attempt, confirmed, day="2026-10-16"):
    return {"id": account_id, "attemptAt": attempt, "confirmedAt": confirmed,
            "dateKST": day, "status": "발송 완료", "evidence": "synthetic proof"}


class SeedingToolsTests(unittest.TestCase):
    def test_powershell_fractional_seconds(self):
        parsed = parse_time("2026-10-16T00:43:46.5423472Z")
        self.assertEqual(parsed.microsecond, 542347)

    def test_normalization(self):
        self.assertEqual(normalize_id("https://www.instagram.com/Example.Id/reels/?hl=ko"), "example.id")
        self.assertEqual(normalize_id("@Example.Id"), "example.id")
        for invalid in ["https://example.com/person", "https://www.instagram.com/reel/ABC/", "a b"]:
            with self.assertRaises(ValueError):
                normalize_id(invalid)

    def test_only_salutation_changes(self):
        raw = (Path(__file__).resolve().parents[1] / "assets/contact.txt").read_text(encoding="utf-8-sig").strip()
        self.assertEqual(render_message("contact", "활동명"), raw.replace("[호칭]", "활동명님 "))
        self.assertEqual(render_message("contact"), raw.replace("[호칭]", ""))
        address = (Path(__file__).resolve().parents[1] / "assets/address-guide.txt").read_text(encoding="utf-8-sig").strip()
        self.assertEqual(render_message("address"), address)
        with self.assertRaises(ValueError):
            render_message("contact", "one\ntwo")

    def test_kst_day_not_utc_day_and_reply_exclusion(self):
        data = [sent("alpha", "2026-10-15T15:01:00Z", "2026-10-15T15:01:05Z"),
                sent("beta", "2026-10-15T14:59:00Z", "2026-10-15T14:59:05Z", "2026-10-15"),
                {"kind": "guide", "id": "gamma"}]
        result = audit_ledger(data, "2026-10-16", manual=2)
        self.assertEqual(result["confirmedToday"], 1)
        self.assertEqual(result["occupiedSlots"], 3)
        self.assertFalse(result["needsReview"])

    def test_pending_and_duplicate_are_not_clean(self):
        data = [sent("alpha", "2026-10-16T00:00:00Z", "2026-10-16T00:00:05Z"),
                {"id": "alpha", "attemptAt": "2026-10-16T00:00:30Z", "status": "전송 시도"}]
        result = audit_ledger(data, "2026-10-16")
        self.assertEqual(result["duplicateIds"], ["alpha"])
        self.assertEqual(result["pendingIds"], ["alpha"])
        self.assertEqual(len(result["spacingViolations"]), 1)
        self.assertTrue(result["needsReview"])

    def test_unknown_time_and_cross_midnight_need_review(self):
        data = [sent("alpha", "2026-10-16T00:00:00", "2026-10-16T00:00:10"),
                sent("beta", "2026-10-16T14:59:58Z", "2026-10-16T15:00:05Z")]
        self.assertEqual(len(audit_ledger(data, "2026-10-16")["invalidRecords"]), 2)

    def test_daily_limit_includes_manual_and_attempts(self):
        data = [{"id": "alpha", "attemptAt": "2026-10-16T00:00:00Z", "status": "전송 시도"}]
        result = audit_ledger(data, "2026-10-16", manual=100)
        self.assertTrue(result["overDailyLimit"])
        self.assertEqual(result["remainingAllowance"], 0)

    def test_invalid_confirmation_still_occupies_attempt_slot(self):
        data = [{"id": "alpha", "attemptAt": "2026-10-16T00:00:00Z", "status": "발송 완료"}]
        result = audit_ledger(data, "2026-10-16", manual=99)
        self.assertEqual(result["attemptsToday"], 1)
        self.assertEqual(result["confirmedToday"], 0)
        self.assertEqual(result["remainingAllowance"], 0)
        self.assertTrue(result["needsReview"])


if __name__ == "__main__":
    unittest.main()
