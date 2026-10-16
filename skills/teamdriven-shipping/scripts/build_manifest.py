#!/usr/bin/env python3
"""Read a private shipping ledger and produce a reconciled daily JSON manifest."""
import argparse
import json
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
HEADERS = ["주문번호", "수령자명", "상품명", "옵션", "수량", "수령자전화번호", "수령자주소", "메모"]


def phone_key(value):
    if not isinstance(value, str):
        raise ValueError("phone must be a string to preserve the leading zero")
    digits = re.sub(r"\D", "", value)
    if not re.fullmatch(r"0\d{8,10}", digits):
        raise ValueError("invalid domestic recipient phone")
    return digits


def scheduled_date(record, holidays):
    explicit = date.fromisoformat(record["ship_date"]) if record.get("ship_date") else None
    if not record.get("received_at"):
        if explicit is not None:
            return explicit  # Historical migration with an evidenced shipping date.
        raise ValueError("received_at or an evidenced historical ship_date is required")
    received = datetime.fromisoformat(record["received_at"])
    if received.tzinfo is None:
        raise ValueError("received_at must include a timezone")
    received = received.astimezone(KST)
    day = received.date()
    if received.time() > time(16, 0):
        day += timedelta(days=1)
    while day.weekday() >= 5 or day in holidays:
        day += timedelta(days=1)
    if explicit is not None and explicit < day:
        evidence = record.get("cutoff_override_evidence")
        if record.get("cutoff_override_confirmed") is not True or not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("ship_date is before the cutoff schedule; a direct user-confirmed exception and its evidence are required")
    return explicit if explicit is not None else day


def build_manifest(ledger, target):
    target = date.fromisoformat(target)
    holidays = {date.fromisoformat(d) for d in ledger.get("holidays", [])}
    records = ledger["records"]
    record_ids = [r["id"] for r in records]
    if len(record_ids) != len(set(record_ids)) or any(not isinstance(i, str) or not i for i in record_ids):
        raise ValueError("record IDs must be nonempty and unique")
    delivered = set()
    delivery_dates = set()
    for delivery in ledger.get("deliveries", []):
        day = date.fromisoformat(delivery["date"])
        if day in delivery_dates:
            raise ValueError("keep only the final delivered revision for each date")
        delivery_dates.add(day)
        if delivery.get("handed_off") is True and day < target:
            delivered.update(delivery["record_ids"])
    rows, provenance, included = [], [], []
    recipients, shipment_lines = set(), set()
    boxes = singles = 0
    for record in records:
        status = record.get("status", "pending")
        if status not in {"pending", "cancelled", "shipped"}:
            raise ValueError(f"unknown status for {record['id']}")
        if status in {"cancelled", "shipped"} or record["id"] in delivered:
            continue
        if scheduled_date(record, holidays) > target:
            continue
        name, address = record["recipient_name"], record["address"]
        if not isinstance(name, str) or not name.strip() or not isinstance(address, str) or not address.strip():
            raise ValueError(f"missing recipient information for {record['id']}")
        phone = phone_key(record["phone"])
        address_key = re.sub(r"\s+", "", address)
        group = record.get("recipient_group")
        recipient = (name, phone, "confirmed:" + group if group else address_key)
        products = record["products"]
        if not products:
            raise ValueError(f"no products for {record['id']}")
        line_ids = [p["id"] for p in products]
        if len(line_ids) != len(set(line_ids)) or any(not isinstance(i, str) or not i for i in line_ids):
            raise ValueError(f"product line IDs must be unique for {record['id']}")
        for product in products:
            quantity, unit = product["quantity"], product["unit"]
            if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 1:
                raise ValueError(f"invalid quantity for {record['id']}/{product['id']}")
            if unit not in {"box", "single"} or not product.get("name"):
                raise ValueError(f"invalid product for {record['id']}/{product['id']}")
            option = product.get("option", "")
            key = (recipient, product["name"], option, unit, product.get("flavor", ""))
            if key in shipment_lines:
                raise ValueError(f"possible duplicate product shipment: {record['id']}/{product['id']}; reconcile the request, do not silently drop it")
            shipment_lines.add(key)
            memo = " / ".join(x for x in [record.get("memo", ""), product.get("memo", "")] if x)
            if unit == "single" and product.get("flavor"):
                memo = " / ".join(x for x in [product["flavor"] + " 낱개", memo] if x)
            rows.append([product.get("order_number", record.get("order_number", "")), name, product["name"], option, quantity, record["phone"], address, memo])
            provenance.append({"record_id": record["id"], "line_id": product["id"], "unit": unit})
            if unit == "box":
                boxes += quantity
            else:
                singles += quantity
        recipients.add(recipient)
        included.append(record["id"])
    return {"date": target.isoformat(), "headers": HEADERS, "rows": rows, "provenance": provenance, "included_record_ids": included, "counts": {"recipients": len(recipients), "product_rows": len(rows), "boxes": boxes, "singles": singles}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--date", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.ledger.resolve() == args.out.resolve():
        parser.error("output must not overwrite the ledger")
    try:
        manifest = build_manifest(json.loads(args.ledger.read_text(encoding="utf-8")), args.date)
    except (KeyError, TypeError, ValueError) as exc:
        parser.exit(2, f"Cannot build shipping manifest: {exc}\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.out.with_suffix(args.out.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(args.out)
    print(json.dumps(manifest["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
