# Subagent 호출 SOP

## 파일 IO 프로토콜

- 디렉터리: `temp/{task_name}/` (cwd 가 temp/ 인 경우 `./{task_name}/`)
- 기동: `python agentmain.py --task {name} [--input "짧은 텍스트"] [--bg] [--llm_no N]` (cwd = 코드 루트)
- `--input` 은 자동으로 디렉터리 생성 + 옛 output 정리 + input.txt 작성. 긴 텍스트는 먼저 input.txt 를 수동 작성 후 `--input` 없이 기동
- `--bg` 백그라운드 우선 (PID 출력 후 exit), 같은 code_run 내에서 sleep 후 poll 가능. `--bg` 아니면 기동 + 폴링 합치기 금지
- subagent 의 cwd 는 여전히 temp, task 디렉터리가 아님
- input: 목표 + 제약만으로 충분, subagent 도 동등한 지능을 가짐. **단계/과한 설명 작성 금지**, 대량 데이터는 경로로 전달
- 통신: output.txt (append, `[ROUND END]` = 라운드 완료) → reply.txt 작성으로 계속 → 10분간 미작성 시 종료. reply 후 출력은 output1/2/3.txt (동일 형식)
- 개입 파일: `_stop` (현재 라운드 종료 후 종료) | `_keyinfo` (working memory 에 주입) | `_intervene` (지시 추가)
- **메인 agent 가 유휴일 때는 output 을 읽고 진행을 관찰하며 필요 시 개입 파일로 보정. 무뇌 장시간 sleep 폴링 금지**
- 감독 모드 기동 시 `--verbose` 추가, output 에 도구 실행 결과가 포함되어 메인 agent 가 요약만 신뢰하지 않고 원시 데이터를 직접 검토 가능

## 시나리오 1: 테스트 모드 - 행동 검증
**용도**: agent 의 실제 행동 관찰, RULES/L2/L3/SOP 보정
**흐름**: test_path 생성/input.txt 작성 → subagent 기동 → output.txt 폴링 (2초 간격) → 검증 → 정리/반복
**테스트 원칙**: 목표만 주고 위치 힌트 안 줌/방법 유도 안 함, 자율 선택을 관찰
**보정 루프**: 문제 발견 → 테스트 설계 → 근원 위치 (RULES/L2/L3/SOP) → patch 보정 → 검증
**기술 포인트**: Insight 우선순위 > SOP; subagent 의 cwd = temp/
**두 가지 테스트**:
- SOP 품질 테스트: input 에 SOP 명을 지정 (예: "ezgmail_sop 로 최근 3통 미열람 메일 확인"), 내비게이션 간섭 배제, 실패 시 SOP 문제
- 내비게이션 능력 테스트: input 에 목표만 작성, subagent 가 insight 에서 올바른 SOP 를 자율로 찾는지 검증. SOP 내용 인라인 금지

## 시나리오 2: Map 모드 - 병렬 처리
**용도**: N 개의 독립 동형 하위 작업을 각자의 subagent 에 분배해 처리
**핵심 장점**: 독립 컨텍스트. 문서 A 처리의 긴 컨텍스트가 문서 B 처리 품질을 오염시키는 것을 방지
**제약**:
- 파일시스템 공유는 장점: 다른 agent 가 다른 입력 파일을 처리해 다른 출력 파일을 생성
- 공유 자원 충돌: 키보드/마우스는 공유 불가; 브라우저는 잠시 병렬 사용 불가, 같은 탭 동시 조작 회피
- map 모드에 부적합한 작업 → 메인 agent 가 순차 실행, subagent 사용 불필요
**표준 흐름 (map-reduce)**:
1. 메인 agent 준비 단계: 데이터 크롤/덤프, 여러 독립 입력 파일로 저장
2. 분배: 파일별로 subagent 하나씩 기동 (메인 agent 자체도 그 중 하나를 처리 가능)
3. 수집: 모든 subagent 완료 대기, 메인 agent 가 각 출력 파일 읽고 결과 집계

## subagent 내부 plan_mode 사용
**원칙**: subagent 자체가 완전한 agent 이므로, 다단계 작업 수신 시 내부에 plan 을 만들어 실행 관리
**트리거 조건**: 작업이 3개 이상 하위 단계를 포함, 하위 단계 간 의존성 존재, checkpoint 로 실행 복구 필요
**구현 방식**:
1. **메인 agent 가 subagent 생성 시**: input.txt 에 작업이 다단계임을 명시, plan_mode 사용 권장
2. **subagent 내부 실행**: 다단계 작업 감지 시 `./subagent_plan.md` 생성하여 plan_mode 로 실행
3. **메인 agent 모니터링**: 최종 결과 (output*.txt) 만 관심, subagent 내부 실행 방식은 무관
4. **파일 전달 메커니즘**: 메인 agent 가 subagent 생성 시 task_dir 에 `context.json` 생성, 모든 파일의 **절대 경로** 포함
   **⚠ subagent 기동 후 첫 단계는 반드시 context.json 읽기**
   **⚠ 모든 파일 조작은 context.json 내 절대 경로 사용**
**형식 예**:
```json
{
  "task": "작업 설명",
  "work_dir": "/absolute/path/to/plan_dir/",
  "input_files": {
    "paper_info": "/absolute/path/to/paper_info.txt"
  },
  "output_files": {
    "pdf": "/absolute/path/to/paper.pdf",
    "report": "/absolute/path/to/paper_report.md"
  },
  "dependencies": ["paper_info.txt 가 존재해야 함"]
}
```
