# 번역 및 행동 지침 생성 관리 모듈

from typing import Dict, List
from translator import DocTranslator
from action_guide import GuideGenerator

class TranslatorManager:
    def __init__(self):
        self.translator = DocTranslator()
        self.action_guide = GuideGenerator()

    def process_document(self, doc: Dict) -> Dict:
         # doc은 OCR -> 심각도 분류를 거친 결과 (ocr_text, extracted_info, severity 포함)
        text = doc.get("ocr_text", "")
        extracted_info = doc.get("extracted_info") or {}
        severity = doc.get("severity") or {}
        deadline = extracted_info.get("deadline")

        detected_doc_type = (
            extracted_info.get("doc_type")
            or doc.get("document_type")
            or "일반 문서"
        )
        
        # 번역 수행
        translated_text, translation_changes = self.translator.translate_doc(text)

        if hasattr(self.translator, "simplify_structure"):
            translated_text = self.translator.simplify_structure(translated_text)

        

        # 행동 지침 생성
        guide_result = self.action_guide.generate_guide(
            doc,
            doc_type=detected_doc_type
        )

        actions = guide_result.get("actions", [])

        # 결과 통합
        result = {
            "original_text": text,
            "ocr_text": text,
            "translated_text": translated_text,
            "translation": {
                "changes": translation_changes,
                "term_count": len(translation_changes)
            },

            "extracted_info": extracted_info,
            "severity": severity,
            "urgency": {
                "level": severity.get("level", "일반"),
                "label": guide_result.get("urgency_label", severity.get("level", "일반")),
                "reasons": severity.get("reason", []),
                "deadline": deadline
            },
            "actions": actions,
            "summary": {
                "urgency_label": guide_result.get("urgency_label", severity.get("level", "일반")),
                "main_message": guide_result.get("main_message", "문서 내용을 확인하세요."),
                "help_contacts": guide_result.get("help_contacts", [])
            },
            "document_type": detected_doc_type,
            "metadata": {"data_source": "Public Document Analysis System v1.0"}
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
        output.append(f"요약: {result['summary']['main_message']}")
        output.append("")

        # 마감일
        deadline = result['urgency']['deadline']
        if deadline:
            output.append(f"마감일: {deadline}")
        else:
            output.append("마감일: 확인된 기한 없음 (원문 재확인 권장)")
        output.append("")

        # 번역된 내용
        output.append("쉬운 설명:")
        output.append("-" * 50)
        output.append(result['translated_text'])
        output.append("")

        # 행동 지침
        actions = result.get('actions', [])
        output.append("해야 할 일:")
        output.append("-" * 50)
        if actions:
            for i, action in enumerate(actions, 1):
                output.append(f"{i}. {action['action']}")
                output.append(f"   → {action['detail']}")
        else:
            output.append("특이사항이 없습니다.")
        output.append("")

        # 도움 연락처
        contacts = result['summary'].get('help_contacts', [])
        if contacts:
            output.append("도움받을 곳")
            output.append("-" * 50)
            for contact in contacts:
                output.append(f"• {contact['name']}: {contact['number']} ({contact['desc']})")
            output.append("")

        output.append("=" * 50)

        return "\n".join(output)