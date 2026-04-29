# Memory Scanner SOP

## 1. 빠른 시작
메모리 패턴 검색 도구. Hex (CE 스타일) 와 문자열 매칭을 지원하며, 특히 LLM 모드를 제공해 대모델이 메모리 컨텍스트를 분석하기 쉽게 합니다.

**Python 호출 방식:**
```python
import sys
sys.path.append('../memory') # 도구 디렉터리를 직접 마운트
from procmem_scanner import scan_memory

# 예: 특정 Hex 패턴 검색, llm_mode 활성화하여 컨텍스트 획득
results = scan_memory(pid, "48 8b ?? ?? 00", mode="hex", llm_mode=True)
```

**CLI:**
```powershell
# 기본 검색
python ../memory/procmem_scanner.py <PID> "pattern" --mode string

# LLM 강화 모드 (컨텍스트 포함 JSON 출력, 권장)
python ../memory/procmem_scanner.py <PID> "pattern" --llm
```

## 2. 전형적 시나리오: 구조체 또는 핵심 데이터 위치 찾기
1. 대상 데이터의 선행 패턴 또는 알려진 상수 (예: 특정 Header 또는 Magic Number) 확정
2. 대상 프로세스에서 해당 패턴 검색:
   `scan_memory(pid, "4D 5A 90 00", mode="hex", llm_mode=True)`
3. 반환된 JSON 의 `context` 필드 분석, 대상 주소 전후의 원시 바이트와 ASCII 미리보기 확인

## 3. 주의사항
- **권한**: 관리자 권한이 강제는 아니나 대상 프로세스의 `PROCESS_QUERY_INFORMATION` 과 `PROCESS_VM_READ` 권한이 필요
- **효율**: 큰 메모리 블록을 검색할 때는 가능한 한 더 고유한 패턴을 제공해 오탐 감소

## 4. CE 식 차집합 스캔으로 동적 필드 위치 찾기
WeChat 등 자체 그리는 UI 에서 조작에 따라 변하는 메모리 필드 (예: 현재 대화 제목) 위치 찾기. 핵심: 1회 전체 scan + 다회 ReadProcessMemory 필터링.
