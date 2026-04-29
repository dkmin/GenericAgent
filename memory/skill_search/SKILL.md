# Skill Search — 105K 스킬 카드 검색

> 105K+ 스킬 카드에서 가장 부합하는 skill 을 시맨틱 검색합니다. 외부 의존성 없음, 기본 API 주소 내장, 즉시 사용 가능.

## 가장 간단한 호출

```python
import sys; sys.path.append('../memory/skill_search')
from skill_search import search

results = search("python send email")  # ⚠️ 반드시 영어 쿼리, 한국어/중국어 매칭 효과 매우 낮음
for r in results:
    s = r.skill
    print(f"[{r.final_score:.2f}] {s.name} — {s.one_line_summary}")
    print(f"  key: {s.key}  category: {s.category}  tags: {s.tags[:3]}")
```

## API 시그니처

```python
search(query, env=None, category=None, top_k=10) -> list[SearchResult]
#  env: 자동 감지, 보통 미지정
#  category: 선택 필터, 예: "devops"
#  top_k: 반환 수, 기본 10
```

## 반환 구조

```
SearchResult
  .final_score    float     종합 점수 (0~1)
  .relevance      float     시맨틱 관련도
  .quality        float     품질 점수
  .match_reasons  list[str] 매칭 이유
  .warnings       list[str] 경고
  .skill          SkillIndex ↓

SkillIndex (자주 쓰는 필드)
  .key              str       고유 식별자/경로
  .name             str       이름
  .one_line_summary str       한 줄 요약
  .description      str       상세 설명
  .category         str       카테고리
  .tags             list[str] 태그
  .form             str       형태 (sop/script/...)
  .autonomous_safe  bool      자율 실행 안전 여부
```

## CLI

```bash
python -m skill_search "python testing"
python -m skill_search "docker deployment" --category devops --top 5
python -m skill_search "git" --json
python -m skill_search --stats
python -m skill_search --env
```

## 설정

| 항목 | 기본값 | 설명 |
|---|---|---|
| API 주소 | `http://www.fudankw.cn:58787` | 환경변수 `SKILL_SEARCH_API` 로 덮어쓰기 가능 |
| API 키 | 없음 (선택) | 환경변수 `SKILL_SEARCH_KEY` |
