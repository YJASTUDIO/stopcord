"""stopcord — AI 에이전트를 위한 오픈소스 안전장치 툴킷.

1인 창업자가 AI 에이전트(Claude, GPT 등)에게 실제 운영을 맡길 때 필요한
킬스위치·승인대기열·데드맨스위치·예산캡을 표준화한 작은 라이브러리.

이름의 유래: 산업안전 비상정지 코드(pull cord) — 당기면 즉시 멈춘다.
"""
from .guard import Guard
from .approvals import ApprovalQueue
from .deadman import DeadmanSwitch, DeadmanResult
from .budget import BudgetTracker

__all__ = [
    "Guard",
    "ApprovalQueue",
    "DeadmanSwitch",
    "DeadmanResult",
    "BudgetTracker",
]

__version__ = "0.1.0"
