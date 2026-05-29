# 분류 기준 정의

# 기준 1: 제출 및 납부 기한
DEADLINE_RULES = [
    (7,  "심각", "납부 기한 {days}일 남음 — 즉각 대응 필요"),
    (14, "경고", "납부 기한 {days}일 남음 — 빠른 확인 필요"),
    (30, "주의", "납부 기한 {days}일 남음 — 확인 필요"),
]

# 기준 2: 법적 효력
LEGAL_FORCE_KEYWORDS = {
    "심각": ["강제집행", "압류", "고소", "고발", "형사처벌", "구속"],
    "경고": ["과태료", "이행강제금", "법적 조치", "소송"],
    "주의": ["시정명령", "행정처분", "경고장"],
}

# 기준 3: 문서 종류
DOC_TYPE_LEVELS = {
    "심각": ["체납고지서", "압류통지서", "강제집행통지서", "고소장"],
    "경고": ["독촉장", "납부독촉", "과태료고지서", "소송안내"],
    "주의": ["세금고지서", "납부고지서", "행정처분사전통지"],
    "일반": ["안내문", "홍보문", "공지사항"],
}

# 기준 4: 중요 키워드
IMPORTANT_KEYWORDS = {
    "심각": ["체납", "즉시", "긴급", "최후통보"],
    "경고": ["미납", "연체", "독촉", "기한 내"],
    "주의": ["납부", "제출", "신청", "확인 요망"],
}

LEVEL_ORDER = ["심각", "경고", "주의", "일반"]

def _higher(a: str, b: str) -> str:
    """두 심각도 중 더 높은 단계를 반환."""
    return a if LEVEL_ORDER.index(a) <= LEVEL_ORDER.index(b) else b


def classify_severity(doc: dict) -> dict:
    # 4가지 기준을 각각 평가 -> 가장 높은 단계를 최종 심각도로 결정

    text  = doc["ocr_text"]
    info  = doc["extracted_info"]
    level = "일반"
    reasons = []

    # 기준 1: 제출 및 납부 기한
    deadline_str = info.get("deadline")
    if deadline_str:
        days_left = (date.fromisoformat(deadline_str) - date.today()).days
        if days_left < 0:
            level = _higher(level, "심각")
            reasons.append(f"납부 기한 {abs(days_left)}일 초과 - 즉각 대응 필요")
        else:
            for threshold, sev, msg in DEADLINE_RULES:
                if days_left <= threshold:
                    level = _higher(level, sev)
                    reasons.append(msg.format(days=days_left))
                    break

    # 기준 2: 법적 효력
    for sev, keywords in LEGAL_FORCE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                level = _higher(level, sev)
                reasons.append(f"법적 효력 키워드 감지: '{kw}'")

    # 기준 3: 문서 종류
    doc_type = info.get("doc_type", "")
    for sev, types in DOC_TYPE_LEVELS.items():
        if doc_type in types:
            level = _higher(level, sev)
            reasons.append(f"문서 종류: {doc_type}")
            break

    # 기준 4: 중요 키워드
    for sev, keywords in IMPORTANT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                level = _higher(level, sev)
                reasons.append(f"중요 키워드 감지: '{kw}'")

    if not reasons:
        reasons.append("특이사항 없음 - 일반 안내 문서")

    return {**doc, "severity": {"level": level, "reason": reasons}}