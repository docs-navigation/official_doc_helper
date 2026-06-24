# 핵심 정보 추출 모듈 (deadline, doc_type 추출)

import re
from datetime import date

from constants import DOC_TYPE_LEVELS, LEVEL_ORDER


# 기한 주변에서 자주 등장하는 표현
DEADLINE_CONTEXT_KEYWORDS = [
    "납부기한", "제출기한", "신청기한", "답변서 제출기한",
    "기한", "마감", "만료일", "납부일", "제출일",
    "출석일", "출두일", "소환일", "변론기일",
    "까지", "내에", "이내"
]


# 발급일, 작성일 등 기한이 아닐 가능성이 높은 표현
NON_DEADLINE_KEYWORDS = ["발급일", "작성일", "시행일", "접수일", "고지일", "통지일"]


# 문서명이 OCR에서 정확히 잡히지 않을 때 보완하기 위한 키워드
FALLBACK_DOC_TYPE_KEYWORDS = {
    "압류예고통지서": ["압류예고", "압류 예정", "재산압류", "급여압류", "통장압류"],
    "체납고지서": ["체납", "체납액", "장기체납", "고액체납"],
    "강제집행통지서": ["강제집행"],
    "경매개시결정문": ["경매개시", "경매 개시"],
    "고소장": ["고소장"],
    "고발장": ["고발장"],
    "구속영장": ["구속영장"],
    "체포영장": ["체포영장"],

    "독촉장": ["독촉", "납부독촉", "납부 독촉", "최고서"],
    "과태료고지서": ["과태료"],
    "범칙금고지서": ["범칙금"],
    "출석요구서": ["출석요구", "출석 요구", "출두요구"],
    "소환장": ["소환"],
    "소장": ["민사소송", "소송 제기"],
    "답변서요청": ["답변서"],

    "납부고지서": ["납부고지", "납부 고지", "납부기한", "납부금액"],
    "세금고지서": ["세금", "과세", "납세", "지방세"],
    "재산세고지서": ["재산세"],
    "종합소득세고지서": ["종합소득세"],
    "부가가치세고지서": ["부가가치세"],
    "시정명령서": ["시정명령", "시정 명령"],
    "경고장": ["경고장"],

    "임대차계약서": ["임대인", "임차인", "보증금", "월세", "전세금"],
    "계약해지통보서": ["계약해지", "계약 해지", "해지통보", "해지 통보"],
    "계약만료통보": ["계약만료", "계약 만료", "만기"],

    "공소장": ["공소장", "공소제기"],
    "추심명령서": ["추심명령"],
    "전부명령서": ["전부명령"],
    "채권압류통지서": ["채권압류"],
    "약식명령서": ["약식명령"],
    "과징금부과통지서": ["과징금"],
    "이행권고결정서": ["이행권고"],
    "변론기일통지서": ["변론기일통지", "변론기일"],
    "보정명령서": ["보정명령"],

    "납세고지서": ["납세고지", "납세 고지"],
    "건강보험료고지서": ["건강보험료"],
    "국민연금고지서": ["국민연금"],
    "관리비고지서": ["관리비"],
    "전세계약서": ["전세계약", "전세 계약"],
    "등기부등본": ["등기부등본", "등기사항전부증명"],

    "안내문": ["안내", "알림"],
    "공지사항": ["공지"],
}


# OCR 결과 텍스트 정리
def clean_text(text):
    if not text:
        return ""

    text = str(text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# 키워드 비교용 문자열 정규화 (OCR 결과의 중간 공백이나 특수문자를 제거)
def _compact(text):
    if not text:
        return ""

    return re.sub(
        r"[\s\-_·ㆍ:：,./()\[\]{}<>「」『』'\"“”‘’]",
        "",
        text
    )


# 올바른 날짜인지 확인 후 date 객체로 변환, 잘못된 날짜면 None(ex: 2026-13-40)
def _safe_date(year, month, day):
    try:
        return date(year, month, day)
    except ValueError:
        return None


# 찾은 날짜 주변 문맥으로 실제 기한일 가능성을 점수화(점수가 양수여야 기한 후보로 인정)
def _deadline_score(text, start, end):
    context = text[max(0, start - 35): min(len(text), end + 35)]

    score = 0

    for keyword in DEADLINE_CONTEXT_KEYWORDS:
        if keyword in context:
            score += 10

    for keyword in NON_DEADLINE_KEYWORDS:
        if keyword in context:
            score -= 5

    return score


# 기한 후보들을 우선순위에 따라 정렬하기 위한 기준값
def _deadline_priority(candidate):
    score = candidate[0]
    deadline = candidate[1]

    is_future = deadline >= date.today()

    return (
        -score,                 # 1순위: 문맥 점수가 높을수록 먼저 (음수로 뒤집음)
        0 if is_future else 1,  # 2순위: 미래(0)를 과거(1)보다 먼저
        deadline,               # 3순위: 더 이른 날짜를 먼저
    )


# OCR 텍스트에서 납부/제출 기한으로 보이는 날짜 추출 (반환 형식: YYYY-MM-DD)
def extract_deadline(text):
    text = clean_text(text)

    if not text:
        return None

    candidates = []

    # 1. YYYY년 M월 DD일
    pattern_ymd_korean = r"(20\d{2})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일?"
    for match in re.finditer(pattern_ymd_korean, text):
        year, month, day = map(int, match.groups())
        parsed_date = _safe_date(year, month, day)

        if parsed_date:
            score = _deadline_score(text, match.start(), match.end())
            candidates.append((score, parsed_date))

    # 2. YYYY.MM.DD / YYYY-MM-DD / YYYY/MM/DD
    pattern_ymd_symbol = r"(20\d{2})\s*[.\-/]\s*(\d{1,2})\s*[.\-/]\s*(\d{1,2})"
    for match in re.finditer(pattern_ymd_symbol, text):
        year, month, day = map(int, match.groups())
        parsed_date = _safe_date(year, month, day)

        if parsed_date:
            score = _deadline_score(text, match.start(), match.end())
            candidates.append((score, parsed_date))

    # 3. YYYYMMDD
    pattern_ymd_compact = r"(20\d{2})(\d{2})(\d{2})"
    for match in re.finditer(pattern_ymd_compact, text):
        year, month, day = map(int, match.groups())
        parsed_date = _safe_date(year, month, day)

        if parsed_date:
            score = _deadline_score(text, match.start(), match.end())
            candidates.append((score, parsed_date))

    # 4. 연도가 없는 경우 -> 현재 연도를 사용
    pattern_md_korean = r"(\d{1,2})\s*월\s*(\d{1,2})\s*일"
    for match in re.finditer(pattern_md_korean, text):
        before_text = text[max(0, match.start() - 6):match.start()]

        if "년" in before_text:
            continue
    
        month, day = map(int, match.groups())
        parsed_date = _safe_date(date.today().year, month, day)

        if parsed_date:
            score = _deadline_score(text, match.start(), match.end())
            candidates.append((score, parsed_date))

    if not candidates:
        return None

    # 기한 문맥(납부기한, 까지 등)이 있는 날짜만 기한으로 인정
    positive_candidates = [
        candidate for candidate in candidates
        if candidate[0] > 0
    ]

    if not positive_candidates:
        return None

    # 위 기준(_deadline_priority)에 따라 정렬한 뒤 가장 우선순위 높은 날짜를 선택
    positive_candidates.sort(key=_deadline_priority)
    best_candidate = positive_candidates[0]
    return best_candidate[1].isoformat()


# 심각도 단계 인덱스 반환 (심각 0, 경고 1, 주의 2, 일반 3)
def _get_doc_type_level(doc_type):
    for index, level in enumerate(LEVEL_ORDER):
        if doc_type in DOC_TYPE_LEVELS.get(level, []):
            return index

    return len(LEVEL_ORDER)


# OCR 텍스트에서 문서 종류를 추출하거나 추정
def extract_doc_type(text):
    text = clean_text(text)

    if not text:
        return None

    # 문서 제목은 보통 상단에 있으므로 앞부분을 우선 검사
    title_area = text[:250]
    compact_title_area = _compact(title_area)

    matched_doc_types = []

    # 1. 문서 상단 영역에서 정확한 문서명 우선 탐색
    for level in LEVEL_ORDER:
        for doc_type in DOC_TYPE_LEVELS.get(level, []):
            compact_doc_type = _compact(doc_type)

            if compact_doc_type and compact_doc_type in compact_title_area:
                matched_doc_types.append(doc_type)

    if matched_doc_types:
        matched_doc_types.sort(
            key=lambda doc_type: (
                _get_doc_type_level(doc_type),
                -len(_compact(doc_type))
            )
        )
        return matched_doc_types[0]

    # 2. 정확한 문서명이 없으면 fallback 키워드로 문서 종류 추정
    compact_text = _compact(text)
    fallback_matches = []

    for doc_type, keywords in FALLBACK_DOC_TYPE_KEYWORDS.items():
        for keyword in keywords:
            if _compact(keyword) in compact_text:
                fallback_matches.append(doc_type)
                break

    if fallback_matches:
        fallback_matches.sort(
            key=lambda doc_type: (
                _get_doc_type_level(doc_type),
                -len(_compact(doc_type))
            )
        )
        return fallback_matches[0]

    return None


# OCR 텍스트에서 심각도 분류에 필요한 핵심 정보 추출
# 반환 구조: {"deadline": "YYYY-MM-DD", "doc_type": "문서종류"}
def extract_info(text):
    cleaned_text = clean_text(text)

    return {
        "deadline": extract_deadline(cleaned_text),
        "doc_type": extract_doc_type(cleaned_text)
    }