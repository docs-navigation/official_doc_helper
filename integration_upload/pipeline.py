# 통합 파이프라인: OCR -> 심각도 분류 -> 번역/행동지침
# 호출하는 쪽은 run_pipeline(파일) 하나만 쓰면 됨.

import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(HERE, "severity_classfication"))
sys.path.append(os.path.join(HERE, "translation_guide"))

from ocr_pipeline import run_ocr
from classification_manager import ClassificationManager
from translator_manager import TranslatorManager


def run_pipeline(uploaded_file, doc_id="doc_001"):
    # 1. OCR (메모리 처리 + 재촬영 판단)
    doc = run_ocr(uploaded_file, doc_id)
    if doc["needs_recapture"]:
        return doc, None                       # 깨진 문서는 여기서 멈춤

    # 2. 심각도 분류
    doc = ClassificationManager().process(doc)

    # 3. 번역/행동지침
    result = TranslatorManager().process_document(doc["ocr_text"], "general")
    doc["severity"]       = result["severity"]
    doc["extracted_info"] = result["extracted_info"]
    doc["easy_summary"]   = result["summary"]["main_message"]
    doc["action_guide"]   = [a["action"] for a in result["actions"]]
    return doc, result
