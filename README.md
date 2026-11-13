# 팀드리븐 업무 스킬

시작 안내: [Notion 팀원 가이드](https://app.notion.com/p/4175fe83354d809980c1c89a4bee1f75)

| 업무 | 스킬 |
| --- | --- |
| 무가 시딩 후보·컨택 | [teamdriven-seeding](skills/teamdriven-seeding) |
| 국내 메가셀러 마케팅허브 컨택 | [mega-seller-dm](skills/mega-seller-dm) |
| 일본 메가셀러 컨택 초안 | [japan-mega-seller-contact](skills/japan-mega-seller-contact) |
| 무가 시딩 CS 초안·상태 판단 | [teamdriven-cs](skills/teamdriven-cs) |

## 설치

- **Codex:** 필요한 GitHub 스킬 폴더 링크를 주고 `$skill-installer`로 설치 요청. 수동 설치는 업무 폴더의 `.agents/skills/스킬명/`에 폴더 전체를 넣는다.
- **Claude Code:** 업무 폴더의 `.claude/skills/스킬명/`에 폴더 전체를 넣는다. `/스킬명`으로 호출한다.
- **Claude 웹·앱:** [downloads](downloads)의 스킬별 ZIP을 다운로드하고 `Customize → Skills → + → Create skill → Upload a skill`에서 업로드·활성화한다. 코드 실행·파일 생성 기능이 필요하다.

ZIP에는 스킬 폴더 하나와 그 안의 `SKILL.md`·참고 파일이 들어 있다. 전체 저장소 ZIP을 Claude 스킬 업로드에 넣지 않는다.

## 첫 실행

```text
설치한 [스킬명]을 읽고 내 환경을 점검해줘.
담당자명과 업무 계정은 내게 확인하고 과거 기본값을 사용하지 마.
Notion 기준·기존 이력·가이드 원문과 실제 사용 가능한 도구를 확인해줘.
지금은 제공한 자료로 초안만 만들고 메시지 발송·DB 수정·출고는 하지 마.
가능한 작업과 추가 연결이 필요한 작업을 나눠 알려줘.
```

Notion·Instagram·Meta 권한은 각자의 계정으로 연결한다. 설치는 계정 로그인·브라우저 제어·정기 감시·자동 발송을 설정하지 않는다. 국내 메가셀러의 마케팅허브 실행에는 스킬에 지정된 Aside 연결도 필요하다. 연결이 없으면 초안을 복사해 사람이 실행할 수 있다.

## 업데이트

원본과 설치본은 자동 동기화되지 않는다. 해당 GitHub 스킬과 설치본을 비교해 `.local/`·개인 설정·실행 기록을 보존하며 갱신한다. Claude 업로드 ZIP도 변경된 버전을 다시 업로드해야 한다.

## 적용 범위

공유된 문구·기준은 위시어 업무용이다. 담당자·캠페인 기준·최신 승인 가이드를 확인하고 사용한다. CS 스킬은 일반 고객 상담 전반이나 자동 발송 엔진을 포함하지 않는다. 고객 명단·주소·대화·토큰은 저장소에 올리지 않는다.
