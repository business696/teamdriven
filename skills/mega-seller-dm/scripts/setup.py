#!/usr/bin/env python3
"""Save non-secret account and Notion settings locally. Does not log in."""
import json
import os
from pathlib import Path
from urllib.parse import urlparse

CONFIG = Path(__file__).resolve().parents[1] / ".local" / "config.json"


def instagram_id(value):
    value = value.strip()
    if value.startswith("https://"):
        parsed = urlparse(value)
        if parsed.hostname not in {"instagram.com", "www.instagram.com"}:
            raise ValueError("Instagram ID 또는 공식 프로필 URL을 입력하세요.")
        value = parsed.path.strip("/")
    value = value.removeprefix("@").lower()
    if not 1 <= len(value) <= 30 or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789._" for c in value):
        raise ValueError("올바른 Instagram ID를 입력하세요.")
    return value


def notion_url(value):
    value = value.strip()
    parsed = urlparse(value)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not (host in {"notion.so", "www.notion.so", "app.notion.com"} or host.endswith(".notion.site")):
        raise ValueError("https://로 시작하는 Notion DB/페이지 URL을 입력하세요.")
    if parsed.username or parsed.password or not parsed.path.strip("/"):
        raise ValueError("특정 Notion DB/페이지 URL이 필요합니다.")
    return value


def person_name(value):
    value = value.strip()
    if not value or len(value) > 80 or any(c in value for c in "\r\n\t[]{}<>"):
        raise ValueError("담당자명은 줄바꿈·괄호 없는 1~80자로 입력하세요.")
    return value


def marketing_hub_url(value):
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname != "business.facebook.com":
        raise ValueError("실제 Meta 마케팅허브의 https://business.facebook.com/ 주소를 입력하세요.")
    if parsed.username or parsed.password or not parsed.path.strip("/") or "login" in parsed.path.lower():
        raise ValueError("로그인 페이지가 아닌, 브랜드를 선택한 마케팅허브 URL을 복사하세요.")
    return value


def ask(label, default, validator):
    while True:
        value = input(f"{label}" + (f" [{default}]" if default else "") + ": ").strip() or default
        try:
            return validator(value)
        except ValueError as error:
            print(error)


def main():
    current = {}
    if CONFIG.exists():
        current = json.loads(CONFIG.read_text(encoding="utf-8"))
        if input("기존 설정을 수정할까요? [y/N]: ").strip().lower() != "y":
            print("기존 설정을 유지했습니다.")
            return
    print("비밀번호·쿠키·토큰은 입력하지 마세요. 계정 연결과 로그인은 별도로 진행합니다.")
    config = {**current,
        "version": 2,
        "brand": "위시어",
        "contact_channel": "meta_creator_marketing_hub",
        "instagram_sender": ask("발신 Instagram ID", current.get("instagram_sender", ""), instagram_id),
        "contact_name": ask("담당자명", current.get("contact_name", "김하늘"), person_name),
        "notion_database_url": ask("Notion 인플루언서 DB URL", current.get("notion_database_url", ""), notion_url),
        "notion_daily_list_url": ask("Notion 일자 리스트 URL", current.get("notion_daily_list_url", ""), notion_url),
        "creator_marketing_hub_url": ask("로그인 후 브랜드를 선택한 Meta 마케팅허브 URL", current.get("creator_marketing_hub_url", ""), marketing_hub_url),
        "screen_mode": current.get("screen_mode", "no-disruption"),
        "timezone": "Asia/Seoul",
    }
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(CONFIG.parent, 0o700)
    temporary = CONFIG.with_suffix(".tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(config, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.chmod(temporary, 0o600)
    temporary.replace(CONFIG)
    print(f"설정 저장: {CONFIG}")
    print("연결·권한 미검증 / 실제 발송 없음. Codex에 ‘어사이드의 마케팅허브와 Notion 연결 점검해줘’라고 요청하세요.")


if __name__ == "__main__":
    main()
