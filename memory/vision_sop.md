# Vision API SOP

## ⚠️ 사전 규칙 (반드시 준수)

1. **먼저 창 열거**: vision 호출 전에 반드시 `pygetwindow` 로 창 제목을 열거하여, 대상 창이 존재하고 전면에 활성화되어 있는지 확인. 창이 없으면 스크린샷 금지.
2. **🚫 전체 화면 스크린샷 금지**: 반드시 ljqCtrl 로 창 영역을 캡처. 부분 (예: 타이틀바) 으로 충분하면 창 전체를 찍지 말고, 창으로 충분하면 절대 전체 화면을 찍지 마십시오. 전체 화면 스크린샷은 어떤 시나리오에서도 허용 안 됨.
3. **vision 안 써도 되면 안 쓰기**: 창 제목/로컬 OCR (`ocr_utils.py`) 로 필요한 정보를 얻을 수 있다면 vision API 를 호출하지 마십시오. token 절약하고 더 신뢰할 수 있음. Vision 은 최후 수단.

## 빠른 사용법

```python
from vision_api import ask_vision
result = ask_vision(image, prompt="이미지 내용 설명", backend="claude", timeout=60, max_pixels=1_440_000)
# image: 파일 경로 (str/Path) 또는 PIL Image
# backend: 'claude' (기본) | 'openai' | 'modelscope'
# 반환 str: 성공 시 모델 응답, 실패 시 'Error: ...'
```

## `vision_api.py` 가 없을 때, vision 능력 최초 구축

1. `memory/vision_api.template.py` → `memory/vision_api.py` 복사
2. 헤더의 "사용자 설정 영역" 만 수정: `mykey.py` 에서 변수명 스캔 (⚠️ 이름만 보고, apikey 값 출력 금지), 사용 가능한 설정명을 찾아 `CLAUDE_CONFIG_KEY` / `OPENAI_CONFIG_KEY` 에 채우고, `DEFAULT_BACKEND` 로 백엔드 선택 후 테스트
3. 폴백: 사용 가능한 config 가 없으면 `https://modelscope.cn/my/myaccesstoken` 에서 token 발급받아 `MODELSCOPE_API_KEY` 에 입력
