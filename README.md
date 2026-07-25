# stopcord

> 당기면 즉시 멈춘다 — AI 에이전트(Claude, GPT 등)를 자율 운영에 실제로 맡기는 1인 창업자를 위한 오픈소스 안전장치 툴킷.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-13%20passing-green.svg)](tests/)

## 왜 만들었나

1인 창업자가 AI 에이전트에게 회사 운영(결제, 배포, SNS 발행 등)을 맡기다 보면
"이 작업이 되돌릴 수 없는 것인가?", "내가 24시간 응답이 없으면 자동으로 멈출 것인가?",
"이번 달 예산 한도를 넘으면 어떻게 되는가?" 같은 안전장치가 반드시 필요합니다.

다들 이걸 각자 즉석으로 짜고 있어서, 표준화된 작은 오픈소스 라이브러리로 만들었습니다.
이 저장소의 로직은 실제 AI 자동화 마이크로 SaaS 스튜디오 운영에 매일 쓰이고 있습니다(dogfooding).

이름은 산업 현장의 비상정지 코드(pull cord)에서 따왔습니다 — 문제가 생기면 당겨서 즉시 멈춘다는 뜻입니다.

## 핵심 기능 (4개 모듈)

| 모듈 | 기능 | 언제 쓰는가 |
|---|---|---|
| `Guard` | 킬스위치(즉시 중단/재개), 되돌릴 수 없는 작업 키워드 감지 | 에이전트가 위험한 작업을 시도할 때 |
| `ApprovalQueue` | 고비용/비가역 작업을 사람이 승인하기 전까지 큐에 등록 | 결제·발행·채용 등 되돌릴 수 없는 작업 전 |
| `DeadmanSwitch` | 사람 무응답 N시간 시 경고 → 자동 킬스위치 활성화 | 창업자가 휴가/수면/장기 부재 중일 때 |
| `BudgetTracker` | 월/일 지출 한도 추적, 하드캡 초과 감지 | 에이전트가 자율로 비용을 발생시킬 때 |

## 빠른 시작

### 설치

```bash
pip install stopcord
# 또는 개발 모드
git clone https://github.com/YJASTUDIO/stopcord.git
cd stopcord
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Python 라이브러리로 사용

```python
from stopcord import Guard, ApprovalQueue, DeadmanSwitch, BudgetTracker

# 1. 킬스위치 — 되돌릴 수 없는 작업 감지
guard = Guard()
if guard.needs_approval("결제수단 연결해줘"):
    print("⚠️ 사람 승인이 필요합니다")

# 2. 승인 대기열 — 비가역 작업을 큐에 쌓기
queue = ApprovalQueue()
req_id = queue.request("Postiz 콘텐츠 발행", category="publish")
print(f"승인 대기 중: {queue.list_pending()}")
# 사람이 승인하면:
queue.resolve(req_id, approved=True, note="회장 승인")

# 3. 데드맨스위치 — 무응답 시 자동 정지
from datetime import datetime, timezone, timedelta
deadman = DeadmanSwitch(guard=guard, warn_hours=24, kill_hours=36)
result = deadman.check(datetime.now(timezone.utc) - timedelta(hours=25))
print(result.action)  # "warn"

# 4. 예산 추적 — 하드캡 초과 감지
budget = BudgetTracker(hardcap=300000, daily_warn=15000)
budget.log_spend("도메인 등록", 12000)
print(budget.status())  # {"total_spent_this_month": 12000, "over_hardcap": False, ...}
```

### CLI로 바로 쓰기

```bash
# 킬스위치
stopcord status                          # 현재 상태
stopcord kill --reason "긴급 점검"        # 즉시 중단
stopcord resume                          # 재개

# 승인 대기열
stopcord approvals list                           # 대기 중 목록
stopcord approvals request "결제수단 연결" --category payment
stopcord approvals resolve <id> --approved true --note "승인"

# 데드맨스위치
stopcord deadman check 2026-07-25T10:00:00+09:00
stopcord deadman check 2026-07-25T10:00:00+09:00 --warn-hours 2 --kill-hours 4

# 예산
stopcord budget status                   # 현재 예산 상태
stopcord budget log "도메인 등록" 12000   # 지출 기록
```

## MCP 서버 (AI 에이전트가 직접 호출)

Claude, GPT 등 MCP를 지원하는 AI 에이전트가 이 도구들을 tool call로 직접 사용할 수 있습니다.

```bash
pip install -e .
python -m stopcord.mcp_server
# 또는
stopcord-mcp
```

노출되는 9개 도구:

| 도구 | 설명 |
|---|---|
| `guard_status` | 킬스위치 현재 상태 |
| `guard_activate_kill` | 킬스위치 활성화(즉시 중단) |
| `guard_deactivate_kill` | 킬스위치 해제(재개) |
| `approval_request` | 승인 요청 등록 |
| `approval_list_pending` | 대기 중 승인 목록 |
| `approval_resolve` | 승인/거부 처리 |
| `deadman_check` | 데드맨스위치 상태 판정 |
| `budget_status` | 예산 현황 |
| `budget_log_spend` | 지출 기록 |

### Claude Desktop에서 연결하기

`claude_desktop_config.json`에 추가:

```json
{
  "mcpServers": {
    "stopcord": {
      "command": "stopcord-mcp",
      "env": {
        "STOPCORD_STATE_DIR": "~/.stopcord"
      }
    }
  }
}
```

## 환경변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `STOPCORD_STATE_DIR` | `~/.stopcord` | 상태 파일(killswitch, approvals.json, budget.json) 저장 경로 |

## 상태 파일

모든 상태는 `STOPCORD_STATE_DIR` 아래 JSON/마커 파일로 저장됩니다:

```
~/.stopcord/
├── .killswitch        # 존재 시 킬스위치 활성 상태
├── approvals.json     # 승인 대기열 (pending + resolved)
└── budget.json        # 예산 추적 (월 누적, 항목별 기록)
```

## 아키텍처

```
┌─────────────────────────────────────────────┐
│              AI 에이전트 (Claude/GPT)         │
│                    │ MCP                     │
│                    ▼                         │
│         ┌─────────────────────┐              │
│         │   stopcord MCP 서버  │              │
│         │  (9개 tool call 노출) │              │
│         └────────┬────────────┘              │
│                  │                           │
│    ┌──────┬──────┼──────┬──────┐              │
│    ▼      ▼      ▼      ▼      ▼              │
│  Guard  Approvals Deadman Budget             │
│                                              │
│  ──────── 로컬 파일 상태 ────────             │
│  ~/.stopcord/                                │
│    .killswitch  approvals.json  budget.json  │
└─────────────────────────────────────────────┘
```

의존성이 파일 기반이라 DB나 외부 서비스 없이도 동작합니다.
상태 디렉토리를 바꾸면 인스턴스를 여러 개 띄울 수 있습니다.

## 개발/테스트

```bash
git clone https://github.com/YJASTUDIO/stopcord.git
cd stopcord
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
pytest tests/          # 13개 케이스
python tests/smoke_test.py  # 스모크 테스트
```

## 기여

버그 리포트, 기능 제안, PR 모두 환영합니다. [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.

## 로드맵

- [x] v0.1.0 — 4개 핵심 모듈 + MCP 서버 + CLI
- [ ] v0.2.0 — 승인 알림 (Slack/웹훅 연동)
- [ ] v0.3.0 — 예산 일일 리포트 자동 생성
- [ ] v0.4.0 — 상태 백엔드 옵션 (SQLite, Redis)
- [ ] v1.0.0 — 안정화 + 문서 완성

## 라이선스

MIT

---

이 프로젝트는 [빌드인퍼블릭](https://buildinpublic.com) 형식으로 진행상황을 공개합니다.