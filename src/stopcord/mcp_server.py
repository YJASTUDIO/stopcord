"""
mcp_server.py — AI 에이전트(Claude/GPT 등)가 stdio MCP로 직접 호출하는 서버.

실행: python -m stopcord.mcp_server
"""
import asyncio
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .guard import Guard
from .approvals import ApprovalQueue
from .deadman import DeadmanSwitch
from .budget import BudgetTracker

guard = Guard()
approvals = ApprovalQueue()
budget = BudgetTracker(hardcap=300000, daily_warn=15000)
deadman = DeadmanSwitch(guard=guard)

server = Server("stopcord")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="guard_status",
            description="킬스위치 현재 상태를 확인한다.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="guard_activate_kill",
            description="킬스위치를 활성화해 모든 자동화를 즉시 중단한다.",
            inputSchema={
                "type": "object",
                "properties": {"reason": {"type": "string"}},
            },
        ),
        Tool(
            name="guard_deactivate_kill",
            description="킬스위치를 해제하고 정상 운영을 재개한다.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="approval_request",
            description="되돌릴 수 없거나 고비용인 작업에 대해 사람의 승인을 요청한다(대기열에 등록).",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["description"],
            },
        ),
        Tool(
            name="approval_list_pending",
            description="현재 승인 대기 중인 항목 목록을 반환한다.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="approval_resolve",
            description="승인 대기열의 항목을 승인하거나 거부한다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "approved": {"type": "boolean"},
                    "note": {"type": "string"},
                },
                "required": ["id", "approved"],
            },
        ),
        Tool(
            name="deadman_check",
            description="데드맨스위치를 확인한다. 사람의 마지막 응답 시각을 기준으로 경고/자동정지를 판정한다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "last_response_at": {"type": "string", "description": "ISO 8601 timestamp of last human response"},
                },
                "required": ["last_response_at"],
            },
        ),
        Tool(
            name="budget_status",
            description="이번 달 누적 지출과 하드캡 대비 상태를 반환한다.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="budget_log_spend",
            description="지출 항목을 기록하고 갱신된 예산 상태를 반환한다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "item": {"type": "string"},
                    "amount": {"type": "number"},
                },
                "required": ["item", "amount"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "guard_status":
        result = guard.status()
    elif name == "guard_activate_kill":
        result = guard.activate_kill(reason=arguments.get("reason", ""))
    elif name == "guard_deactivate_kill":
        result = guard.deactivate_kill()
    elif name == "approval_request":
        entry_id = approvals.request(
            description=arguments["description"],
            category=arguments.get("category", "기타"),
        )
        result = f"승인 요청 등록됨 (id={entry_id})"
    elif name == "approval_list_pending":
        result = str(approvals.list_pending())
    elif name == "approval_resolve":
        ok = approvals.resolve(
            entry_id=arguments["id"],
            approved=arguments["approved"],
            note=arguments.get("note", ""),
        )
        result = "승인 처리 완료" if ok else "해당 ID의 승인 항목을 찾을 수 없음"
    elif name == "deadman_check":
        from datetime import datetime as _dt
        last = _dt.fromisoformat(arguments["last_response_at"])
        dr = deadman.check(last)
        result = f"action={dr.action}, elapsed={dr.elapsed_hours:.1f}h, message={dr.message}"
    elif name == "budget_status":
        result = str(budget.status())
    elif name == "budget_log_spend":
        result = str(budget.log_spend(item=arguments["item"], amount=arguments["amount"]))
    else:
        result = f"알 수 없는 도구: {name}"

    return [TextContent(type="text", text=result)]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
