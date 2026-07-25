# 기여 가이드

StopCord에 관심 가져주셔서 감사합니다.

## 개발 환경 설정

```bash
git clone https://github.com/YJASTUDIO/stopcord.git
cd stopcord
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## 테스트 실행

```bash
pytest tests/ -v          # 정식 테스트 (13개 케이스)
python tests/smoke_test.py # 스모크 테스트
```

PR을 보내기 전에 반드시 두 테스트가 통과해야 합니다.

## 코드 스타일

- Python 3.10+ 지원
- 타입 힌트 사용 권장
- 함수/클래스에 docstring 작성
- 커밋 메시지는 conventional commits 형식 (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)

## 구조

```
src/stopcord/
├── __init__.py      # 공개 API
├── guard.py         # 킬스위치
├── approvals.py     # 승인 대기열
├── deadman.py       # 데드맨스위치
├── budget.py        # 예산 추적
├── cli.py           # CLI 인터페이스
└── mcp_server.py    # MCP 서버 (AI 에이전트용)
```

## 새 모듈 추가 시

1. `src/stopcord/<module>.py`에 구현
2. `src/stopcord/__init__.py`에서 export
3. `tests/test_stopcord.py`에 테스트 추가
4. MCP 노출이 필요하면 `mcp_server.py`의 `list_tools`와 `call_tool`에 등록
5. CLI 지원이 필요하면 `cli.py`에 서브명령 추가
6. README의 표/아키텍처 업데이트

## 이슈 보고

- 버그: 재현 단계, 기대 동작, 실제 동작을 포함해주세요
- 기능 제안: 사용 사례와 함께 설명해주세요

## 라이선스

기여물은 MIT 라이선스에 따라 배포됩니다.