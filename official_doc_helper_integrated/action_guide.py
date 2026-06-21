# 행동 지침 분석 모듈

from typing import Dict, List, Union, Optional
from datetime import datetime, timedelta
import re

class GuideGenerator:
    # 행동 지침 생성
    def generate_guide(self, classified_doc: Union[Dict, str], doc_type: str = "일반 문서") -> Dict:
        if isinstance(classified_doc, str):
            doc = {
                "ocr_text": classified_doc,
                "extracted_info": {
                    "doc_type": doc_type
                },
                "severity": {
                    "level": "일반",
                    "reason": []
                }
            }
        else:
            doc = classified_doc or {}

        text = doc.get("ocr_text", "")
        extracted_info = doc.get("extracted_info") or {}
        severity = doc.get("severity") or {}

        level = severity.get("level", "일반")
        reasons = severity.get("reason", [])

        deadline = extracted_info.get("deadline")
        detected_doc_type = (
            extracted_info.get("doc_type")
            or doc.get("document_type")
            or doc_type
            or "일반 문서"
        )

        # 카테고리 분류
        category = self._detect_category(detected_doc_type, text)

        # 행동 지침 생성
        actions = self._generate_actions(
            category = category,
            level = level,
            deadline = deadline,
            doc_type = detected_doc_type,
            text = text
        )

        # 도움 연락처 제공
        help_contacts = self._get_help_contacts(category)

        return {
            "urgency_level": level,
            "urgency_label": self._level_to_label(level),
            "deadline": deadline,
            "doc_type": detected_doc_type,
            "document_type": detected_doc_type,
            "category": category,
            "reasons": reasons,
            "main_message": self._create_main_message(
                level=level,
                doc_type=detected_doc_type,
                deadline=deadline
            ),
            "actions": actions,
            "help_contacts": help_contacts
        }
    
    def _level_to_label(self, level: str) -> str:
        label_map = {
            "심각": "매우 긴급",
            "경고": "긴급",
            "주의": "주의",
            "일반": "일반"
        }

        return label_map.get(level, level)

    def _detect_category(self, doc_type: str, text: str) -> str:
        doc_type = doc_type or ""
        text = text or ""
        combined = doc_type + " " + text

        real_estate_keywords = [
            "임대차", "전세", "월세", "보증금", "임대인", "임차인",
            "계약해지", "계약만료", "부동산", "등기부", "등기사항",
            "근저당", "전입신고", "확정일자", "원상복구", "하자"
        ]

        court_keywords = [
            "소장", "답변서", "출석", "출두", "소환", "변론기일",
            "판결", "지급명령", "보정명령", "공소장", "고소장", "고발장",
            "구속영장", "체포영장", "강제집행", "압류", "가압류",
            "경매", "추심명령", "전부명령", "약식명령"
        ]

        tax_keywords = [
            "세금", "납세", "납부", "고지서", "체납", "독촉",
            "재산세", "종합소득세", "부가가치세", "지방세", "국세",
            "과태료", "범칙금", "가산금", "가산세", "건강보험료",
            "국민연금", "관리비"
        ]

        if any(keyword in combined for keyword in real_estate_keywords):
            return "real_estate"

        if any(keyword in combined for keyword in court_keywords):
            return "court"

        if any(keyword in combined for keyword in tax_keywords):
            return "tax"

        return "general"

    # 행동 지침 생성
    def _generate_actions(self, category: str, level: str, deadline: str, doc_type: str, text: str) -> List[Dict]:
        urgency_dict = {'level': level, 'deadline': deadline}

        if category == "tax":
            return self._generate_tax_actions(text, urgency_dict)
        elif category == "court":
            return self._generate_court_actions(text, urgency_dict)
        elif category == "real_estate":
            return self._generate_real_estate_actions(text, urgency_dict)
        else:
            return self._generate_general_actions(text, urgency_dict)

    # 세금 관련 행동 지침
    def _generate_tax_actions(self, text: str, urgency: Dict) -> List[Dict]:
        actions = []

        actions.append({
            'priority': 1,
            'action': '문서 내용 확인',
            'detail': '세금 종류, 금액, 납부 기한을 확인하세요.'
        })

        # 납부 관련
        if '납부' in text:
            actions.append({
                'priority': 2,
                'action': '납부 방법 확인',
                'detail': '은행, ATM, 인터넷뱅킹, 위택스(wetax.go.kr)에서 납부할 수 있습니다.'
            })

            if urgency['level'] in ['심각', '경고']:
                actions.append({
                    'priority': 3,
                    'action': '즉시 납부 또는 분할납부 신청',
                    'detail': '한 번에 내기 어려우면 관할 세무서에 전화해서 분할납부를 신청하세요.'
                })

        # 이의신청 관련
        if '이의신청' in text:
            actions.append({
                'priority': 4,
                'action': '이의신청 검토',
                'detail': '세금이 잘못 계산되었다고 생각되면 문서에 적힌 이의신청 기간을 확인하고, 기한 안에 신청하세요.'
            })

        return actions
    
    # 법원 관련 행동 지침
    def _generate_court_actions(self, text: str, urgency: Dict) -> List[Dict]:
        actions = []

        actions.append({
            'priority': 1,
            'action': '법률 상담 받기',
            'detail': '가까운 법률구조공단(132) 또는 대한법률구조공단에 무료 상담을 신청하세요.'
        })

        if '답변서' in text:
            actions.append({
                'priority': 2,
                'action': '답변서 작성 및 제출',
                'detail': '법원에 당신의 입장을 설명하는 답변서를 제출하세요. 변호사 도움을 받는 것이 좋습니다.'
            })

        if '출석' in text or '출두' in text:
            actions.append({
                'priority': 2,
                'action': '법정 출석 준비',
                'detail': '지정된 날짜에 법원에 출석하세요. 관련 서류를 모두 준비하세요.'
            })

        if urgency['level'] == '심각':
            actions.append({
                'priority': 1,
                'action': '긴급 대응 필요',
                'detail': '즉시 법률 전문가와 상담하세요. 시간이 매우 중요합니다.'
            })

        return actions

    # 부동산 관련 행동 지침
    def _generate_real_estate_actions(self, text: str, urgency: Dict) -> List[Dict]:
        actions = []

        actions.append({
            'priority': 1,
            'action': '계약서 확인',
            'detail': '원본 계약서를 찾아서 내용을 비교하세요.'
        })

        if '보증금' in text:
            actions.append({
                'priority': 2,
                'action': '보증금 관련 확인',
                'detail': '보증금 반환 시기와 조건을 확인하세요.'
            })

        if '명도' in text or '퇴거' in text:
            actions.append({
                'priority': 1,
                'action': '긴급 상담 필요',
                'detail': '즉시 부동산 전문 변호사나 주거복지센터(1600-0777)에 상담하세요.'
            })

        return actions

    def _generate_general_actions(self, text: str, urgency: Dict) -> List[Dict]:
        actions = [
            {
                'priority': 1,
                'action': '문서 내용 이해',
                'detail': '중요한 내용을 천천히 읽고 이해하세요.'
            },
            {
                'priority': 2,
                'action': '관련 기관 문의',
                'detail': '문서 발송 기관에 전화해서 자세한 설명을 요청하세요.'
            }
        ]

        if urgency['deadline']:
            deadline_val = urgency['deadline']
            actions.insert(1, {
                'priority': 1,
                'action': '마감일 확인',
                'detail': f"마감일: {deadline_val}까지 필요한 조치를 완료하세요."
            })

        return actions
    
    def _create_main_message(self, level: str, doc_type: str, deadline: str) -> str:
        deadline_text = f" 기한은 {deadline}입니다." if deadline else ""

        if level == "심각":
            return f"{doc_type} 문서입니다.{deadline_text} 법적 조치나 불이익 가능성이 있으니 즉시 확인해야 합니다."

        if level == "경고":
            return f"{doc_type} 문서입니다.{deadline_text} 빠른 확인과 대응이 필요합니다."

        if level == "주의":
            return f"{doc_type} 문서입니다.{deadline_text} 기한과 요구사항을 확인해야 합니다."

        return f"{doc_type} 문서입니다.{deadline_text} 내용을 확인하고 필요한 경우 보관하세요."

    def _get_help_contacts(self, category: str) -> List[Dict]:
        common_contacts = [
            {"name": "정부민원안내콜센터", "number": "110", "desc": "일반 민원 상담"}
        ]

        if category == "tax":
            return common_contacts + [{"name": "국세상담센터", "number": "126", "desc": "세금 관련 상담"}]

        if category == "court":
            return common_contacts + [{"name": "대한법률구조공단", "number": "132", "desc": "법률 상담"}]

        if category == "real_estate":
            return common_contacts + [{"name": "법률상담", "number": "132", "desc": "임대차, 보증금, 계약 분쟁 상담"}]

        return common_contacts