# 심각도 분류 로직

from datetime import date

from constants import (
    LEVEL_ORDER,
    DEADLINE_RULES,
    LEGAL_FORCE_KEYWORDS,
    DOC_TYPE_LEVELS,
    IMPORTANT_KEYWORDS,
)


# 두 심각도 중 더 높은 단계 반환
def _higher(a, b):
    return a if LEVEL_ORDER.index(a) <= LEVEL_ORDER.index(b) else b


# 키워드 탐색
def _check_keywords(text, keyword_map, label):
    found_level = "일반"
    reasons = []

    for sev in LEVEL_ORDER[:-1]:
        keywords = keyword_map.get(sev, [])

        matched = [
            keyword
            for keyword in keywords
            if keyword in text
        ]

        if matched:
            found_level = _higher(found_level, sev)
            reasons.append(f"{label} 감지 ({sev}): {', '.join(matched)}")

            # 심각 단계가 감지되면 최고 단계이므로 조기 종료
            if found_level == "심각":
                break

    return found_level, reasons


# deadline 문자열 기준 심각도 판단
def _check_deadline(deadline_str):
    level = "일반"
    reasons = []

    if not deadline_str:
        return level, reasons

    try:
        deadline = date.fromisoformat(deadline_str)
        days_left = (deadline - date.today()).days

        if days_left < 0:
            level = _higher(level, "심각")
            reasons.append(f"납부/제출 기한 {abs(days_left)}일 초과 - 즉각 대응 필요")

        else:
            for threshold, sev, msg in DEADLINE_RULES:
                if days_left <= threshold:
                    level = _higher(level, sev)

                    if "{days}" in msg:
                        reasons.append(msg.format(days=days_left))
                    else:
                        reasons.append(msg)

                    break

    except ValueError:
        reasons.append("기한 형식이 올바르지 않아 날짜 기준 분류를 건너뜀")

    return level, reasons


# 문서 종류 기준 심각도 판단
def _check_doc_type(doc_type):
    level = "일반"
    reasons = []

    if not doc_type:
        return level, reasons

    for sev, types in DOC_TYPE_LEVELS.items():
        if any(doc_type == t or t in doc_type for t in types):
            level = _higher(level, sev)
            reasons.append(f"문서 종류: {doc_type}")
            break

    return level, reasons


# 문서의 심각도를 분류하여 반환
def classify_severity(doc):
    text = doc.get("ocr_text", "")
    info = doc.get("extracted_info", {})

    level = "일반"
    reasons = []

    # 기준 1: 제출 및 납부 기한
    deadline_str = info.get("deadline")
    deadline_level, deadline_reasons = _check_deadline(deadline_str)

    level = _higher(level, deadline_level)
    reasons.extend(deadline_reasons)

    # 기준 2: 법적 효력 키워드
    legal_level, legal_reasons = _check_keywords(
        text=text,
        keyword_map=LEGAL_FORCE_KEYWORDS,
        label="법적 효력 키워드"
    )

    level = _higher(level, legal_level)
    reasons.extend(legal_reasons)

    # 기준 3: 문서 종류
    doc_type = info.get("doc_type", "")
    doc_type_level, doc_type_reasons = _check_doc_type(doc_type)

    level = _higher(level, doc_type_level)
    reasons.extend(doc_type_reasons)

    # 기준 4: 중요 키워드
    important_level, important_reasons = _check_keywords(
        text=text,
        keyword_map=IMPORTANT_KEYWORDS,
        label="중요 키워드"
    )

    level = _higher(level, important_level)
    reasons.extend(important_reasons)

    # 판단 근거가 없을 경우 기본 사유 추가
    if not reasons:
        reasons.append("특이사항 없음 - 일반 안내 문서")

    # 중복 reason 제거
    reasons = list(dict.fromkeys(reasons))

    return {
        **doc,
        "severity": {
            "level": level,
            "reason": reasons
        }
    }