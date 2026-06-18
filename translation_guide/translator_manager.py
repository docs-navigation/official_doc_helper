# 번역 및 행동 지침 생성 관리 모듈

from typing import Dict, List
from translator import DocTranslator
from action_guide import GuideGenerator
import json

class TranslatorManager:
    def __init__(self):
        self.translator = DocTranslator()
        self.action_guide = GuideGenerator()

    def process_document(self, text: str, doc_type: str) -> Dict:
        # 번역 수행
        translated_text, translation_changes = self.translator.translate_doc(text)
        translated_text = self.translator.simplify_structure(translated_text)

        # 마감일 추출
        deadline = self.action_guide.extract_deadline(text)

        # 긴급도 분석
        urgency = self.action_guide.analyze_urgency(text, deadline)

        # 행동 지침 생성
        actions = self.action_guide.generate_actions(text, doc_type, urgency)

        # 전체 요약 생성
        summary = self.action_guide.create_summary(text, doc_type, urgency, actions)

        # 결과 통합
        result = {
            'original_text': text,
            'translated_text': translated_text,
            'translation': {
                'changes': translation_changes,
                'term_count': len(translation_changes)
            },

            'urgency': {
                'level': urgency['level'],
                'reasons': urgency['reasons'],
                'deadline': deadline.strftime('%Y-%m-%d') if deadline else None
            },

            'actions': actions,
            'summary': summary,
            'document_type': doc_type,
            'metadata': {'data_source': self.translator.add_attribution()}
        }

        return result

    def generate_user_friendly_output(self, result: Dict) -> str:
        output = []

        output.append("=" * 50)
        output.append("문서 분석 결과")
        output.append("=" * 50)
        output.append("")

        # 긴급도
        output.append(f"긴급도: {result['summary']['urgency_label']}")
        output.append(f"{result['summary']['main_message']}")
        output.append("")

        # 마감일
        if result['urgency']['deadline']:
            output.append(f"마감일: {result['urgency']['deadline']}")
            output.append("")

        # 번역된 내용
        output.append("쉬운 설명:")
        output.append("-" * 50)
        output.append(result['translated_text'])
        output.append("")

        # 행동 지침
        output.append("해야 할 일:")
        output.append("-" * 50)
        for i, action in enumerate(result['actions'], 1):
            output.append(f"{i}. {action['action']}")
            output.append(f"   → {action['detail']}")
            output.append("")

        # 도움 연락처
        output.append("도움받을 곳:")
        output.append("-" * 50)
        for contact in result['summary']['help_contacts']:
            output.append(f"• {contact['name']}: {contact['number']}")
            output.append(f"  ({contact['desc']})")
        output.append("")

        output.append("=" * 50)

        return "\n".join(output)
