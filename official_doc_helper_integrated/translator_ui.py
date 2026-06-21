import json
import streamlit as st


def render_translation_page(result: dict):
    main_color = "#0054A3"
    
    st.markdown(
        f"""
        <style>
        /* 카테고리 공통 제목 */
        .category-header {{
            font-size: 28px !important;
            font-weight: 800 !important;
            color: #31343F;
            margin-top: 30px !important;
            margin-bottom: 15px !important;
            display: flex;
            align-items: center;
        }}

        div[data-testid="stTextArea"] textarea {{
            font-size: 16px !important;
            line-height: 1.6 !important;
            font-weight: 380 !important;
            color: #222222 !important;
        }}

        /* 용어 변경 */
        .term-box {{
            padding: 20px;
            border-radius: 14px;
            border: 1px solid #e0e0e0;
            background-color: #ffffff;
            margin-bottom: 12px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.03);
        }}
        .term-text {{
            font-size: 22px;
            font-weight: 700;
            color: #222222;
        }}
        .term-count {{
            font-size: 16px;
            color: #666666;
            margin-top: 5px;
        }}
        .arrow {{
            color: black;
            margin: 0 10px;
            font-weight: 900;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.header("공문서 번역 결과")

    original_text = result.get("ocr_text") or result.get("original_text", "")
    translated_text = result.get("translated_text", "")

    # 원문 및 번역 결과 비교
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f'<div class="category-header">원본 내용</div>', unsafe_allow_html=True)
        st.text_area(
            label="OCR 원문",
            value=original_text,
            height=400,
            label_visibility="collapsed"
        )

    with col2:
        st.markdown(f'<div class="category-header">쉬운 설명</div>', unsafe_allow_html=True)
        st.text_area(
            label="쉬운 설명",
            value=translated_text,
            height=400,
            label_visibility="collapsed"
        )

    st.divider()

    # 바뀐 용어
    st.markdown(f'<div class="category-header">변환된 용어 정리</div>', unsafe_allow_html=True)

    changes = (
        result.get("translation", {}).get("changes")
        or result.get("translation_changes")
        or []
    )

    if changes:
        for change in changes:
            original = change.get("original", "")
            simplified = change.get("simplified", "")
            count = change.get("count", 1)

            st.markdown(
                f"""
                <div class="term-box">
                    <div class="term-text">
                        <span>{original}</span>
                        <span class="arrow">→</span>
                        <span style="color: {main_color};">{simplified}</span>
                    </div>
                    <div class="term-count">본문 내 등장 횟수: {count}회</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("변환된 어려운 용어가 없습니다.")


def render_finish_page(result: dict):
    main_color = "#0054A3"
    st.markdown(
        f"""
        <style>
        /* 카테고리 공통 제목 */
        .category-header {{
            font-size: 28px !important;
            font-weight: 700 !important;
            color: #31343F;
            margin-top: 40px !important;
            margin-bottom: 20px !important;
            display: flex;
            align-items: center;
        }}

        .info-label {{
            font-size: 28px;
            color: #666666;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        .info-value {{
            font-size: 28px;
            font-weight: 500;
            color: #111111;
            margin-bottom: 20px;
        }}

        /* 해야 할 일 */
        .action-box {{
            padding: 24px;
            border-radius: 14px;
            border: 1px solid #e0e0e0;
            background-color: #ffffff;
            margin-bottom: 16px;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.03);
        }}
        .action-title {{
            font-size: 26px;
            font-weight: 780;
            margin-bottom: 10px;
            color: black;
        }}
        .action-detail {{
            font-size: 16px;
            font-weight: 430;
            color: #444444;
            color: {main_color};
            line-height: 1.6;
        }}

        /* 다운로드 버튼 */
        div[data-testid="stDownloadButton"] {{
            display: flex;
            justify-content:center;
        }} 
        
        div[data-testid="stDownloadButton"] > button {{
            width: 100% !important;
            max-width: 500px !important;
            height: 70px !important;
            font-size: 24px !important;
            font-weight: 700 !important;
            color: white !important;
            background-color: {main_color} !important;
            border: none !important;
            border-radius: 12px !important;
            transition: all 0.3s ease;
        }}
        
        div[data-testid="stDownloadButton"] > button:hover {{
            background-color: #003E77 !important;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}

        div[data-testid="stDownloadButton"] > button p {{
            font-size: 16px !important;
            font-weight: 450 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.header("최종 분석 결과")

    # 데이터 추출
    urgency = result.get("urgency", {})
    summary = result.get("summary", {})
    urgency_level = urgency.get("level", "알 수 없음")
    deadline = urgency.get("deadline") or summary.get("deadline") or "없음"
    document_type = result.get("document_type", "일반 문서")
    main_message = result.get("main_message") or summary.get("main_message") or "내용이 없습니다."

    # 상단 정보
    st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f'<p class="info-label">긴급도</p><p class="info-value">{urgency_level}</p>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<p class="info-label">마감일</p><p class="info-value">{deadline}</p>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<p class="info-label">문서 유형</p><p class="info-value">{document_type}</p>', unsafe_allow_html=True)

    st.divider()

    # 주요 내용 요약
    st.markdown(f'<div class="category-header">주요 내용 요약</div>', unsafe_allow_html=True)
    st.info(main_message)
    st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)
    st.divider()

    # 해야 할 일
    st.markdown(f'<div class="category-header">해야 할 일</div>', unsafe_allow_html=True)
    actions = result.get("actions", [])
    if actions:
        for idx, action in enumerate(actions, start=1):
            st.markdown(f"""
                <div class="action-box">
                    <div class="action-title">{idx}. {action.get("action", "")}</div>
                    <div class="action-detail">{action.get("detail", "")}</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("생성된 실천 지침이 없습니다.")

    st.divider()

    # 도움받을 곳
    st.markdown(f'<div class="category-header">문의 및 도움</div>', unsafe_allow_html=True)
    contacts = result.get("help_contacts") or summary.get("help_contacts") or []
    if contacts:
        for contact in contacts:
            st.write(f"- **{contact.get('name', '')}**: {contact.get('number', '')} ({contact.get('desc', '')})")
    else:
        st.info("연락처 정보가 없습니다.")

    st.divider()

    # 분석 결과 저장
    st.markdown('<div style="margin-top: 60px;"></div>', unsafe_allow_html=True)
    
    result_json = json.dumps(result, ensure_ascii=False, indent=2)

    left_col, center_col, right_col = st.columns([1.5, 2, 1.5])
    
    with center_col:
        st.download_button(
            label="분석 결과 다운로드 (JSON 파일)",
            data=result_json,
            file_name="analysis_result.json",
            mime="application/json",
            use_container_width=True
        )