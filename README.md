# WQA (Web QA)

WQA는 Chromium을 직접 조작하는 동안 발생하는 Fetch/XHR 응답을 수집하고,
JSON 응답에서 개인정보와 보안정보 노출 후보를 찾는 Windows용 QA 도구입니다.
검출 원문은 메모리 내부에서만 사용하며 Console, GUI, Excel, CSV, Log에는
보호된 값만 출력합니다.

## 환경

- Windows 11
- Python 3.13.9
- Playwright, PySide6, openpyxl, orjson

## 설치

```powershell
cd D:\mobigen\51.source\92.local\wqa
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

## 실행

GUI:

```powershell
python main.py
```

Console:

```powershell
python main.py --cli --url "https://example.com"
python main.py --headless --url "https://example.com"
```

GUI에서 URL을 입력하고 `Start`를 누르면 Chromium이 실행된 뒤 해당 URL로
자동 이동합니다. 스킴을 생략하면 `https://`를 자동 적용합니다. 마지막 URL은
`config.user.json`에 저장되어 다음 실행 시 자동 표시됩니다.

## GUI

상단:

- `Start`, `Stop`: Browser 수집 시작/중단
- `Export Excel`, `Export CSV`: 결과 내보내기
- `Clear`: 수집 결과 초기화
- `Mode`: Privacy 또는 Security 분석 모드
- `Include masked`: 이미 마스킹된 결과 포함
- `Password candidate`: 기본 비활성 Password 후보 활성화
- URL 입력

상태 표시줄은 `Idle`, `Running`, `Stopped` 상태와 총 API/검출 건수를
표시합니다. Running 중에는 Start가 비활성화되고 Stop이 활성화됩니다.

### API Filter와 검색

Filter:

- `All`: 모든 API
- `Privacy`: Privacy 유형이 검출된 API
- `Security`: Security 유형이 검출된 API
- `Current Page`: 가장 최근 페이지에서 발생한 API
- `Only Unmasked`: 미마스킹 검출이 있는 API

Search Box는 보호된 API URL, Field Path, Displayed Value를 통합 검색합니다.

### API Detail

API를 선택하면 오른쪽 패널에서 다음 정보를 확인할 수 있습니다.

- `Request`: Request Header
- `Response (JSON)`: 재귀 JSON Tree
- `Detected`: 검출 유형, 마스킹 상태, 보호된 값, Field Path

아래 개인정보 목록에서 검출 결과를 선택하면 해당 API가 선택되고 Response
Tree의 Field Path로 자동 이동하여 노란색으로 Highlight합니다.

## Settings

메뉴의 `Settings > Settings`에서 다음 항목을 변경하고 저장할 수 있습니다.

- Ignore HTTPS Errors
- Headless Browser
- Response Size Limit
- Max API Records
- Privacy Mode 활성 여부
- Security Mode 활성 여부

기본값은 [config.json](config.json)에 있으며 사용자 변경값과 최근 URL은
Git에서 제외되는 `config.user.json`에 저장됩니다.

```json
{
  "browser": {
    "headless": false,
    "ignore_https_errors": true,
    "viewport_width": 1600,
    "viewport_height": 900
  },
  "capture": {
    "response_max_size_mb": 1,
    "max_api_records": 1000
  }
}
```

`ignore_https_errors` 기본값은 `true`이므로 사내 Self-Signed Certificate
사이트도 접속할 수 있습니다. Response Body 기본 제한은 1MB이며 초과 본문은
저장·분석하지 않고 `Skipped`로 표시합니다. API는 기본 1,000건을 FIFO로
보관합니다.

## 오류 안내

Browser 시작 및 이동 오류를 다음과 같이 구분해 안내합니다.

- DNS lookup 실패
- HTTPS 인증서 오류
- Connection refused
- Timeout
- HTTP 404
- HTTP 500

## QA Mode와 Rule Engine

Privacy Mode:

- Email
- Phone / Mobile Phone
- Resident Number
- Business Number
- Name Candidate
- User ID Candidate

Security Mode:

- JWT
- Access Token
- API Key
- Password Candidate
- IP Address
- Session ID

[rules/rules.json](rules/rules.json)의 `enabled`, `show_in_report`,
`modes.PRIVACY`, `modes.SECURITY`로 Detector 활성 여부와 출력 여부를
관리합니다. `USER_ID_CANDIDATE`, `PASSWORD_CANDIDATE`,
`NAME_CANDIDATE`는 확정 개인정보가 아닌 휴리스틱 후보입니다.

## 출력 보호

예:

- `qa@example.com` → `qa***@example.com`
- `010-1234-5678` → `010-****-5678`
- Token/API Key/Session ID → 앞뒤 일부만 표시

기본 GUI와 Export에는 미마스킹 노출만 포함합니다. Request/Response Tree,
API URL, Excel Summary에도 동일한 출력 보호를 적용합니다.

## Excel 및 CSV

Excel:

- `Summary`: 총 API, Privacy/Security 검출 수, 전체 Response Size,
  평균 Elapsed, API별 검출 건수
- `Detail`: Timestamp, Method, Status, API, Field Path, Detected Type,
  Masked, Displayed Value, Elapsed Time, Response Size, Screenshot

CSV는 대용량 처리용 Detail 형식이며 UTF-8 BOM으로 저장됩니다.

최초 표시 대상 개인정보가 검출되면 현재 페이지를
`capture/yyyyMMdd_HHmmss.png`로 한 번 저장하고 Export 결과에 경로를
기록합니다.

## Log와 About

실행 로그는 `logs/yyyyMMdd.log`에 저장됩니다. 개인정보 검출 원문은 기록하지
않습니다. `Help > About`에서 WQA Version, Python Version, Playwright
Version을 확인할 수 있습니다.

## 테스트

```powershell
pip install pytest
python -m pytest -q
```

Detector False Positive, 마스킹, FIFO, HTTPS Ignore, 설정 Load/Save,
CSV 원문 보호, Excel Summary 등을 검증합니다.

## 구조

```text
wqa/
├── browser/       Playwright 및 Browser 오류 분류
├── detector/      독립 Detector
├── parser/        JSON leaf parser
├── models/        API, Finding, 설정 모델
├── services/      Config, Rule, Excel, CSV, Log, Screenshot, API 저장
├── ui/            PySide6 GUI, Settings Dialog, Browser worker
├── rules/         JSON Rule Engine 설정
├── capture/       Screenshot
├── logs/          일별 안전 로그
├── output/        Excel/CSV 결과
└── tests/         단위 테스트
```
