#!/usr/bin/env python3
"""Offline helpers. Never reads browser sessions, sends DMs, or uploads data."""

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

KST = timezone(timedelta(hours=9))
DONE = {"발송 완료", "발송완료", "confirmed"}
PENDING = {"전송 시도", "전송시도", "attempted", "pending"}
RESERVED = {"p", "reel", "reels", "direct", "stories", "explore", "accounts"}
ASSETS = Path(__file__).resolve().parents[1] / "assets"


def normalize_id(value):
    value = value.strip()
    if "://" in value:
        parsed = urlparse(value)
        if parsed.scheme not in {"https", "http"} or parsed.hostname not in {
            "instagram.com", "www.instagram.com", "m.instagram.com"
        }:
            raise ValueError("Instagram 프로필 주소가 아닙니다")
        parts = [part for part in parsed.path.split("/") if part]
        value = parts[0] if parts else ""
        if len(parts) > 1 and parts[1:] not in [["reels"], ["tagged"]]:
            raise ValueError("프로필 또는 프로필 릴스 주소를 입력하세요")
    value = value.removeprefix("@").lower()
    if not re.fullmatch(r"[a-z0-9._]{1,30}", value) or value in RESERVED:
        raise ValueError("유효한 계정 ID를 확인할 수 없습니다")
    return value


def render_message(kind, name=None):
    filename = "contact.txt" if kind == "contact" else "address-guide.txt"
    body = (ASSETS / filename).read_text(encoding="utf-8-sig").strip()
    if kind == "address":
        if name is not None:
            raise ValueError("주소 가이드에는 호칭 자리표시자가 없습니다")
        return body
    if body.count("[호칭]") != 1:
        raise ValueError("승인 신규 컨택 원문의 호칭 자리표시자를 확인하세요")
    if name is not None and any(c in name for c in "\r\n\t"):
        raise ValueError("호칭에 줄바꿈을 넣을 수 없습니다")
    salutation = name.strip() + "님 " if name and name.strip() else ""
    return body.replace("[호칭]", salutation)


def parse_time(value):
    # PowerShell DateTime can serialize 7 fractional digits; Python 3.9 accepts 6.
    value = re.sub(r"(\.\d{6})\d+(?=Z|[+-]\d{2}:\d{2}|$)", r"\1", value)
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("시각에 시간대가 없습니다")
    return parsed


def audit_ledger(data, day, manual=0):
    date.fromisoformat(day)
    if manual < 0:
        raise ValueError("수동 신규 발송 수는 0 이상이어야 합니다")
    records = data if isinstance(data, list) else data.get("records") if isinstance(data, dict) else None
    if not isinstance(records, list):
        raise ValueError("원장은 배열 또는 records 배열을 가진 객체여야 합니다")
    report = {
        "dateKST": day, "manualNew": manual, "confirmedToday": 0,
        "attemptsToday": 0, "pendingIds": [], "duplicateIds": [],
        "spacingViolations": [], "invalidRecords": []
    }
    seen, done_today, today = set(), set(), []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            report["invalidRecords"].append({"index": index, "reason": "객체 아님"})
            continue
        if record.get("kind", "cold") != "cold":
            continue
        try:
            account_id = normalize_id(record["id"])
            attempt = parse_time(record["attemptAt"])
            actual_day = attempt.astimezone(KST).date().isoformat()
            if actual_day == day:
                # An attempted send consumes a slot even if its confirmation is invalid.
                today.append((attempt, account_id))
            status = record["status"]
            if status not in DONE | PENDING:
                raise ValueError("알 수 없는 발송 상태")
            if account_id in seen:
                report["duplicateIds"].append(account_id)
            seen.add(account_id)
            declared_day = record.get("dateKST")
            if declared_day and declared_day != actual_day:
                report["invalidRecords"].append({
                    "index": index, "id": account_id, "reason": "dateKST와 실제 시도일 불일치"
                })
            confirmed = None
            if status in DONE:
                confirmed = parse_time(record["confirmedAt"])
                if confirmed < attempt or not record.get("evidence"):
                    raise ValueError("완료 시각 또는 확인 근거 불충분")
                if confirmed.astimezone(KST).date().isoformat() != actual_day:
                    report["invalidRecords"].append({
                        "index": index, "id": account_id, "reason": "자정 경계 전송일 수동 대조 필요"
                    })
            else:
                report["pendingIds"].append(account_id)
            if actual_day == day:
                if confirmed is not None:
                    done_today.add(account_id)
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            report["invalidRecords"].append({"index": index, "reason": str(error)})
    today.sort()
    for previous, current in zip(today, today[1:]):
        gap = (current[0] - previous[0]).total_seconds()
        if gap < 60:
            report["spacingViolations"].append({
                "previous": previous[1], "current": current[1], "seconds": gap
            })
    report["confirmedToday"] = len(done_today)
    report["attemptsToday"] = len(today)
    report["occupiedSlots"] = len(today) + manual
    report["remainingAllowance"] = max(0, 100 - report["occupiedSlots"])
    report["overDailyLimit"] = report["occupiedSlots"] > 100
    report["needsReview"] = bool(
        report["pendingIds"] or report["duplicateIds"] or report["spacingViolations"]
        or report["invalidRecords"] or report["overDailyLimit"]
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    normal = commands.add_parser("normalize")
    normal.add_argument("values", nargs="+")
    render = commands.add_parser("render")
    render.add_argument("kind", choices=["contact", "address"])
    render.add_argument("--name", help="이미 검증한 이름 또는 활동명. 미지정이면 생략")
    audit = commands.add_parser("audit")
    audit.add_argument("ledger", type=Path)
    audit.add_argument("--date", required=True, help="한국시간 YYYY-MM-DD")
    audit.add_argument("--manual", required=True, type=int, help="확인된 수동 신규 수. 회신 제외")
    args = parser.parse_args()
    try:
        if args.command == "normalize":
            print(json.dumps([normalize_id(v) for v in args.values], ensure_ascii=False))
        elif args.command == "render":
            print(render_message(args.kind, args.name))
        else:
            result = audit_ledger(
                json.loads(args.ledger.read_text(encoding="utf-8-sig")), args.date, args.manual
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2 if result["needsReview"] else 0
    except (OSError, ValueError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    sys.exit(main())
