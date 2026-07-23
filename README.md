# Web QA Tool (WQA)

사용자가 Chromium을 직접 조작하는 동안 발생하는 Fetch/XHR 응답을 수집하고,
JSON 응답의 모든 leaf value에서 개인정보·민감정보 패턴을 찾는 Windows용 도구입니다.

현재 구현 범위는 STEP 1~4입니다.

- Chromium 실행 및 직접 로그인/탐색
- Fetch/XHR의 Method, URL, Status, Body, Size, 응답 시간 수집
- API 기록 메모리 저장(JSON이 아닌 Body는 분석 생략)
- 중첩 JSON의 `data.users[0].email` 형식 field path 생성
- 필드명이 아닌 value만 이용한 독립 Detector 분석
- 이메일, 전화/휴대폰, 주민등록번호, 사업자번호, IP, JWT, Access Token,
  Password, Session ID, API Key, 일반 User ID 패턴

## 설치

Python 3.12 가상환경 사용을 권장합니다. PowerShell에서:

```powershell
cd D:\mobigen\51.source\92.local\wqa
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
```

STEP 1~4 실행에 필요한 최소 패키지만 설치하려면 다음 명령도 가능합니다.

```powershell
pip install playwright==1.55.0 orjson==3.11.3
playwright install chromium
```

## 실행

```powershell
python main.py
```

특정 페이지를 바로 열려면:

```powershell
python main.py --url "https://example.com"
```

열린 Chromium에서 직접 로그인하고 평소처럼 사이트를 사용합니다. Fetch/XHR
응답 요약과 검출 결과가 콘솔에 실시간 출력됩니다. 브라우저 창을 모두 닫거나
터미널에서 `Ctrl+C`를 누르면 종료됩니다.

## 테스트

```powershell
pip install pytest
python -m pytest
```

Detector는 브라우저/UI와 독립적이므로 문자열만 전달해 단위 테스트할 수 있습니다.

```python
from detector.email_detector import EmailDetector

matches = EmailDetector().detect("contact: qa@example.com")
```

## 구조와 확장 방향

- `browser/`: Playwright 수집만 담당
- `services/api_logger.py`: API 기록의 메모리 저장
- `parser/`: UI와 무관한 JSON leaf 파싱
- `detector/`: 공통 `Detector` 계약과 유형별 구현
- `services/analysis_service.py`: parser와 detector 조합
- `models/`: 계층 간 전달 모델
- `rules/rules.json`: STEP 10 Rule Engine을 위한 자리

새 코드 기반 Detector는 `Detector`를 구현하고 `DetectorRegistry`에 등록할 수
있습니다. JSON만으로 규칙을 추가하는 Rule Engine, 마스킹 판정, Excel, GUI,
Screenshot, DOM 비교는 각각 STEP 5~10에서 단계적으로 구현할 예정입니다.

Password와 User ID는 field 이름을 사용하지 않는 value-only 휴리스틱이므로 오탐
가능성이 있습니다. STEP 10에서 규칙별 활성화, 우선순위, 예외 목록을 설정할 수
있도록 확장하는 것이 권장됩니다.
