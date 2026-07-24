"""
deadman.py — 데드맨 스위치

사람(관리자)의 마지막 확인/응답 이후 경과 시간을 기준으로
경고 → 자동 킬스위치 활성화를 수행하는 모듈.
호출자가 "마지막 응답 시각"을 제공해야 한다(저장소/DB 접근은 이 패키지 책임 밖).
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from .guard import Guard


@dataclass
class DeadmanResult:
    elapsed_hours: float
    action: str  # "none" | "warn" | "killed" | "already_killed"
    message: str


class DeadmanSwitch:
    def __init__(self, guard: Optional[Guard] = None, warn_hours: float = 24, kill_hours: float = 36):
        self.guard = guard or Guard()
        self.warn_hours = warn_hours
        self.kill_hours = kill_hours

    def check(self, last_response_at: datetime) -> DeadmanResult:
        now = datetime.now(timezone.utc)
        if last_response_at.tzinfo is None:
            last_response_at = last_response_at.replace(tzinfo=timezone.utc)
        elapsed_hours = (now - last_response_at).total_seconds() / 3600.0

        if self.guard.is_killed():
            return DeadmanResult(elapsed_hours, "already_killed", "이미 킬스위치 활성 상태입니다.")

        if elapsed_hours >= self.kill_hours:
            self.guard.activate_kill(reason=f"데드맨스위치: {elapsed_hours:.1f}시간 무응답")
            return DeadmanResult(
                elapsed_hours, "killed",
                f"🚨 {elapsed_hours:.1f}시간 무응답으로 자동정지(킬스위치) 활성화."
            )
        elif elapsed_hours >= self.warn_hours:
            return DeadmanResult(
                elapsed_hours, "warn",
                f"⚠️ {elapsed_hours:.1f}시간 무응답. {self.kill_hours}시간 도달 시 자동정지됩니다."
            )
        return DeadmanResult(elapsed_hours, "none", "정상 범위.")
