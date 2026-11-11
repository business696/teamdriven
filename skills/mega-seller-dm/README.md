# 메가셀러 DM 컨택 스킬

어사이드에서 실제 Instagram DM 이력을 확인하고, 미컨택 선별·위시어 확정 문구·승인된 발송·Notion 기록을 이어서 처리하는 Codex 스킬입니다.

## 설치와 첫 실행

Codex에 아래 문장을 보내 설치하세요.

```text
$skill-installer https://github.com/business696/teamdriven/tree/main/skills/mega-seller-dm 이 스킬 설치해줘.
```

설치 후 다음 메시지에서 **“$mega-seller-dm 처음 설정해줘”**라고 요청하면 됩니다. 이미 설치돼 있다면 기존 `.local/` 설정을 보존하고 스킬 파일만 업데이트하세요.

설정할 항목은 네 가지입니다.

1. 발신 Instagram ID
2. 담당자명 (기본 김하늘)
3. Notion 인플루언서 DB URL
4. Notion 일자별 메가셀러 리스트 URL

대화로 설정하거나, 설치된 스킬 폴더에서 `python3 scripts/setup.py`를 실행하세요. Python 3.9 이상이면 추가 패키지가 필요 없습니다. 설정은 Git에서 제외되는 `.local/config.json`에 저장합니다.

## 실행 예시

```text
$mega-seller-dm 메가셀러 중 실제 DM 미컨택 명단만 뽑아줘. 보내지는 마.
```

```text
$mega-seller-dm 방금 확인한 미컨택 명단에 확정 문구로 보내고 Notion에 기록해줘.
```

문구만 출력하려면 `python3 scripts/render_dm.py --name '크리에이터명'`을 사용하세요. 원문을 유지하고 이름·담당자만 치환합니다.

## 필요한 연결

- Codex 호스트가 제공하는 Aside 제어 도구와 사용자의 Instagram 로그인
- 지정 DB·리스트에 접근할 수 있는 Notion API/커넥터

이 패키지는 로그인·브라우저 확장·API 서버를 자동 설치하지 않습니다. 첫 실행에서 현재 도구를 확인하고 필요한 연결을 안내합니다. 호스트가 Aside 백그라운드 제어를 제공하지 않으면 화면 조작 없이 자동 조회·발송하는 것은 지원되지 않습니다. 다른 브라우저로 바꾸거나 화면을 앞으로 띄워 우회하지 않습니다.

스킬 검증·설정 저장은 실제 DM 발송 검증과 별개입니다. 실행 로그, 수신자 명단·주소, 쿠키·비밀번호·토큰은 저장소에 넣지 마세요. 제품·매출 문구는 위시어 확정본이며 다른 브랜드에 그대로 전용하지 않습니다.
