# ljqCtrl 사용 및 좌표 변환 SOP

> **must call update working ckp**: `ljqCtrl 은 항상 물리 좌표 사용｜pyautogui 금지｜조작 전 gw 로 창 활성화`

## 0. API 빠른 참조 (Signatures)
- `ljqCtrl.dpi_scale`: float (스케일 계수 = 논리 너비 / 물리 너비)
- `ljqCtrl.SetCursorPos(z)`: 마우스를 논리 좌표 z=(x, y) 로 이동
- `ljqCtrl.Click(x, y=None)`: 클릭 시뮬레이션. `Click((x, y))` 또는 `Click(x, y)` 지원
- `ljqCtrl.Press(cmd, staytime=0)`: 키 입력 시뮬레이션. 예: `Press('ctrl+c')`
- `ljqCtrl.FindBlock(fn, wrect=None, threshold=0.8)`: 이미지 찾기. `((center_x, center_y), is_found)` 반환
- `ljqCtrl.MouseDClick(staytime=0.05)`: 마우스 더블클릭

## 1. 환경 로딩
도구 모듈을 import 하려면 먼저 `../memory` 를 path 에 추가해야 합니다:
```python
import sys, os, pygetwindow as gw
sys.path.append("../memory")
import ljqCtrl
```

## 2. 핵심: High-DPI 물리 좌표 환산
`ljqCtrl` 의 `Click/MoveTo` 인터페이스는 **물리 픽셀 좌표**를 받습니다.
`pygetwindow` 등으로 창 위치(논리 좌표)를 가져올 때는 스케일 계수로 나눠야 합니다.

- **환산 공식**: `물리 좌표 = 논리 좌표 / ljqCtrl.dpi_scale`
- **참고**: 3840 (4K) 은 현재 개발 머신 예시일 뿐, 실제 물리 경계는 시스템 환경이 결정하므로 코드에서는 항상 `dpi_scale` 로 동적 계산해야 합니다.

## 3. 창 조작 및 클릭 흐름
1. **창 활성화**: `gw.getWindowsWithTitle('제목')` 으로 창을 얻고 `restore()` 와 `activate()` 호출
2. **좌표 계산**:
```python
win = gw.getWindowsWithTitle('微信')[0]
# 창 안의 어떤 점의 논리 좌표 (lx, ly) 계산
# 물리 좌표로 변환 후 클릭
px, py = lx / ljqCtrl.dpi_scale, ly / ljqCtrl.dpi_scale
ljqCtrl.Click(px, py)
```

## 4. 함정 회피 가이드
- **⚠️ 항상 물리 좌표 사용**: ljqCtrl.Click/SetCursorPos 에 전달하는 좌표는 반드시 물리 좌표(=스크린샷 픽셀 좌표)여야 합니다. pygetwindow 로 얻은 논리 좌표는 먼저 `/ dpi_scale` 변환합니다. 논리 좌표 전달 금지.
- **물리 검증**: 시뮬레이션 조작 전에 창이 `activate()` 로 전면에 와있는지 반드시 확인합니다.
- **오프셋**: 모든 상대 오프셋 픽셀 값(예: "오른쪽으로 10픽셀") 도 `dpi_scale` 로 나눠야 합니다.
- **좌표 정렬**: 물리 좌표 = 스크린샷 좌표; ljqCtrl 가 DPI 변환을 자동 처리하므로 수동으로 다시 계산하지 마십시오.
- **⚠️ 창 좌표 변환 함정**: `win32gui.GetWindowRect(hwnd)` 로 얻은 사각형은 타이틀바와 테두리를 포함하지만, 스크린샷 내용은 클라이언트 영역입니다. 스크린샷 안 요소를 클릭하려면 `win32gui.ClientToScreen(hwnd, (0, 0))` 로 클라이언트 영역 원점의 화면 좌표를 얻어 스크린샷 내 좌표를 더해야 합니다. GetWindowRect 좌상단 + 스크린샷 좌표를 직접 더하지 마십시오.
- **⚠️ win32 DPI 좌표 함정**: `SetProcessDPIAware()` 를 호출하지 않으면, `GetWindowRect/ClientToScreen/GetClientRect` 등에서 얻는 창/클라이언트 좌표는 보통 **논리 좌표**입니다. 후속 스크린샷이나 `ljqCtrl` 가 물리 픽셀을 쓴다면, 일관되게 `좌표 / ljqCtrl.dpi_scale` 처리를 해야 합니다. 동등한 대안: 먼저 `SetProcessDPIAware()` 를 호출하고 이후에는 raw 물리 좌표를 그대로 사용. 논리/물리 혼용 금지.
- **텍스트 입력**: ljqCtrl 에는 TypeText/SendKeys 가 없습니다. 입력란에 텍스트를 넣을 때: 먼저 클릭/세 번 클릭으로 필드 선택, 이후 `pyperclip.copy('텍스트'); ljqCtrl.Press('ctrl+v')`.
