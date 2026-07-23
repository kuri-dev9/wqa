# WQA (Web QA)

WQA는 사용자가 Chromium을 직접 조작하는 동안 발생하는 Fetch/XHR 응답을
실시간 수집하고, JSON 응답에서 개인정보 또는 보안정보 노출 후보를 찾는
Windows용 QA 도구입니다.

현재 버전에는 STEP 1~4의 수집·파싱·검출 기능과 함께 GUI, 마스킹 보호,
메모리 제한, Excel 내보내기, Screenshot, Rule Engine 및 QA Mode가 구현되어
있습니다.

## 개발 환경

- Windows 11
- Python 3.13.9
- Playwright
- PySide6
- openpyxl
- orjson

## 설치

PowerShell에서 다음 명령을 실행합니다.

```powershell
cd D:\mobigen\51.source\92.local\wqa
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

Python 버전 확인:

```powershell
python --version
# Python 3.13.9
```

## 실행

GUI 실행:

```powershell
python main.py
```

기본 시작 페이지를 GUI의 URL 입력란에 입력한 뒤 `Start`를 누릅니다. 열린
Chromium에서 직접 로그인하고 평소처럼 사이트를 사용하면 됩니다.

기존 Console 모드도 사용할 수 있습니다.

```powershell
python main.py --cli --url "https://example.com"
python main.py --headless --url "https://example.com"
```

## GUI

상단 도구 모음:

- `Start`: Chromium을 별도 작업 스레드에서 시작
- `Stop`: 수집 중단 및 브라우저 종료
- `Export Excel`: 현재 검출 결과를 `.xlsx`로 저장
- `Clear`: GUI에 표시된 API와 검출 결과 초기화
- `Mode`: Privacy 또는 Security 검사 선택
- `Include masked`: 이미 마스킹된 값도 목록과 Excel에 포함
- `Password candidate`: 기본 비활성화된 Password 후보 검사 활성화

왼쪽 위 API 목록에는 Method, Status, URL, Elapsed, Detected Count가 표시되고,
왼쪽 아래에는 Timestamp, Type, Masked, API, Field Path가 표시됩니다.

API를 선택하면 오른쪽에서 다음 상세 정보를 확인할 수 있습니다.

- `Request`: Request Header
- `Response (JSON)`: 재귀 Tree View. 1MB 초과 본문은 `Skipped` 표시
- `Detected`: 해당 API의 검출 유형, 마스킹 상태, 보호된 표시값, Field Path

하단 Status Bar에는 총 API 수와 검출 건수가 표시됩니다.

## 출력 보호와 마스킹

원문 검출값은 분석 중 메모리에서만 사용합니다. Console, GUI, Excel에는
자동 보호된 `Displayed Value`만 출력합니다.

예:

- `qa@example.com` → `qa***@example.com`
- `010-1234-5678` → `010-****-5678`
- 주민등록번호, 토큰, API Key, Session ID도 유형별 보호 형식 적용

기본 목록과 Excel에는 `Masked=False`, 즉 응답에서 마스킹되지 않은 검출만
포함합니다. `Include masked`를 선택하면 마스킹된 후보도 포함할 수 있습니다.

`ab***@gmail.com`, `010****1234`처럼 이미 부분 마스킹되어 완전한 형식을
충족하지 않는 값은 Email 또는 Phone 확정 검출로 분류하지 않습니다.

## QA Mode

### Privacy Mode

- Email
- Phone / Mobile Phone
- Resident Number
- Business Number
- Name Candidate
- User ID Candidate

### Security Mode

- JWT
- Access Token
- API Key
- Password Candidate
- IP Address
- Session ID

`USER_ID_CANDIDATE`, `PASSWORD_CANDIDATE`, `NAME_CANDIDATE`는 값 패턴만으로
개인정보임을 확정할 수 없는 휴리스틱 결과입니다. `server01`, `router001`,
`version2026` 등은 User ID 확정값이 아니라 Candidate로만 취급됩니다.

## Rule Engine

[rules/rules.json](rules/rules.json)에서 Detector 활성 여부와 Report 표시 여부,
Mode별 검사 유형을 관리합니다.

```json
{
  "type": "PASSWORD_CANDIDATE",
  "enabled": false,
  "show_in_report": false
}
```

- `enabled`: Detector 결과 사용 여부
- `show_in_report`: GUI/Console/Excel 기본 출력 여부
- `modes.PRIVACY`, `modes.SECURITY`: Mode별 Detector 목록

규칙 파일을 변경하면 Detector 코드를 수정하지 않고 활성 유형을 조정할 수
있습니다. GUI의 `Password candidate` 체크는 실행 중 해당 규칙을 임시로
활성화합니다.

## 메모리 제한

[models/settings.py](models/settings.py)의 기본 설정:

- `max_api_records = 1000`: 초과 시 가장 오래된 API부터 FIFO 제거
- `max_response_body_bytes = 1MB`: 초과 본문은 저장·파싱하지 않고 `Skipped`
- `include_masked = False`

## Excel 및 Screenshot

Excel 컬럼:

Timestamp, Method, Status, API, Field Path, Detected Type, Masked,
Displayed Value, Elapsed Time, Response Size, Screenshot

최초 표시 대상 개인정보가 검출되면 현재 페이지를 `capture/yyyyMMdd_HHmmss.png`
형식으로 한 번 캡처하고 Excel의 Screenshot 컬럼에 기록합니다.

## 테스트

```powershell
pip install pytest
python -m pytest -q
```

Detector와 Parser는 Playwright 및 GUI와 독립적으로 테스트할 수 있습니다.
False Positive, Candidate 등급, 마스킹 이메일/전화번호, FIFO 저장 제한,
Rule/Mode 및 Excel 원문 미출력을 검증합니다.

## 구조

```text
wqa/
├── browser/       Playwright 수집
├── detector/      독립 Detector
├── parser/        JSON leaf parser
├── models/        API, Finding, 설정 모델
├── services/      분석, Rule, Excel, Screenshot, API 저장
├── ui/            PySide6 GUI 및 Browser worker
├── rules/         JSON Rule Engine 설정
├── capture/       Screenshot
├── output/excel/  Excel 결과
└── tests/         단위 테스트
```
