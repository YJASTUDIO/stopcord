"""빠른 스모크 테스트 — 실제로 4개 모듈이 정상 동작하는지 확인."""
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from stopcord import Guard, ApprovalQueue, DeadmanSwitch, BudgetTracker

tmp = Path(tempfile.mkdtemp())
print(f"[state_dir] {tmp}")

# 1. Guard
g = Guard(state_dir=tmp)
assert g.status() == "정상 운영중"
assert g.needs_approval("결제수단 연결해줘") is True
assert g.needs_approval("리서치 요약해줘") is False
print("[Guard] needs_approval 판정 OK, status:", g.status())

# 2. ApprovalQueue
aq = ApprovalQueue(state_dir=tmp)
eid = aq.request("결제수단 연결", category="payment")
pending = aq.list_pending()
assert len(pending) == 1 and pending[0]["id"] == eid
resolved = aq.resolve(eid, approved=True, note="회장 승인")
assert resolved is True
assert len(aq.list_pending()) == 0
print("[ApprovalQueue] 등록->조회->해결 OK")

# 3. DeadmanSwitch
ds = DeadmanSwitch(guard=g, warn_hours=24, kill_hours=36)
r_none = ds.check(datetime.now(timezone.utc) - timedelta(hours=1))
assert r_none.action == "none"
r_warn = ds.check(datetime.now(timezone.utc) - timedelta(hours=25))
assert r_warn.action == "warn"
r_kill = ds.check(datetime.now(timezone.utc) - timedelta(hours=40))
assert r_kill.action == "killed"
assert g.is_killed() is True
print("[DeadmanSwitch] none->warn->killed 3단계 전이 OK, guard killed:", g.is_killed())

# 4. BudgetTracker
bt = BudgetTracker(hardcap=300000, daily_warn=15000, state_dir=tmp)
status1 = bt.log_spend("도메인 등록", 12000)
assert status1["over_hardcap"] is False
status2 = bt.log_spend("서버비", 290000)
assert status2["over_hardcap"] is True
print("[BudgetTracker] 하드캡 초과 감지 OK:", status2)

shutil.rmtree(tmp)
print("\n=== 전체 스모크 테스트 통과 ===")
