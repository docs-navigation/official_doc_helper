# 통합 UI - 전체 파이프라인 흐름
# 문서 인식 및 추출 모듈(OCR) -> 심각도 분류 모듈 -> 번역 및 행동지침 모듈

import streamlit as st
from classification_manager import ClassificationManager
from translator_manager import TranslatorManager
from translator_ui import render_translation_page, render_finish_page

st.set_page_config(page_title="공문서 쉽게 보기", layout="wide")

main_color = "#0054A3"

# 심각도별 강조 색
SEVERITY_COLORS = {
    "심각": "#C0392B",
    "경고": "#E67E22",
    "주의": "#D4A017",
    "일반": "#0054A3"
}

# 공통 스타일
st.markdown(
    """
    <style>
    .app-title {
        font-size: 42px;
        font-weight: 800;
        color: #31343F;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .category-header {
        font-size: 28px;
        font-weight: 800;
        color: #31343F;
        margin-top: 30px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
    }
    .app-card {
        padding: 24px;
        border-radius: 14px;
        border: 1px solid #e0e0e0;
        background-color: #ffffff;
        margin-bottom: 16px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.03);
    }
    .info-label {
        font-size: 16px;
        color: #666666;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .info-value {
        font-size: 22px;
        font-weight: 500;
        color: #111111;
    }
    .sev-badge {
        display: inline-block;
        padding: 10px 24px;
        border-radius: 12px;
        color: #ffffff;
        font-size: 26px;
        font-weight: 800;
    }
    .reason-item {
        font-size: 16px;
        color: #444444;
        line-height: 1.7;
        margin-bottom: 6px;
    }
    div[data-testid="stTextArea"] textarea {
        font-size: 16px !important;
        line-height: 1.6 !important;
        font-weight: 380 !important;
        color: #222222 !important;
    }
    div[data-testid="stButton"] > button {
        border-radius: 12px !important;
        height: 52px !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        border: 1px solid #0054A3 !important;
        color: #0054A3 !important;
        background-color: #ffffff !important;
        transition: all 0.2s ease;
    }
    div[data-testid="stButton"] > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    div[data-testid="stButton"] > button[kind="primary"],
    button[data-testid="stBaseButton-primary"] {
        background-color: #0054A3 !important;
        color: #ffffff !important;
        border: none !important;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {
        background-color: #003E77 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# OCR 모듈 연결 지점
# 실제 OCR 모듈의 full_pipeline로 교체. 지금은 OCR 연결 전 레이아웃 테스트용 샘플 doc 반환
def run_ocr(uploaded_file):
    # TODO: 실제 OCR 모듈 연결
    #   from ocr_pipeline import full_pipeline
    #   path = save_temp(uploaded_file)
    #   return full_pipeline(path)
    return {
        "doc_id": "uploaded",
        "input_type": "image",
        "ocr_text": (
            "재산세 납부 고지서\n"
            "귀하의 재산세가 체납되었습니다. "
            "기한 내 미납 시 압류 등 강제집행이 진행될 수 있습니다.\n"
            "납부기한: 2026년 7월 15일"
        ),
        "extracted_info": {},
        "severity": {},
        "easy_summary": "",
        "action_guide": {}
    }


# 전체 파이프라인 실행 
def run_pipeline(uploaded_file):
    # 1. OCR 모듈
    doc = run_ocr(uploaded_file)
    # 2. 심각도 분류 모듈
    doc = ClassificationManager().process(doc)
    # 3. 번역/행동지침 모듈
    result = TranslatorManager().process_document(doc)
    return doc, result


# 세션 상태 초기화
if "doc" not in st.session_state:
    st.session_state.doc = None
    st.session_state.result = None


st.markdown('<div class="app-title">공문서 번역 및 가이드 시스템</div>', unsafe_allow_html=True)

st.markdown('<div class="category-header">문서 올리기</div>', unsafe_allow_html=True)
uploaded = st.file_uploader("공문서 이미지를 올려주세요", type=["png", "jpg", "jpeg"])

col_run, col_reset = st.columns([1, 1])
with col_run:
    if st.button("분석 시작", type="primary", disabled=uploaded is None, use_container_width=True):
        with st.spinner("문서를 분석하고 있어요..."):
            doc, result = run_pipeline(uploaded)
            st.session_state.doc = doc
            st.session_state.result = result
with col_reset:
    if st.button("다시 하기", use_container_width=True):
        st.session_state.doc = None
        st.session_state.result = None

# 결과가 있으면 단계별 페이지 표시
if st.session_state.result:
    doc = st.session_state.doc
    result = st.session_state.result

    st.divider()
    page = st.radio(
        "단계",
        ["1. 문서 인식", "2. 심각도 분류", "3. 번역 결과", "4. 행동 지침"],
        horizontal=True
    )
    st.divider()

    # 1. 문서 인식 결과
    if page == "1. 문서 인식":
        st.header("문서 인식 결과")
        info = doc.get("extracted_info", {})

        c1, c2 = st.columns(2)
        with c1:
            doc_type_val = info.get("doc_type") or "확인 안 됨"
            st.markdown(
                f'<div class="app-card"><div class="info-label">문서 종류</div>'
                f'<div class="info-value">{doc_type_val}</div></div>',
                unsafe_allow_html=True
            )
        with c2:
            deadline_val = info.get("deadline") or "확인 안 됨"
            st.markdown(
                f'<div class="app-card"><div class="info-label">기한</div>'
                f'<div class="info-value">{deadline_val}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown('<div class="category-header">추출된 원문</div>', unsafe_allow_html=True)
        st.text_area(
            "원문",
            value=doc.get("ocr_text", ""),
            height=360,
            label_visibility="collapsed"
        )

    # 2. 심각도 분류 결과
    elif page == "2. 심각도 분류":
        st.header("심각도 분류 결과")
        severity = doc.get("severity", {})
        level = severity.get("level", "일반")
        color = SEVERITY_COLORS.get(level, "#0054A3")

        st.markdown('<div class="category-header">이 문서가 얼마나 급한가요?</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="app-card"><span class="sev-badge" '
            f'style="background-color:{color};">{level}</span></div>',
            unsafe_allow_html=True
        )

        st.markdown('<div class="category-header">판단 이유</div>', unsafe_allow_html=True)
        reasons = severity.get("reason", [])
        if reasons:
            reason_html = "".join(f'<div class="reason-item">• {r}</div>' for r in reasons)
        else:
            reason_html = '<div class="reason-item">• 특이사항 없음</div>'
        st.markdown(f'<div class="app-card">{reason_html}</div>', unsafe_allow_html=True)

    # 3. 번역 결과 
    elif page == "3. 번역 결과":
        render_translation_page(result)

    # 4. 행동 지침 
    else:
        render_finish_page(result)