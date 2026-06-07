# 행동 지침 분석 모듈

from typing import Dict, List
from datetime import datetime, timedelta
import re

class GuideGenerator:
    def __init__(self):
        # 긴급도 키워드
        self.urgency_keywords = {
            'critical': ['압류', '경매', '강제집행', '명도', '퇴거', '출석', '출두'],
            'high': ['납부기한', '답변서', '이의신청', '체납', '독촉'],
            'medium': ['고지', '통지', '안내', '계약'],
            'low': ['확인', '조회', '참고']
        }

        # 문서 유형별 행동 템플릿
        self.action_templates = {
            'tax': self._generate_tax_actions,
            'court': self._generate_court_actions,
            'real_estate': self._generate_real_estate_actions,
            'general': self._generate_general_actions
        }

    # 행동 지침 생성
    def generate_guide(self, text: str, doc_type: str = "general") -> Dict:
        deadline = self.extract_deadline(text)
        urgency = self.analyze_urgency(text, deadline)
        actions = self.generate_actions(text, doc_type, urgency)
        summary = self.create_summary(text, doc_type, urgency, actions)

        return summary

    def analyze_urgency(self, text: str, deadline: datetime = None) -> Dict:
        urgency_level = 'low'
        reasons = []

        # 키워드 기반 긴급도 판단
        for level, keywords in self.urgency_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    if level == 'critical':
                        urgency_level = 'critical'
                        reasons.append(f'"{keyword}" 발견 - 즉시 대응 필요')
                    elif level == 'high' and urgency_level != 'critical':
                        urgency_level = 'high'
                        reasons.append(f'"{keyword}" 발견 - 빠른 대응 필요')
                    elif level == 'medium' and urgency_level == 'low':
                        urgency_level = 'medium'
                        reasons.append(f'"{keyword}" 발견')

        # 마감일 기반 긴급도 조정
        if deadline:
            days_left = (deadline - datetime.now()).days
            if days_left <= 3:
                urgency_level = 'critical'
                reasons.append(f'마감까지 {days_left}일 남음')
            elif days_left <= 7:
                if urgency_level not in ['critical']:
                    urgency_level = 'high'
                reasons.append(f'마감까지 {days_left}일 남음')
            elif days_left < 0:
                urgency_level = 'critical'
                reasons.append('마감일이 이미 지남')

        return {
            'level': urgency_level,
            'reasons': reasons,
            'deadline': deadline
        }

    def extract_deadline(self, text: str) -> datetime:
        # 날짜 패턴 매칭
        date_patterns = [
            r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{4})\.(\d{2})\.(\d{2})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                year, month, day = map(int, match.groups())
                try:
                    return datetime(year, month, day)
                except ValueError:
                    continue

        return None

    def generate_actions(self, text: str, doc_type: str, urgency: Dict) -> List[Dict]:
        generator = self.action_templates.get(doc_type, self._generate_general_actions)
        return generator(text, urgency)

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

            if urgency['level'] in ['critical', 'high']:
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

        if urgency['level'] == 'critical':
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
            actions.insert(1, {
                'priority': 1,
                'action': '마감일 확인',
                'detail': f"마감일: {urgency['deadline'].strftime('%Y년 %m월 %d일')}"
            })

        return actions

    def create_summary(self, text: str, doc_type: str, urgency: Dict, actions: List[Dict]) -> Dict:
        urgency_labels = {
            'critical': '🚨 매우 긴급',
            'high': '⚠️ 긴급',
            'medium': '📌 보통',
            'low': 'ℹ️ 참고'
        }

        return {
            'urgency_label': urgency_labels[urgency['level']],
            'urgency_level': urgency['level'],
            'main_message': self._get_main_message(doc_type, urgency['level']),
            'deadline': urgency['deadline'],
            'actions': sorted(actions, key=lambda x: x['priority']),
            'help_contacts': self._get_help_contacts(doc_type)
        }

    def _get_main_message(self, doc_type: str, urgency_level: str) -> str:
        messages = {
            'tax': {
                'critical': '세금을 즉시 납부하거나 분할납부를 신청해야 합니다.',
                'high': '세금 납부 기한이 얼마 남지 않았습니다.',
                'medium': '세금 납부 관련 안내입니다.',
                'low': '세금 관련 안내 사항입니다.'
            },

            'court': {
                'critical': '법적 조치가 임박했습니다. 즉시 법률 상담을 받으세요.',
                'high': '법원 문서입니다. 빠른 대응이 필요합니다.',
                'medium': '법원에서 보낸 통지입니다.',
                'low': '법원 관련 안내 사항입니다.'
            },

            'real_estate': {
                'critical': '부동산 계약 관련 긴급 사항입니다.',
                'high': '부동산 계약 관련 중요 통지입니다.',
                'medium': '부동산 계약 안내입니다.',
                'low': '부동산 관련 안내 사항입니다.'
            },

            'general': {
                'critical': '기한이 지났거나 빠른 대응이 필요한 문서입니다.',
                'high': '빠른 확인이 필요한 행정 문서입니다.',
                'medium': '확인이 필요한 행정 문서입니다.',
                'low': '일반 행정 문서입니다.'
            }
        }

        return messages.get(doc_type, {}).get(urgency_level, '문서를 확인하세요.')

    def _get_help_contacts(self, doc_type: str) -> List[Dict]:
        common = [
            {'name': '정부민원콜센터', 'number': '110', 'desc': '정부 관련 모든 민원 상담'}
        ]

        specific = {
            'tax': [
                {'name': '국세상담센터', 'number': '126', 'desc': '세금 관련 상담'},
                {'name': '위택스', 'number': '1544-1414', 'desc': '지방세 납부 및 상담'}
            ],
            'court': [
                {'name': '법률구조공단', 'number': '132', 'desc': '무료 법률 상담'},
                {'name': '대한법률구조공단', 'number': '1600-5050', 'desc': '법률 지원'}
            ],
            'real_estate': [
                {'name': '주거복지센터', 'number': '1600-0777', 'desc': '주거 관련 상담'},
                {'name': '부동산거래관리시스템', 'number': '1588-0149', 'desc': '부동산 거래 상담'}
            ]
        }

        return common + specific.get(doc_type, [])
