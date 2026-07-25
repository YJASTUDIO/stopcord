"""pytest 기반 정식 테스트 — smoke_test.py의 assert들을 pytest 케이스로 재구성."""
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from stopcord import Guard, ApprovalQueue, DeadmanSwitch, BudgetTracker


@pytest.fixture
def state_dir():
    d = Path(tempfile.mkdtemp())
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_guard_status_default(state_dir):
    g = Guard(state_dir=state_dir)
    assert g.status() == "정상 운영중"
    assert g.is_killed() is False


def test_guard_kill_resume_cycle(state_dir):
    g = Guard(state_dir=state_dir)
    g.activate_kill(reason="test")
    assert g.is_killed() is True
    assert g.status() == "중단됨"
    g.deactivate_kill()
    assert g.is_killed() is False


@pytest.mark.parametrize("text,expected", [
    ("결제수단 연결해줘", True),
    ("payment method setup", True),
    ("리서치 요약해줘", False),
    ("문서 초안 작성", False),
])
def test_guard_needs_approval(state_dir, text, expected):
    g = Guard(state_dir=state_dir)
    assert g.needs_approval(text) is expected


def test_approval_queue_lifecycle(state_dir):
    aq = ApprovalQueue(state_dir=state_dir)
    eid = aq.request("결제수단 연결", category="payment")
    assert len(aq.list_pending()) == 1
    assert aq.resolve(eid, approved=True, note="승인") is True
    assert len(aq.list_pending()) == 0
    assert aq.resolve("no-such-id", approved=True) is False


def test_deadman_switch_transitions(state_dir):
    g = Guard(state_dir=state_dir)
    ds = DeadmanSwitch(guard=g, warn_hours=24, kill_hours=36)

    r = ds.check(datetime.now(timezone.utc) - timedelta(hours=1))
    assert r.action == "none"

    r = ds.check(datetime.now(timezone.utc) - timedelta(hours=25))
    assert r.action == "warn"
    assert g.is_killed() is False

    r = ds.check(datetime.now(timezone.utc) - timedelta(hours=40))
    assert r.action == "killed"
    assert g.is_killed() is True

    # 이미 킬된 상태에서 재확인하면 already_killed
    r = ds.check(datetime.now(timezone.utc) - timedelta(hours=50))
    assert r.action == "already_killed"


def test_budget_tracker_hardcap(state_dir):
    bt = BudgetTracker(hardcap=300000, daily_warn=15000, state_dir=state_dir)
    status1 = bt.log_spend("도메인 등록", 12000)
    assert status1["over_hardcap"] is False
    status2 = bt.log_spend("서버비", 290000)
    assert status2["over_hardcap"] is True
    assert status2["total_spent_this_month"] == 302000


def test_approval_resolve_approve(state_dir):
    aq = ApprovalQueue(state_dir=state_dir)
    eid = aq.request("도메인 구매", category="payment")
    ok = aq.resolve(eid, approved=True, note="회장 승인")
    assert ok is True
    assert len(aq.list_pending()) == 0
    data = aq._read()
    assert len(data["resolved"]) == 1
    assert data["resolved"][0]["approved"] is True


def test_approval_resolve_reject(state_dir):
    aq = ApprovalQueue(state_dir=state_dir)
    eid = aq.request("임의 결제", category="payment")
    ok = aq.resolve(eid, approved=False, note="회장 거부")
    assert ok is True
    data = aq._read()
    assert data["resolved"][0]["approved"] is False


def test_deadman_custom_thresholds(state_dir):
    g = Guard(state_dir=state_dir)
    ds = DeadmanSwitch(guard=g, warn_hours=2, kill_hours=4)
    r = ds.check(datetime.now(timezone.utc) - timedelta(hours=3))
    assert r.action == "warn"
    r = ds.check(datetime.now(timezone.utc) - timedelta(hours=5))
    assert r.action == "killed"
    assert g.is_killed() is True


def test_mcp_tool_count():
    """MCP 서버가 9개 도구를 노출하는지 확인 (기존 7 + approval_resolve + deadman_check)."""
    from stopcord.mcp_server import list_tools
    import asyncio
    tools = asyncio.run(list_tools())
    names = [t.name for t in tools]
    assert "approval_resolve" in names
    assert "deadman_check" in names
    assert len(tools) == 9
