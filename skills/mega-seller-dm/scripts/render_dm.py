#!/usr/bin/env python3
"""Render an approved DM. No network access or message sending."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def clean_name(value):
    value = value.strip()
    if not value or len(value) > 80 or any(c in value for c in "\r\n\t[]{}<>") or "://" in value:
        raise ValueError("호칭에 사용할 이름을 줄바꿈·괄호 없는 1~80자로 입력하세요.")
    return value


def render(name, contact_name="김하늘"):
    template = (ROOT / "assets" / "dm.txt").read_text(encoding="utf-8")
    if "[이름]" not in template or "[담당자명]" not in template:
        raise ValueError("확정 문구의 이름·담당자명 치환 위치가 없습니다.")
    return template.replace("[이름]", clean_name(name)).replace("[담당자명]", clean_name(contact_name))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="님을 제외한 실제 호칭")
    args = parser.parse_args()
    config_file = ROOT / ".local" / "config.json"
    config = json.loads(config_file.read_text(encoding="utf-8")) if config_file.exists() else {}
    if config.get("brand", "위시어") != "위시어":
        parser.error("다른 브랜드는 해당 브랜드의 확정 문구가 필요합니다.")
    try:
        print(render(args.name, config.get("contact_name", "김하늘")), end="")
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
