# stopcord

> 당기면 즉시 멈춘다 — AI 에이전트(Claude, GPT 등)를 자율 운영에 실제로 맡기는 1인 창업자를 위한 오픈소스 안전장치 툴킷.

## 왜 만들었나

1인 창업자가 AI 에이전트에게 회사 운영(결제, 배포, SNS 발행 등)을 맡기다 보면
"이 작업이 되돌릴 수 없는 것인가?", "내가 24시간 응답이 없으면 자동으로 멈출 것인가?",
"이번 달 예산 한도를 넘으면 어떻게 되는가?" 같은 안전장치가 반드시 필요합니다.

다들 이걸 각자 즉석으로 짜고 있어서, 표준화된 작은 오픈소스 라이브러리로 만들었습니다.
이 저장소의 로직은 실제 AI 자동화 마이크로 SaaS 스튜디오 운영에 매일 쓰이고 있습니다(dogfooding).

이름은 산업 현장의 비상정지 코드(pull cord)에서 따왔습니다 — 문제가 생기면 당겨서 즉시 멈춘다는 뜻입니다.

## 핵심 기능

| 모듈 | 기능 |
|---|---|
| `Guard` | 킬스위치(즉시 중단/재개), 되돌릴 수 없는 작업 키워드 감지 |
| `ApprovalQueue` | 고비용/비가역 작업을 사람이 승인하기 전까지 큐에 등록 |
| `DeadmanSwitch` | 사람 무응답 N시간 시 경고 → 자동 킬스위치 활성화 |
| `BudgetTracker` | 월/일 지출 한도 추적, 하드캡 초과 감지 |

## MCP 서버 (AI 에이전트가 직접 호출)

Claude, GPT 등 MCP를 지원하는 AI 에이전트가 이 도구들을 tool call로 직접 사용할 수 있습니다.

```bash
pip install -e .
python -m stopcord.mcp_server
```

노출되는 도구: `guard_status`, `guard_activate_kill`, `guard_deactivate_kill`,
`approval_request`, `approval_list_pending`, `budget_status`, `budget_log_spend`

## 설치 및 사용 (Python 라이브러리로)

```python
from stopcord import Guard, ApprovalQueue, DeadmanSwitch, BudgetTracker

guard = Guard()
if guard.needs_approval("결제수단 연결해줘"):
    print("사람 승인이 필요합니다")

queue = ApprovalQueue()
queue.request("Postiz 콘텐츠 발행", category="publish")
```

## 개발/테스트

```bash
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e .
python tests/smoke_test.py
```

## 라이선스

MIT

---

이 프로젝트는 빌드인퍼블릭 형식으로 진행상황을 공개합니다. 진행 로그와 배경 스토리는 곧 블로그/X에 공개될 예정입니다.
