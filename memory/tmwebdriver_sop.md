# TMWebDriver SOP

- web_scan/web_execute_js 도구를 직접 사용하세요. 이 파일은 특성과 함정만 기록합니다.
- 하부: `../TMWebDriver.py` 가 Chrome 확장으로 사용자 브라우저를 인계받음 (로그인 상태/Cookie 유지)
- Selenium/Playwright 가 아니며, 사용자 브라우저 로그인 상태를 유지

## 공통 특성
- ⚠ web_execute_js 에서 `await` 사용 시 **명시적 `return`** 이 있어야 반환값을 받을 수 있음 (하부가 async 래핑이라 return 없으면 null 반환)
- ✅ web_scan 은 동일 출처 iframe 을 자동 관통; 크로스 도메인 iframe 은 CDP 또는 postMessage 필요 (아래 섹션 참조)

## 제한 (isTrusted)
- JS 이벤트의 `isTrusted=false`, 민감 조작 (예: 파일 업로드/일부 버튼) 이 차단될 수 있음. 이런 경우 **CDP 브리지** 우선
- ⚠ JS 로 버튼 클릭 시 새 탭이 안 열림 → 브라우저 팝업 차단 가능성, CDP 클릭으로 대체 시도
- 파일 업로드: JS 로 `<input type=file>` 채우기 불가; 우선 CDP batch: getDocument → querySelector → DOM.setFileInputFiles, 차선 ljqCtrl 물리 클릭
- 물리 좌표 변환 시: `physX = (screenX + rect 중심x) * dpr`, `physY = (screenY + chromeH + rect 중심y) * dpr`. 여기서 `chromeH = outerHeight - innerHeight`

## 내비게이션
- `web_scan` 은 현재 페이지만 읽고 이동하지 않음. 사이트 전환은 `web_execute_js` + `location.href='url'`

## Google 이미지 검색
- class 명이 난독화되어 있어 하드코딩 금지. 결과 클릭은 `[role=button]` div 사용
- web_scan 으로 사이드바 필터링, 팝업 후 JS 사용: 텍스트는 `document.body.innerText`, 큰 이미지는 img 를 순회해 `naturalWidth` 가 가장 큰 src 채택
- "방문" 링크: a 를 순회하며 `textContent.includes('访问')` 인 href 찾기
- 썸네일: `img[src^="data:image"]` 직접 추출; 큰 이미지 src 는 잘릴 수 있으니 `return img.src` 사용

## Chrome PDF 다운로드
시나리오: PDF 링크가 브라우저 안에서 미리보기로 열리고 다운로드되지 않음
```js
fetch('PDF_URL').then(r=>r.blob()).then(b=>{
  const a=document.createElement('a');
  a.href=URL.createObjectURL(b);
  a.download='filename.pdf';
  a.click();
});
```
주의: 동일 출처이거나 CORS 허용 필요. 크로스 도메인은 먼저 대상 도메인으로 이동 후 실행

## Chrome 백그라운드 탭 throttling
- 백그라운드 탭의 `setTimeout` 은 Chrome intensive throttling 으로 ≥1분/회로 지연. 확장 스크립트에서 setTimeout 폴링 의존 회피
- 일부 SPA 페이지는 CDP `Page.bringToFront` 로 전면 전환해야 데이터 로드

## CDP 브리지 (tmwd_cdp_bridge 확장) ⭐ 우선
확장 경로: `assets/tmwd_cdp_bridge/` (설치 필요, debugger 권한 포함)
⚠ TID 약속 식별자: 최초 실행 시 `assets/tmwd_cdp_bridge/config.js` 에 자동 생성 (gitignore 됨), 확장이 manifest 로 참조
호출: `web_execute_js` 의 script 에 JSON 문자열 직접 전달 (도구 계층이 객체 형식 자동 인식, WS → background.js cmd 라우팅)
```js
// JSON 문자열을 script 인자로 직접 전달, DOM 조작 불필요
web_execute_js script='{"cmd": "cookies"}'
web_execute_js script='{"cmd": "tabs"}'
web_execute_js script='{"cmd": "cdp", "tabId": N, "method": "...", "params": {...}}'
web_execute_js script='{"cmd": "batch", "commands": [...]}'
// 반환값은 바로 JSON 결과
```
통신 방식: ⭐ JSON 문자열 직접 전달 (우선) | TID DOM 방식 (TID 요소 + MutationObserver, web_scan/execute_js 의 하부 의존)
단일 명령: `{cmd:'tabs'}` | `{cmd:'cookies'}` | `{cmd:'cdp', tabId:N, method:'...', params:{...}}` | `{cmd:'management', method:'list|reload|disable|enable', extId:'...'}`
- management: list 는 모든 확장 정보 반환; reload/disable/enable 은 extId 필요
- ⭐ batch 혼합: `{cmd:'batch', commands:[{cmd:'cookies'},{cmd:'tabs'},{cmd:'cdp',...},...]}`
  - `{ok:true, results:[...]}` 반환, 한 요청에 여러 명령, CDP 는 lazy attach 로 session 재사용
  - 하위 명령은 외부 batch 의 tabId 를 자동 상속 (예: cookies 명령은 현재 페이지 URL 을 올바르게 가져옴)
  - `$N.path` 는 N 번째 결과 필드 참조 (0-indexed). 예: `"nodeId":"$2.root.nodeId"`
  - ⚠ batch 의 선행 명령이 실패하면 후속 `$N` 참조가 silent 하게 undefined 가 됨. results 배열의 각 항목 ok 상태를 점검해야 함
  - 전형적 파일 업로드: getDocument(**depth:1**) → querySelector(`input[type=file]`) → setFileInputFiles
  - 사상:
    - 동일 체인 내 nodeId 출처를 일관되게 유지, querySelector 경로와 performSearch 경로를 혼용 안 함
    - 업로드 후 프런트엔드 프레임워크가 인지 못 할 수 있음. 필요 시 JS 로 `input`/`change` 이벤트 보조 발송
    - 업로드 전 `input.accept` 확인. 다중 input 의 경우 accept/부모 컨테이너 의미로 구분
    - 요소 대기는 `DOM.performSearch('input[type=file]')` 로 가벼운 폴링 우선
    - 일시적 input 의 핵심은 **발견 → setFileInputFiles 시간 윈도우 단축**: 동일 batch 내 완료 우선; 안 되면 DOM 이벤트 리스너; 몽키 패치는 최후 수단
  - ⚠ tabId: CDP 기본은 sender.tab.id (현재 주입 페이지). 크로스 탭은 명시적 tabId 또는 batch 내 tabs 조회 선행 필요
- ⭐ 크로스 탭은 전면 전환 불필요: tabId 만 지정하면 백그라운드 탭 조작 가능

## CDP 클릭 전체 라이프사이클 (미검증, BBS#23)
- 일반 클릭은 **3 이벤트 시퀀스** 필요: mouseMoved → mousePressed → mouseReleased (50-100ms 간격)
  - mouseMoved 생략 시 MUI Tooltip/Ant Design Dropdown 등 hover 의존 컴포넌트가 작동 안 함
  - ⚠ autofill 해제는 예외적으로 mousePressed 만으로 충분 (아래 autofill 섹션 참조)
- 좌표 보정 (페이지에 transform:scale/zoom 있을 때):
  ```js
  var scale = window.visualViewport ? window.visualViewport.scale : 1;
  var zoom = parseFloat(getComputedStyle(document.documentElement).zoom) || 1;
  var realX = x * zoom; var realY = y * zoom;
  ```
- iframe 내부 요소 CDP 클릭: 좌표 합성 필요 `finalX = iframeRect.x + elRect.x`
  - 크로스 도메인 iframe 은 contentDocument 접근 불가:
  - ⚠ `Target.getTargets`/`Target.attachToTarget` 은 CDP 브리지에서 "Not allowed" 반환 (chrome.debugger 권한 제한)
  - ⭐ **검증된 방안**: `Page.getFrameTree` 로 iframe frameId 찾기 → `Page.createIsolatedWorld({frameId})` 로 contextId 획득 → `Runtime.evaluate({expression, contextId})` 로 iframe 내 JS 실행
  - batch 체인 참조: `$0.frameTree.childFrames` 순회로 url 매칭 frame 찾기, `$1.executionContextId` 를 evaluate 에 전달
  - postMessage 중계 방안은 content script 가 이미 iframe 에 주입된 경우만 유효, 제3자 결제 iframe 은 보통 미주입

## CDP 텍스트 입력 (미검증, BBS#23)
- `insertText` 는 빠르지만 key 이벤트 없음. 제어 컴포넌트는 `input` 이벤트 dispatch 보조 필요
- 완전한 키보드 시뮬레이션 필요 시 `dispatchKeyEvent` 로 키별 분배

## CDP DOM 도메인 closed Shadow DOM 관통 (미검증, BBS#24/#25)
- `DOM.getDocument({depth:-1, pierce:true})` 로 모든 Shadow 경계 (closed 포함) 관통
- `DOM.querySelector({nodeId, selector})` 로 위치 → `DOM.getBoxModel({nodeId})` 로 좌표
- getBoxModel 은 content 8 값 [x1,y1,...x4,y4] 반환, 중심은 **4점 평균**: centerX=sum(x)/4, centerY=sum(y)/4
  - ⚠ 대각선 평균으로 단순화 불가 — 요소에 transform:rotate/skew 있을 때 4점이 사각형 아님
- querySelector 는 **Shadow 경계를 가로지르는 조합 셀렉터 작성 불가**, 단계 분리 필요: 먼저 host 찾고 그 shadow 내 자식 요소 찾기
- ⚠ nodeId 는 DOM 변경 시 무효화 → `backendNodeId` 가 더 안정적, 또는 getDocument 재호출로 갱신


## autofill 획득과 로그인
감지: web_scan 출력의 input 에 `data-autofilled="true"`, value 가 보호 힌트로 표시 (실제 값 아님, Chrome 보안 보호로 클릭 해제 필요)
- ⚠ **사전 조건: 반드시 먼저 CDP `Page.bringToFront` 로 탭을 전면 전환**. Chrome 은 전면 탭에서만 autofill 보호값을 해제, 백그라운드 탭은 물리 클릭 무효
- ⭐ **원클릭 해제와 로그인**: bringToFront → mousePressed 로 임의 필드 클릭 (Released 불필요, 한 번 해제로 페이지 전체 적용) → 500ms 대기 → input/change 이벤트 보조 → 로그인 클릭

## 인증 코드/페이지 시각 스크린샷
- ⭐ CDP 스크린샷 우선: `Page.captureScreenshot`(format:'png') → base64 반환, 전면/백그라운드 탭 무관, 전체 페이지 고화질
- 인증 코드 canvas/img: JS `canvas.toDataURL()` 로 base64 직접 획득이 가장 깔끔

## simphtml 와 TMWebDriver 디버깅
- simphtml 디버깅은 반드시 `code_run` 으로 실제 브라우저에 JS 주입 (Python 단에서 DOM 시뮬레이션 불가)
- `d=TMWebDriver()`, `d.set_session('url_pattern')`, `d.execute_js(code)` → `{'data': value}` 반환
- simphtml: `str(simphtml.optimize_html_for_tokens(html))` — BS4 Tag 반환이므로 str() 필요

## 연결 안 될 때 진단
web_scan 실패 시 순서대로 진단 (자동 감지 우선, 사용자 참여는 최후):
① 브라우저 안 켜졌나? → 브라우저 프로세스 실행 중인지 확인 (tasklist/ps), 없으면 기동하고 정상 URL 열기 (⚠ about:blank 등 내부 페이지는 확장 미로딩)
② WS 백그라운드 죽었나? → 로컬 18766 포트 미수신이면 dead → 수동으로 **백그라운드 지속 실행** `from TMWebDriver import TMWebDriver; TMWebDriver()` 으로 master 기동
③ 확장 미설치? → Chrome 사용자 디렉터리의 `Secure Preferences` 읽기 → `extensions.settings` 에서 `path` 가 `tmwd_cdp_bridge` 를 포함하는 항목 찾기
  찾으면 → 확장 설치됨, 다른 원인 진단; 없으면 → web_setup_sop 로
④ 위 모두 정상이지만 여전히 연결 안 됨 → 사용자 협조 요청
