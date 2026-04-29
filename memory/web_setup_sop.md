# Web 도구체인 초기화 실행 SOP

web_scan 과 web_execute_js 가 이미 사용 가능 상태라면 본 SOP 를 실행할 필요 없음.
초기 설치 시, code_run 은 사용 가능하지만 web 도구가 아직 설정되지 않은 경우에만 사용.

## 목표
시스템 권한 (code_run) 만 갖춘 상태에서 Web 인터랙션 능력 (web_scan / web_execute_js) 을 구축.

## 사전: 브라우저 감지

## tmwd_cdp_bridge 확장 설치
확장 경로: `../assets/tmwd_cdp_bridge/` (MV3 Chrome 확장, CDP debugger + scripting + cookie 능력 포함)

### 확장 관리 페이지 자동 열기
`chrome://extensions` 는 명령줄이나 JS 로 열 수 없음. 클립보드 + 주소창 방식 필요

### 설치 단계 (chrome 확장 페이지는 자동화 어려움)
1. 확장 관리 페이지 열고 「개발자 모드」활성화
2. 「압축 해제된 확장 프로그램 로드」클릭, `assets/tmwd_cdp_bridge/` 디렉터리 선택, 또는 사용자에게 직접 드래그 요청
3. "오류" 표시되어도 무시 가능. 일반적으로 GA 미연결이라 그런 것

## 검증
⚠ web_scan 이 「사용 가능한 탭이 없음」을 표시한다고 해서 반드시 확장 미설치는 아님. 브라우저 미실행이거나 blank 페이지만 있을 수도 있음.
이 때 함부로 시도 금지, 먼저 `start "" "https://www.baidu.com"` 으로 정상 페이지를 연 뒤 `web_scan` 으로 재확인.
여전히 사용 불가하면, 기본 브라우저가 무엇인지/플러그인이 어느 브라우저에 설치됐는지/설치 여부를 자동 감지 불가 — 이때 사용자 협조 요청.
