# 자율 행동 SOP

⚠️ **경로 주의**: autonomous_reports 는 temp/ 아래에 있으므로 `./autonomous_reports/` 로 접근합니다. **절대** `../memory/autonomous_reports/` 나 `../autonomous_reports/` 가 아닙니다! TODO 는 cwd 아래에 있습니다.
보고서는 `./autonomous_reports/` 에 저장하며, 파일명은 `RXX_간단한설명.md` 형식입니다 (XX는 history.txt 로부터 추론하여 자동 증가).

자율 행동을 허가합니다. 환경에 부작용을 주지 않는 한 자유롭게 진행해도 됩니다.

## 시작 (1단계)
- update_working_checkpoint: `자율행동｜마무리 시 SOP 재독 | from autonomous_operation_sop.helper import *; set_todo()/complete_task(tasktitle, historyline, report_path)`

2단계:
```python
from autonomous_operation_sop.helper import *
print(get_history(40))  # 이력 파악, 중복 회피
print(get_todo())       # 할 일 확인
```

## 작업 선택
- 미완료 항목이 있으면 → **하나만** 골라 바로 실행, 나머지는 다음 회차로
- TODO 가 없으면 → `autonomous_operation_sop/task_planning.md` 를 읽고 계획만 짠 뒤 다음 회차에 실행
- 같은 하위 작업을 두 번 연속 선택하지 않습니다
- 가치 공식: **「AI 학습 데이터로 커버되지 않는 것」 × 「향후 협업에 지속적으로 도움이 되는 것」**

## 실행
- 작업을 선정한 뒤 update_working_checkpoint 로 선택된 TODO 항목과 실행 시 주의점을 checkpoint 에 append 합니다
- code_run 으로 마무리 콜백을 준비합니다. script 는 handler._done_hooks.append("자율 작업 sop를 다시 읽고 방금의 마무리 작업이 올바른지 점검, 잘못됐으면 수정"), inline_eval=True (비공개 인자)
- 라운드 30회 이내, 작은 단위로 빠르게, 탐색하면서 실험합니다
- 임시 스크립트로 가설을 검증합니다. 읽기만 하고 결론 내지 말고, 완전히 검증한 뒤 보고서를 작성합니다
- 실패하더라도 실험 과정과 결과를 기록합니다. 실패 보고서도 가치가 있습니다
- 사용자가 오프라인이므로 결정이 필요한 문제는 보고서에 기록해 검토를 기다리되, 멈추지 마세요

**마무리 (4가지 모두 필수)**:
0. 본 sop 를 다시 읽기
1. cwd 에 보고서 작성 (파일명 자유). 메모리 갱신 제안이 있으면 보고서 끝에 첨부
2. `from/import helper; complete_task(tasktitle, historyline, report_path)` → 자동으로 번호 매기고 보고서를 autonomous_reports/ 로 이동, history 에 prepend (historyline 형식: `유형 | 주제 | 결론`, 엄격히 한 줄)
3. `set_todo()` 로 TODO 경로 획득 → 완료 항목을 `[x]` 로 표시
4. 종료. 남은 TODO 는 다음 회차에 처리

## 권한 경계
- 승인 불필요: 읽기 전용 탐색, cwd 내 쓰기/스크립트 실험
- 보고서로 검토 요청 필요: global_mem / memory 아래 SOP 수정, 소프트웨어 설치, 외부 API 호출, 비임시 파일 삭제
- 절대 금지: 비밀키 읽기, 핵심 코드베이스 수정, 비가역적 위험 작업

## 사용자 검토 대기
- 사용자가 돌아온 뒤 보고서를 검토하여 승인/수정/거부를 결정합니다
