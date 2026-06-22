# 심각도 분류 관리 모듈

from classifier import classify_severity
from info_extractor import extract_info, clean_text


# 외부에서 호출하는 진입점
class ClassificationManager:

    def process(self, doc):
        text = doc.get("ocr_text", "")
        cleaned_text = clean_text(text)

        existing_info = doc.get("extracted_info") or {}
        extracted_info = extract_info(cleaned_text)

        # 기존 정보 유지, 새로 추출된 값이 None이 아닐 때만 덮어씀
        merged_info = {
            **existing_info,
            **{key: value for key, value in extracted_info.items() if value is not None}
        }

        # 업데이트된 복사본을 만들어 분류기에 전달
        updated_doc = {
            **doc,
            "ocr_text": cleaned_text,
            "extracted_info": merged_info,
        }
        return classify_severity(updated_doc)

    # 심각도 레벨 문자열 반환
    def get_level(self, doc):
        result = self.process(doc)
        return result["severity"]["level"]

    # 심각도 판단 근거 리스트 반환
    def get_reasons(self, doc):
        result = self.process(doc)
        return result["severity"]["reason"]