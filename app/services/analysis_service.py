# app/services/analysis_service.py

"""
일기 텍스트를 분석해 감정(단일 라벨) + 상황 맞춤 음악 2~3곡을 추천하는 모듈.

핵심 로직
- 다중 컨텍스트 감지(예: study, calm, rain 등 원하는 만큼 확장 가능)
- 감정 강도(score)에 따라 사용자 선호 대분류 가중치 가변 적용
  - score < PREFERRED_FORCE_THRESHOLD: 가능한 한 선호 대분류 우선
  - score >= PREFERRED_FORCE_THRESHOLD: 상황/감정 적합성 우선
- 연애/실연 테마는 일기에 단서 없으면 금지
- 공부/집중 맥락에서 고BPM/고에너지 회피
- 장르는 항상 '대분류/소분류'로 정규화(genre, genre_main, genre_sub)
- 결과 검증 후 필요 시 1회 재생성(보정)
- OpenAI Python SDK v1 사용, JSON-only 응답 강제(response_format)

추가
- 출생연도(year) 기반 나이/나이대(age group)를 프롬프트에 명시해 세대 취향/향수/템포 가이드를 제공
- 선호 장르(genres)는 백엔드(DB)에서 조회해 넘어온 대분류명(예: ["pop","jazz"])을 사용
"""

import json
import re
from datetime import datetime
from typing import Optional, List, Tuple

from openai import OpenAI
from app.core.config import settings

# -------------------- OpenAI Client --------------------
client = OpenAI(api_key=settings.OPENAI_API_KEY)

# -------------------- 규칙 파라미터 --------------------
PREFERRED_FORCE_THRESHOLD = 0.70  # 감정 점수 기준(낮으면 선호 대분류를 더 우선)

# 공부/집중 맥락에서 피할 요소
_HIGH_ENERGY_TAGS = [
    "edm", "big room", "dubstep", "hardstyle", "electro house",
    "drum and bass", "dnb", "festival"
]

# -------------------- 컨텍스트 마커 (확장 가능) --------------------
# 기본 컨텍스트
_CONTEXT_MARKERS = {
    "study":     ["공부", "집중", "랩실", "도서관", "시험", "과제", "숙제", "리포트", "study", "focus"],
    "energy":    ["운동", "헬스", "웨이트", "러닝", "달리기", "드라이브", "업비트", "신나", "에너지", "파티", "춤", "클럽"],
    "calm":      ["차분", "조용", "편안", "힐링", "휴식", "명상", "잔잔", "고요", "진정", "안정"],
    # 연애/실연(일기에 있을 때만 허용)
    "romance":   ["연애", "사랑", "연인", "로맨스", "그리움", "보고싶", "사랑해", "romance", "romantic", "love", "miss you"],
}

# 추가 컨텍스트
_EXTRA_CONTEXT_MARKERS = {
    "nostalgia":   ["추억", "옛날", "회상", "그때", "그립", "nostalgia", "remember"],
    "stress":      ["스트레스", "압박", "불안", "걱정", "과부하", "번아웃", "overwhelmed", "burnout", "피로"],
    "commute":     ["지하철", "버스", "통학", "출근", "퇴근", "혼잡", "commute", "지옥철"],
    "rain":        ["비", "장마", "비오는", "우중", "rain", "rainy"],
    "late-night":  ["밤새", "새벽", "늦은 밤", "야밤", "야근", "잠이 안와", "불면", "late night", "midnight", "insomnia"],
    "social":      ["친구들", "모임", "파티", "회식", "만남", "모여", "social"],
    "family":      ["엄마", "아빠", "부모", "형제", "자매", "가족"],
    "travel":      ["여행", "비행기", "공항", "숙소", "호텔", "여정", "trip", "여행지"],
    "work":        ["업무", "프로젝트", "회의", "보고서", "직장", "회사", "work", "deadline"],
    "celebration": ["생일", "기념일", "축하", "행복한 날", "케이크", "celebrate"],
}
_CONTEXT_MARKERS.update(_EXTRA_CONTEXT_MARKERS)

# -------------------- 로맨스/실연 금지용 키워드 --------------------
_BREAKUP_WORDS = [
    "이별", "헤어지", "실연", "권태기", "떠났", "전남친", "전여친", "전 애인",
    "breakup", "heartbreak", "ex", "broken heart", "split", "separation", "divorce"
]
_ROMANCE_MARKERS = [
    "연애", "사랑", "연인", "로맨스", "그리움", "보고싶", "사랑해",
    "boyfriend", "girlfriend", "romance", "romantic", "love", "miss you"
]

# -------------------- 대분류 키워드 (정규화용, 추천을 제한하지 않음) --------------------
_MAJOR_KEYWORDS = {
    "pop": {"pop", "k-pop", "kpop", "synthpop", "city pop", "indie-pop", "pop-rock",
            "pop ballad", "pop-ballad", "ballad", "dream pop", "bedroom pop", "chill pop", "lo-fi pop"},
    "rock": {"rock", "alt rock", "alternative", "punk", "metal", "shoegaze", "grunge",
             "hard rock", "indie rock", "post-rock", "math rock", "emo"},
    "jazz": {"jazz", "swing", "bebop", "bossa", "fusion", "cool jazz", "latin jazz"},
    "classical": {"classical", "orchestral", "piano", "chamber", "baroque", "romantic", "minimal", "neoclassical"},
    "hiphop": {"hip-hop", "hiphop", "rap", "trap", "boom bap", "lo-fi hip hop", "lofi hip hop", "drill"},
    "electronic": {"electronic", "edm", "house", "trance", "techno", "synthwave", "chillstep",
                   "downtempo", "ambient", "idm", "dnb", "drum and bass", "drum & bass"},
    # 선호 집합 외 대분류(허용)
    "r&b": {"r&b", "r&b-soul", "neo-soul", "soul"},
    "folk": {"folk", "indie folk", "acoustic"},
    "country": {"country"},
    "blues": {"blues"},
    "reggae": {"reggae", "ska", "dub"},
    "world": {"world", "klezmer", "afrobeat", "latin", "balkan"},
    "metal": {"metal", "black metal", "death metal", "power metal"},
    "other": set(),
}

_ALLOWED_LABELS = ["기쁨", "슬픔", "화남", "무기력", "예민"]

# -------------------- 컨텍스트별 소분류 힌트 (있으면 참고, 없으면 패스) --------------------
_CONTEXT_SUBGENRE_HINTS = {
    "study": {
        "pop":        ["dream pop", "chill pop", "lo-fi pop", "acoustic ballad (non-romantic)"],
        "electronic": ["ambient", "downtempo", "chillstep", "lo-fi electronic"],
        "hiphop":     ["lo-fi hip hop", "jazzy hip hop (instrumental)"],
        "jazz":       ["cool jazz", "bossa (instrumental)", "piano trio"],
        "classical":  ["minimal", "baroque", "solo piano"],
        "rock":       ["post-rock (instrumental)", "soft rock (mellow)"],
        "r&b":        ["neo-soul (mellow)", "instrumental r&b"],
        "folk":       ["indie folk (instrumental)", "acoustic instrumental"]
    },
    "calm": {
        "pop":        ["pop-ballad (non-romantic)", "indie-pop (soft)", "dream pop"],
        "electronic": ["ambient", "downtempo"],
        "hiphop":     ["lo-fi hip hop (soft)"],
        "jazz":       ["ballad", "cool jazz", "bossa"],
        "classical":  ["minimal", "adagio", "solo piano"],
        "rock":       ["soft rock", "acoustic rock"],
        "r&b":        ["neo-soul (soft)"],
        "folk":       ["acoustic", "indie folk"]
    },
    "energy": {
        "pop":        ["dance-pop", "synthpop", "city pop"],
        "electronic": ["house", "trance", "techno", "edm"],
        "hiphop":     ["trap", "drill", "boom bap (upbeat)"],
        "jazz":       ["swing (uptempo)", "fusion"],
        "rock":       ["punk", "garage rock", "hard rock"],
        "classical":  ["allegro (orchestral)"],
        "r&b":        ["contemporary r&b (upbeat)"]
    },
    "romance": {  # 일기에 로맨스/이별 단서 있을 때만 허용
        "pop":        ["pop-ballad (romantic)"],
        "r&b":        ["slow jam", "neo-soul ballad"],
        "jazz":       ["jazz ballad"],
        "rock":       ["soft rock ballad"],
        "classical":  ["romantic adagio"]
    },
    # 확장
    "nostalgia": {
        "pop":        ["dream pop", "bedroom pop"],
        "folk":       ["indie folk", "acoustic"],
        "jazz":       ["jazz ballad"],
        "hiphop":     ["lo-fi hip hop (nostalgic)"]
    },
    "stress": {
        "electronic": ["ambient", "downtempo"],
        "classical":  ["minimal", "solo piano"],
        "hiphop":     ["lo-fi hip hop"],
        "pop":        ["chill pop"]
    },
    "commute": {
        "pop":        ["city pop", "indie-pop (mellow)"],
        "electronic": ["synthwave (mild)", "downtempo"],
        "hiphop":     ["lo-fi hip hop"]
    },
    "rain": {
        "electronic": ["ambient (rainy)"],
        "jazz":       ["bossa", "jazz ballad"],
        "folk":       ["acoustic"],
        "pop":        ["chill pop"]
    },
    "late-night": {
        "electronic": ["downtempo", "ambient"],
        "hiphop":     ["chillhop", "lo-fi hip hop"],
        "r&b":        ["neo-soul (soft)"],
        "pop":        ["dream pop"]
    }
    # 필요 시 계속 추가 가능
}

# -------------------- 유틸 함수 --------------------
def _has_any(text: str, keywords: List[str]) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in keywords)

def _parse_bpm(tempo: str) -> Optional[int]:
    m = re.search(r"(\d{2,3})\s*BPM", (tempo or ""), re.IGNORECASE)
    return int(m.group(1)) if m else None

def _normalize_emotion_label(label: str) -> str:
    s = (label or "").strip().lower()
    if "기쁨" in s: return "기쁨"
    if "슬픔" in s or "외로" in s: return "슬픔"
    if "화" in s or "분노" in s: return "화남"
    if "무기력" in s or "지침" in s or "피곤" in s: return "무기력"
    if "예민" in s or "불안" in s or "초조" in s or "걱정" in s: return "예민"
    return "무기력"

def _detect_contexts(diary: str) -> List[str]:
    """키워드 기반 다중 컨텍스트 감지. 0개면 ['neutral'] 반환."""
    found: List[str] = []
    t = (diary or "").lower()
    for ctx, words in _CONTEXT_MARKERS.items():
        if any(w.lower() in t for w in words):
            found.append(ctx)
    if not found:
        return ["neutral"]
    # 중복 제거/안정 정렬
    seen, ordered = set(), []
    for c in found:
        if c not in seen:
            seen.add(c)
            ordered.append(c)
    return ordered

def _build_subgenre_hint(preferred_majors: List[str], ctx_list: List[str]) -> str:
    """
    감지된 여러 컨텍스트에 대해, 존재하는 힌트만 모아 텍스트화.
    힌트는 '참고용'이며 강제 규칙이 아님.
    """
    lines: List[str] = []
    majors_for_hint = preferred_majors[:] if preferred_majors else None
    for ctx in ctx_list:
        table = _CONTEXT_SUBGENRE_HINTS.get(ctx)
        if not table:
            continue
        targets = majors_for_hint or list(table.keys())
        collected: List[str] = []
        for major in targets:
            subs = table.get(major)
            if subs:
                collected.append(f"  - {major}: {', '.join(subs)}")
        if collected:
            lines.append(f"[{ctx}]")
            lines.extend(collected)
    return "컨텍스트별 소분류 예시(참고용):\n" + ("\n".join(lines) if lines else "특정 예시 제한 없음.")

def _coarse_major_guess(sub: str) -> str:
    """소분류 문자열로부터 대분류 추정(휴리스틱)."""
    s = (sub or "").lower()
    checks = [
        ("electronic", ["ambient", "idm", "synthwave", "future bass", "dnb", "drum and bass", "drum & bass",
                        "techno", "house", "trance", "edm", "downtempo", "chillstep"]),
        ("hiphop",     ["hip hop", "hip-hop", "rap", "trap", "drill", "boom bap", "lofi"]),
        ("rock",       ["rock", "punk", "metal", "shoegaze", "grunge", "post-rock", "math rock", "emo"]),
        ("pop",        ["pop", "k-pop", "kpop", "synthpop", "city pop", "indie pop",
                        "pop ballad", "pop-ballad", "ballad", "dream pop", "bedroom pop", "chill pop", "lo-fi pop"]),
        ("jazz",       ["jazz", "swing", "bebop", "bossa", "fusion", "cool jazz", "latin jazz"]),
        ("classical",  ["classical", "orchestral", "piano", "chamber", "baroque", "romantic", "minimal", "neoclassical"]),
        ("r&b",        ["r&b", "soul", "neo-soul"]),
        ("folk",       ["folk", "acoustic"]),
        ("blues",      ["blues"]),
        ("reggae",     ["reggae", "ska", "dub"]),
        ("world",      ["afrobeat", "latin", "balkan", "klezmer", "world"]),
    ]
    for major, kws in checks:
        if any(k in s for k in kws):
            return major
    return "other"

def _infer_major_from_sub(sub: str, preferred_majors: List[str]) -> str:
    """소분류 → 대분류 추정. 선호 대분류가 매치되면 우선."""
    s = (sub or "").lower()
    # 1) 선호 대분류 우선
    for major in preferred_majors:
        for kw in _MAJOR_KEYWORDS.get(major, set()):
            if kw in s:
                return major
    # 2) 전체 키워드에서 탐색
    for major, kws in _MAJOR_KEYWORDS.items():
        if any(kw in s for kw in kws):
            return major
    # 3) 휴리스틱
    return _coarse_major_guess(s)

def _ensure_major_sub(raw: str, preferred_majors: List[str]) -> Tuple[str, str, str]:
    """항상 '대분류/소분류'를 보장."""
    g = (raw or "").strip()
    if "/" in g:
        main, sub = [p.strip().lower() for p in g.split("/", 1)]
        return main, sub, f"{main}/{sub}"
    sub = g.lower() or "misc"
    main = _infer_major_from_sub(sub, preferred_majors) or "other"
    return main, sub, f"{main}/{sub}"

def _theme_conflict(
    diary: str,
    title: str,
    reason: str,
    summary: str,
    tempo: str,
    genre: str
) -> Tuple[bool, str]:
    """
    상황 불일치 규칙 체크.
    - (A) 곡에 연애/실연 테마가 보이는데, 일기에 관련 단서가 없으면 충돌
    - (B) 공부/집중 맥락에서 고BPM(>=120) 또는 고에너지 전자/댄스 태그면 충돌
    """
    diary_has_romance = _has_any(diary, _ROMANCE_MARKERS + _BREAKUP_WORDS)
    song_has_romance  = _has_any(title,  _ROMANCE_MARKERS + _BREAKUP_WORDS) \
                        or _has_any(reason, _ROMANCE_MARKERS + _BREAKUP_WORDS) \
                        or _has_any(summary, _ROMANCE_MARKERS + _BREAKUP_WORDS)
    if song_has_romance and not diary_has_romance:
        return True, "romance_theme_without_diary_context"

    # 공부/집중 맥락 필터
    if _has_any(diary, _CONTEXT_MARKERS["study"]):
        bpm = _parse_bpm(tempo or "")
        if bpm and bpm >= 120:
            return True, "too_fast_for_study"
        if _has_any(genre, _HIGH_ENERGY_TAGS):
            return True, "too_energetic_for_study"

    return False, ""

# 접두사(라벨) 제거용 정규식: "일기와의 연결 이유:", "추천 이유:", "이유:", "Reason:" 등
_REASON_PREFIX_RE = re.compile(
    r"^\s*(일기와의\s*연결\s*이유|연결\s*이유|추천\s*이유|이유|reason|why)\s*[:：\-]\s*",
    re.IGNORECASE,
)

def _clean_reason_text(s: Optional[str]) -> str:
    if not s:
        return ""
    return _REASON_PREFIX_RE.sub("", s).strip()

def _choose_eul_reul(s: str) -> str:
    """끝 글자 받침에 따라 '을/를' 선택"""
    if not s:
        return "를"
    code = ord(s[-1])
    if 0xAC00 <= code <= 0xD7A3:
        return "을" if (code - 0xAC00) % 28 else "를"
    return "를"

def _format_korean_reason_sentence(reason_parts: dict) -> str:
    """
    reason_parts = {
        "summary": "오늘 하루 종일 과제를 했구나",
        "clues": ["혼자 랩실에 남아 있었다", "주변이 조용해졌다", "마음이 편안하다"],
        "interpretation": "편안함과 외로움이 공존하는 상황인 것 같아"
    }
    → '오늘 하루 종일 과제를 했구나. "혼자 랩실에 남아 있었다", "주변이 조용해졌다", "마음이 편안하다"를 보니 편안함과 외로움이 공존하는 상황인 것 같아.'
    """
    if not isinstance(reason_parts, dict):
        return str(reason_parts)

    summary = (reason_parts.get("summary") or "").strip()
    interp  = (reason_parts.get("interpretation") or "").strip()
    clues   = [c.strip() for c in (reason_parts.get("clues") or []) if c.strip()]

    if clues:
        # 유니코드 큰따옴표로 감싸기
        clues_text = ", ".join([f'“{c}”' for c in clues])
        particle = _choose_eul_reul(clues[-1])
        return f'{summary}. {clues_text}{particle} 보니 {interp}.'
    else:
        return f'{summary}. 그래서 {interp}.'

# -------------------- 메인 API --------------------
def analyze_text(text: str, year: int, genres: Optional[List[str]] = None) -> dict:
    """
    감정(단일 라벨) + 상황맞춤 음악 "후보 2~3곡" 추천.
    입력:
      - text: 일기 본문
      - year: 사용자 출생연도 (DB에서 조회한 값)
      - genres: 사용자 선호 대분류 리스트(예: ["pop","jazz"]).
    반환(JSON):
      {
        "emotion": {"label": "...", "score": 0.xx, "reason": "요약/단서/해석"},
        "music_candidates": [
          {
            "title": "...", "artist": "...", "album": "...",
            "genre": "main/sub",
            "tempo": "느림|중간|빠름 + BPM", "mood": "...",
            "track_summary": "곡 설명 한 줄",
            "reason": "일기와 왜 어울리는지 한두 문장"
          }
        ]
      }
    """
    # OpenAI 사용 가드
    if not settings.ENABLE_OPENAI or not settings.OPENAI_API_KEY:
        raise RuntimeError("OpenAI API is disabled. ENABLE_OPENAI/OPENAI_API_KEY 확인")

    # 선호 대분류 정규화
    preferred_majors = [g.lower() for g in (genres or [])]
    # 컨텍스트 감지
    contexts = _detect_contexts(text)  # 예: ["study","calm","rain"]
    subgenre_hint_text = _build_subgenre_hint(preferred_majors, contexts)
    contexts_text = ", ".join(contexts)

    # 나이/나이대 계산
    try:
        current_year = datetime.now().year
        age = max(0, int(current_year) - int(year))
    except Exception:
        age = 0  # 방어값

    if age < 20:
        age_group = "10대"
        age_guide = "최신 트렌디/밝은 곡을 우선 고려."
    elif age < 30:
        age_group = "20대"
        age_guide = "감성적 발라드/인디 위주, 트렌디/잔잔 밸런스."
    elif age < 40:
        age_group = "30대"
        age_guide = "차분한 팝/발라드, 안정적 분위기 선호."
    elif age < 50:
        age_group = "40대"
        age_guide = "향수 자극 곡 일부 허용, 과한 전자음 지양."
    else:
        age_group = "50대 이상"
        age_guide = "향수/클래식/올드팝 고려, 과도한 강렬함 지양."

    preferred_text = ", ".join(preferred_majors) if preferred_majors else "특이사항 없음"

    # -------- System 지침 --------
    system_instructions = f"""
    너는 한국 사용자를 위한 '일기 감정 분석 + 음악 추천' 전문가다.
    반드시 JSON만 출력한다(텍스트/설명/코드블록 금지).

    사용자 정보:
    - 출생연도: {year}
    - 현재 나이: 약 {age}세 ({age_group})
    - 나이대 가이드: {age_guide}
    - 선호 대분류: {preferred_text}

    정확성:
    - 음악 메타데이터(가수/앨범/장르)가 불확실하면 그 곡을 버리고 신뢰되는 대중적 곡을 선택.
    - 장르는 반드시 '대분류/소분류' 표기(예: pop/pop-ballad, electronic/ambient).
    - 템포는 '느림/중간/빠름 + 대략 BPM'.

    상황 일치(매우 중요):
    - 곡의 '주제/가사/용도'가 일기의 '상황'과 맞아야 한다.
    - 일기에 연애/이별 단서가 없으면 사랑/로맨스/실연 테마 금지.
    - 공부/집중이면 저가사·저에너지 위주, 에너지/운동이면 업비트 허용, 차분/휴식이면 잔잔한 계열 선호.

    선호 대분류(우선, 강제 아님):
    - 감정 점수가 낮거나 중간(score < {PREFERRED_FORCE_THRESHOLD:.2f})이면 가능한 한 선호 대분류에서 선택.
    - 감정 점수가 높으면(≥ {PREFERRED_FORCE_THRESHOLD:.2f}) 선호를 벗어나도 상황/감정 적합성을 우선.

    감지된 컨텍스트: [{contexts_text}]
    {subgenre_hint_text}

    감정 분석:
    - label은 '기쁨/슬픔/화남/무기력/예민' 중 단 하나.
    - 긍정/부정이 섞이면 균형적으로 기술(극단적 어조 금지).
    - score는 [0,1] 실수. 강도가 약하면 0.45~0.65 범위.
    - 구어체 결과를 위해 아래 형식을 '반드시' 채워라.

    reason_parts 작성 규칙(JSON):
    - reason_parts.summary: 한두 문장, 마지막은 반드시 '~했구나'로 끝낼 것. (예: "오늘 하루 종일 과제를 했구나")
    - reason_parts.clues: 일기에서 핵심 단서 1~3개 배열, 각 항목 끝에 마침표/따옴표 금지. (예: ["혼자 랩실에 있었다", "방해받지 않았다"])
    - reason_parts.interpretation: 한 문장, 마지막은 반드시 '…인 것 같아'로 끝낼 것. (예: "외로움과 편안함이 공존하는 상황인 것 같아")

    음악 추천:
    - 항상 2~3곡 후보를 제시한다.
    - 각 곡은 title, artist, album, genre(대분류/소분류), tempo, mood, track_summary, reason을 가진다.
    - track_summary: 곡 자체 한 줄 설명(주제/느낌/용도)
    - music.reason은 '문장만' 작성하며, "일기와의 연결 이유:" 같은 접두사는 절대 붙이지 않는다.
    - 모든 곡은 music_candidates 배열 안의 JSON 객체로 제공한다.
    """

    # -------- User 프롬프트(입력/스키마) --------
    input_json = json.dumps({"text": text, "year": year, "preferred_genres": genres or []}, ensure_ascii=False)

    _output_schema = {
    "emotion": {
        "label": "기쁨/슬픔/화남/무기력/예민 중 하나(단일 라벨)",
        "score": 0.0,
        # 모델은 reason_parts를 채운다. (최종 reason 문자열로 합성)
        "reason_parts": {
            "summary": "…했구나",
            "clues": ["단서1", "단서2"],
            "interpretation": "…인 것 같아"
        }
    },
        "music_candidates": [
            {
                "title": "곡 제목",
                "artist": "가수 이름",
                "album": "앨범명",
                "genre": "대분류/소분류",
                "tempo": "느림/중간/빠름 + 대략 BPM",
                "mood": "곡의 분위기",
                "track_summary": "이 곡 자체 한 줄 설명",
                "reason": "일기와 왜 어울리는지 한두 문장 (접두사 금지)"
            }
        ]
    }

    user_prompt = (
        "[입력]\n"
        + input_json
        + "\n\n[출력 JSON 스키마]\n"
        + json.dumps(_output_schema, ensure_ascii=False, indent=2)
    )

    def _call(messages: List[dict]) -> dict:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},  # JSON만 허용
            temperature=0.25,  # 정확/일관성 우선
            messages=messages,
        )
        content = resp.choices[0].message.content or ""
        return json.loads(content)

    # 1차 생성
    data = _call([
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": user_prompt},
    ])

    # -------- 사후 검증 & 보정(필요 시 1회 재생성) --------
    try:
        # 감정 라벨 정규화
        if "emotion" in data and isinstance(data["emotion"], dict):
            raw_label = data["emotion"].get("label", "")
            normalized = _normalize_emotion_label(raw_label)
            data["emotion"]["label"] = normalized if normalized in _ALLOWED_LABELS else "무기력"

            # reason_parts → reason 합성 (구어체: ~했구나 / …인 것 같아)
            rp = data["emotion"].get("reason_parts")
            if isinstance(rp, dict):
                summary = (rp.get("summary") or "").strip()
                clues   = rp.get("clues") or []
                interp  = (rp.get("interpretation") or "").strip()

                # 방어적 정리
                summary = re.sub(r"[.!?…]+\s*$", "", summary)   # 끝부호 제거 (모델이 붙여도 정규화)
                interp  = re.sub(r"[.!?…]+\s*$", "", interp)
                # 단서 정리: 쉼표로 합치고 불필요한 부호 제거
                clues = [re.sub(r'[\"\'\s]+$', '', str(c).strip()) for c in clues if str(c).strip()]
                clues_text = ", ".join(clues)

                if clues_text:
                    particle = _choose_eul_reul(clues_text)
                    reason = f"{summary}. {clues_text}{particle} 보니 {interp}."
                else:
                    reason = f"{summary}. 그래서 {interp}."
                data["emotion"]["reason"] = reason
                
            # reason 템플릿 강제 변환
            if isinstance(data["emotion"].get("reason"), str):
                data["emotion"]["reason"] = _format_korean_reason_sentence(data["emotion"]["reason"])

        # 감정 점수 파싱
        try:
            score = float(data.get("emotion", {}).get("score", 0.5))
        except Exception:
            score = 0.5

        # === 후보 리스트 정규화/검증 + 레거시 대응 ===
        # 레거시 대응: 모델이 실수로 "music"만 줄 경우 candidates로 승격
        if "music_candidates" not in data and isinstance(data.get("music"), dict):
            data["music_candidates"] = [data["music"]]
            data.pop("music", None)

        candidates = data.get("music_candidates", [])
        if not isinstance(candidates, list):
            candidates = []

        normalized = []
        for c in candidates:
            if not isinstance(c, dict):
                continue
            # 장르 정규화 (항상 main/sub)
            g_raw = c.get("genre", "") or f"{c.get('genre_main','')}/{c.get('genre_sub','')}"
            main, sub, fused = _ensure_major_sub(g_raw, preferred_majors)
            c["genre"] = fused

            # reason 접두사 클린업
            if isinstance(c.get("reason"), str):
                c["reason"] = _clean_reason_text(c["reason"])

            # genre_main/sub 출력 숨김
            c.pop("genre_main", None)
            c.pop("genre_sub", None)

            # 상황 충돌 필터 (연애테마/공부 고BPM 등)
            title = c.get("title", "") or ""
            reason_blob = f"{c.get('reason','')} {c.get('track_summary','')}"
            tempo = c.get("tempo", "") or ""
            conflict, why = _theme_conflict(text, title, reason_blob, c.get("track_summary","") or "", tempo, fused)
            if conflict:
                continue  # 충돌 후보는 버림

            # 선호 대분류 보정 필요? (감정 약할 때)
            prefer_major_fix = (preferred_majors and score < PREFERRED_FORCE_THRESHOLD and main not in preferred_majors)
            if prefer_major_fix:
                # 선호 대분류로 재추론 요청은 재호출 비용이 크니 여기선 소프트 필터만 적용
                # 선호 밖이면 일단 후보에 포함하되, 선호 대분류와 일치하는 후보를 우선 정렬하도록 표식
                c["_prefer_penalty"] = 1  # 선호 밖이면 패널티
            else:
                c["_prefer_penalty"] = 0

            normalized.append(c)

        # 후보가 하나도 안 남으면(너무 빡세게 걸러졌을 때) 원본이라도 사용
        if not normalized and isinstance(candidates, list):
            normalized = candidates
            for c in normalized:
                if isinstance(c, dict):
                    c.pop("genre_main", None)
                    c.pop("genre_sub", None)
                    if isinstance(c.get("reason"), str):
                        c["reason"] = _clean_reason_text(c["reason"])

        # 선호 대분류 패널티 기준으로 정렬(선호 일치 우선)
        normalized.sort(key=lambda x: x.get("_prefer_penalty", 0))
        for c in normalized:
            c.pop("_prefer_penalty", None)

        data["music_candidates"] = normalized[:3]  # 2~3곡 유지(혹시 많이 오면 3개로 컷)

    except Exception:
        # 파싱/검증 중 문제 발생 시 최초 결과 반환(필요하면 로깅)
        pass

    return data
