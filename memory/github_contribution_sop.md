# GitHub Contribution SOP
**트리거**: 오픈소스 프로젝트에 PR 제출 (버그 수정 / 기능 추가 / 문서 수정) | **금지**: 코드만 읽고 변경 제출이 필요 없는 경우
**핵심 원칙**: 한 PR 은 한 가지 일만, 테스트 통과해야 push, 프로젝트 규칙 존중

## 사전 준비 (새 프로젝트 첫 진입 시)
1. **프로젝트 규칙 읽기** (필수, 건너뛰기 금지)
   ```
   file_read('CONTRIBUTING.md')  # 기여 가이드
   file_read('.github/PULL_REQUEST_TEMPLATE.md')  # PR 템플릿
   file_read('.github/ISSUE_TEMPLATE/')  # Issue 템플릿
   ```
   없으면 README 의 Contributing 섹션을 읽습니다. 그것도 없으면 본 SOP 의 기본 절차를 따릅니다.

2. **프로젝트 구조와 테스트 방식 파악**
   ```
   # 테스트 명령 찾기
   file_read('package.json')  # Node: scripts.test
   file_read('Makefile')      # 또는 Makefile
   file_read('pyproject.toml') # Python: [tool.pytest] 등
   ```
   테스트 명령을 메모해 둡니다. 테스트를 돌리지 않은 PR = 검증되지 않은 PR.

3. **Fork + Clone**
   ```
   code_run('bash', 'gh repo fork OWNER/REPO --clone && cd REPO && git remote -v')
   ```

## 작업 흐름 (PR 마다)

### Step 1: 목표 확정
- 관련 Issue 읽기 (있을 경우)
- 한 줄로 명확히: 무엇을, 왜 바꾸는가
- 확인: 누가 이미 작업 중인가? (Issue assignee, 최근 PR 확인)

### Step 2: 브랜치 생성
```
code_run('bash', 'git checkout -b fix/issue-설명 && git status')
```
브랜치 명명: `fix/xxx` (버그 수정), `feat/xxx` (신규 기능), `docs/xxx` (문서)

### Step 3: 변경 구현
- **최소 변경**: 꼭 바꿔야 하는 것만, 무관한 코드를 김에 리팩터링하지 않습니다
- **프로젝트 스타일 준수**: 들여쓰기, 네이밍, 주석 스타일을 기존 코드와 일치시킵니다
- **로직 단위마다 한 번씩 커밋**:
  ```
  code_run('bash', 'git add -A && git commit -m "fix: 간결한 설명"')
  ```
- Commit 메시지 형식: 프로젝트 규칙 준수 (Conventional Commits / 프로젝트 자체 규칙)
  - 규칙이 없으면: `type: 짧은 설명`
  - type: fix / feat / docs / refactor / test / chore

### Step 4: 테스트 (건너뛰기 금지)
```
code_run('bash', '프로젝트 테스트 명령')  # npm test / pytest / go test ./...
```
**체크 항목**:
- [ ] 기존 테스트 모두 통과?
- [ ] 신규 기능에 대응 테스트가 있는가? (프로젝트가 테스트 문화가 있다면)
- [ ] lint/type check 통과? (프로젝트에 있다면)

**⛔ 테스트 미통과 시 push 금지. 통과할 때까지 수정.**

### Step 5: Push + PR 제출
```
code_run('bash', 'git push origin HEAD')
```
PR 내용:
- **제목**: `type: 간결한 설명` 또는 프로젝트 템플릿 준수
- **본문**에 반드시 포함:
  - 무엇을 바꿨는가 (What)
  - 왜 바꿨는가 (Why) — Issue 와 연결할 때는 `Fixes #123`
  - 어떻게 테스트했는가 (Testing)
- **쓰지 말 것**: 과한 설명, 무관한 배경, 자화자찬

### Step 6: CI 확인
PR 제출 후 CI 대기:
- ✅ 모두 통과 → review 대기
- ❌ 실패 → 로그를 보고 자기 문제부터 수정
  - CI 실패가 upstream 문제 (당신 변경과 무관) → PR 에 명시
  ```
  code_run('bash', 'gh run view --log-failed')
  ```

### Step 7: Review 대응
- **reviewer 가 고치라면 고침**, 스타일 취향으로 다투지 않음
- **동의하지 않는 기술 결정**: 정중하게 이유를 설명하되, 최종 판단은 maintainer 존중
- **수정 후**: commit 추가 + 테스트 + push, force push 금지 (maintainer 가 squash 를 요청한 경우 제외)
- **reviewer 가 테스트 추가 요청** → 추가합니다, 선택 사항이 아닙니다

## 흔한 실수 (회피)

| 실수 | 올바른 방법 |
|------|----------|
| 한 PR 에 여러 일 | 독립적인 여러 PR 로 분리 |
| PR 제출 후 방치 | 매일 review 상태 확인 |
| 테스트 안 돌리고 push | Step 4 는 강제 게이트 |
| 코드 스타일 흐트러짐 | 기존 코드와 일치 |
| commit message "update" | 무엇을 바꿨는지 구체적으로 |
| force push 로 review 이력 덮어쓰기 | commit 추가 |
| PR 설명 비어있음 | What/Why/Testing 작성 |

## 후속 상태 머신

```
PR 제출 → CI 대기
  CI ✅ → Review 대기
    Review 통과 → Merge 대기 ✅
    Review 수정 요구 → 수정 + 테스트 → CI 대기로 복귀
  CI ❌ → 수정 → CI 대기로 복귀
```

매 라운드 후속 확인:
```
code_run('bash', 'gh pr status')
code_run('bash', 'gh pr checks PR_NUMBER')
code_run('bash', 'gh pr view PR_NUMBER --comments')
```
