# 스케줄 작업 SOP

디렉터리: `../sche_tasks/` 에 작업 정의 JSON, `../sche_tasks/done/` 에 실행 보고서

## 작업 JSON 형식 (*.json)
```json
{"schedule":"08:00", "repeat":"daily", "enabled":true, "prompt":"...", "max_delay_hours":6}
```
repeat 가능 값: daily | weekday | weekly | monthly | once | every_Nh (N 시간마다) | every_Nd (N 일마다)
max_delay_hours (선택, 기본 6): schedule 보다 몇 시간이 지나면 더 이상 트리거하지 않음. 부팅이 너무 늦어 옛 작업이 실행되는 것을 방지

## 트리거 흐름
1. scheduler.py (reflect/) 가 60초마다 sche_tasks/*.json 폴링
2. 모든 조건 충족 시에만 트리거: enabled=true + 현재 시간 ≥ schedule + 쿨다운 경과 (done/ 의 최신 보고서 타임스탬프 기준)
3. 트리거 시 prompt 조립, 보고서 경로 `../sche_tasks/done/YYYY-MM-DD_작업명.md` 포함
4. **작업 수신 후 첫 번째로 할 일**: update_working_checkpoint 로 보고서 대상 파일 경로를 기록, 긴 작업 도중 잊지 않도록
5. 실행 완료 후 위 경로에 보고서 작성 (scheduler 는 이 파일로 오늘 실행 여부를 판정)

## 로그와 모니터링
- scheduler 가 자동으로 `sche_tasks/scheduler.log` 에 로그 작성 (트리거/스킵/에러)
- `scheduler.health_check()` 는 모든 작업 상태 목록 반환 (HEALTHY/OVERDUE/DISABLED/NEVER_RUN/ERROR)
- JSON 파싱 오류, schedule 형식 오류, 알 수 없는 repeat 유형은 모두 로그에 기록

## 참고
- once 유형: 1회 실행 후 100년 쿨다운 (실효는 영구 스킵)
- 작업 파일은 "무엇을 할지"만 관리, 보고서 경로는 scheduler 가 자동 생성하여 prompt 에 주입
- sche_tasks 디렉터리는 ../, 즉 코드 root 아래에 있음
