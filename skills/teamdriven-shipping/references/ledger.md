# 로컬 접수 원장과 시트 대조

사용자의 작업 폴더에서 기존 원장·최종 전달 이력을 우선 사용한다. 아래 구조는 새 원장을 만들거나 기존 데이터를 대조 도구에 넘길 때 쓰는 형식이다. 운영 원장은 GitHub에 올리지 않는다.

`scripts/build_manifest.py`는 원장을 읽어 특정 날짜의 유효 출고 행을 JSON으로 만든다. 원장·DB·Excel을 수정하지 않는다. 의심 중복을 발견하면 출력 대신 실패해 확인을 요구한다.

```json
{
  "holidays": [],
  "records": [
    {
      "id": "request-demo-1",
      "received_at": "2030-01-02T10:00:00+09:00",
      "status": "pending",
      "recipient_name": "예시 수령자",
      "phone": "TEST-A",
      "address": "테스트 도시 테스트로 1",
      "products": [
        {"id": "line-1", "name": "버터쿠키 박스", "quantity": 1, "unit": "box", "option": "", "memo": ""}
      ]
    }
  ],
  "deliveries": []
}
```

위 예시 전화번호는 합성 표기로 실제 입력 검증에 통과하지 않는다. 실데이터의 `phone`은 앞자리 0을 가진 국내 전화번호 문자열이다.

## 필드와 이력

- `id`: 출고 요청의 고유 ID. 단순 동명이인이나 상품명으로 만들지 않는다. 여러 채팅·파일에서 같은 원본 요청을 다시 입력할 때 기존 ID를 재사용한다.
- `received_at`: 시간대가 포함된 접수 시각. 비교는 Asia/Seoul이다. `ship_date`를 명시하면 사용자 확정 출고일이 우선한다.
- `status`: `pending`, `cancelled`, `shipped`. 주소 확인 같은 업무 상태는 `memo`로 남기고 접수에서 제외하지 않는다. `shipped`는 사용자 확인 또는 확정된 이전 최종 전달 시트 근거가 있을 때만 쓴다.
- `products[].id`: 요청 내부의 고유 상품 행 ID. 수량 변경은 기존 행 값을 수정한다. 상품 추가는 새 행 ID를 추가한다. 원문·변경 근거는 기존 원장의 이력 필드에 보존한다.
- `products[].unit`: `box` 또는 `single`. `flavor`는 낱개 맛을 구분할 때 쓴다. `order_number`, `option`, `memo`는 선택 필드다.
- `recipient_group`: 사용자 확인으로 같은 배송지임이 확정된 경우에만 같은 수령자를 묶는 명시적 키다. 다른 실주소에 같은 키를 붙이지 않는다. 출력 주소는 수정하지 않는다.
- `deliveries[]`: `date`, `handed_off`, `record_ids`를 기록한다. 같은 날 최종 수정본은 기존 항목을 대체해 실제 마지막 전달본의 ID만 남긴다. 중간 초안의 행을 모두 누적하지 않는다.

예: `{"date":"2030-01-02","handed_off":true,"record_ids":["request-demo-1"]}`. 대상 출고일보다 앞선 날짜에 전달한 최종본의 요청만 완료 근거가 된다. 오늘 전달한 시트는 오늘 추가·변경 시 그대로 유지한다. 이미 발송된 요청에 대한 새 배송은 새로운 요청 ID로 접수한다.

## 실행

```bash
python scripts/build_manifest.py --ledger /private/work/ledger.json --date 2030-01-03 --out /private/work/manifest.json
```

환경에 지정된 Python 런타임이 있으면 그 실행 파일을 사용한다. 출력 `headers`, `rows`, `counts`, `provenance`, `included_record_ids`를 Excel 작성 단계의 입력·검증 근거로 사용한다. 수령자 수가 맞더라도 상품별 수량과 기존 행 보존은 별도로 확인한다.

휴일 목록은 검증된 회사 영업일 달력의 날짜만 넣는다. 스크립트는 주말을 건너뛰지만 공휴일을 추정하지 않는다. 지정 날짜가 휴무일인데 사용자가 출고일을 명시했다면 자동으로 바꾸지 않는다.
