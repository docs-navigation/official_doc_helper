# ocr_pipeline.py
# 문서 인식 및 추출 모듈 (OCR) — 공문서 번역/가이드 시스템의 정식 OCR
#
# 책임: 업로드 파일(이미지/PDF)에서 텍스트를 뽑아 doc 딕셔너리로 돌려준다.
#       분류/번역은 하지 않는다(다음 모듈 담당). 통합 앱은 run_ocr 하나만 부르면 된다.

import os
import re
import cv2
import numpy as np
import easyocr
import torch
from ultralytics import YOLO

# ---- 설정값 (코드에 숫자 박지 않고 여기 모음) ----
YOLO_WEIGHTS_PATH = os.environ.get("OCR_YOLO_WEIGHTS", "best.pt")
OCR_LANGS = ["ko", "en"]

MIN_CHARS = 20              # 추출 글자가 이보다 적으면 거의 못 읽음
MIN_KOREAN_CHARS = 30       # 한글(2자 이상) 합이 이보다 적으면 본문 인식 실패로 봄
MIN_MEAN_CONF = 0.45        # EasyOCR 평균 신뢰도가 이보다 낮으면 인식 불량
DIGITAL_PDF_MIN_CHARS = 30  # 텍스트 레이어가 이 정도면 전자 PDF로 보고 OCR 생략
RENDER_DPI = 200

_PDF_MAGIC = b"%PDF"
_model = None
_reader = None


def _resolve_weights():
    for p in [YOLO_WEIGHTS_PATH, "runs/detect/train/weights/best.pt"]:
        if os.path.exists(p):
            return p
    return YOLO_WEIGHTS_PATH  # 없으면 YOLO가 명확한 에러를 내도록 그대로 전달


def _get_model():
    global _model
    if _model is None:
        _model = YOLO(_resolve_weights())
    return _model


def _get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(OCR_LANGS, gpu=torch.cuda.is_available())
    return _reader


def _read_bytes(uploaded_file):
    # Streamlit UploadedFile / 파일객체 / 경로 / bytes 무엇이 와도 (bytes, 파일명)으로 통일
    if hasattr(uploaded_file, "getvalue"):
        return uploaded_file.getvalue(), getattr(uploaded_file, "name", "")
    if hasattr(uploaded_file, "read"):
        return uploaded_file.read(), getattr(uploaded_file, "name", "")
    if isinstance(uploaded_file, str):
        with open(uploaded_file, "rb") as f:
            return f.read(), uploaded_file
    if isinstance(uploaded_file, (bytes, bytearray)):
        return bytes(uploaded_file), ""
    raise TypeError("지원하지 않는 입력 형식입니다.")


def _ocr_array(img_bgr):
    # 신뢰도를 받으려고 paragraph=False
    reader = _get_reader()
    results = reader.readtext(img_bgr, paragraph=False)  # [(bbox, text, conf), ...]
    text = "\n".join(r[1] for r in results)
    confs = [float(r[2]) for r in results]
    return text, confs


def _ocr_image(file_bytes):
    # 촬영 이미지: YOLO로 종이 영역을 찾아 크롭한 뒤 OCR
    arr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return "", [], "image"
    res = _get_model()(img)[0]
    if len(res.boxes) == 0:
        crop = img  # 종이를 못 찾으면 원본 전체로 시도
    else:
        b = res.boxes[res.boxes.conf.argmax()].xyxy[0].cpu().numpy().astype(int)
        x1, y1, x2, y2 = b
        crop = img[y1:y2, x1:x2]
    text, confs = _ocr_array(crop)
    return text, confs, "image"


def _ocr_pdf(file_bytes):
    import fitz  # PyMuPDF
    pdf = fitz.open(stream=file_bytes, filetype="pdf")
    layer = "\n".join(p.get_text() for p in pdf).strip()
    if len(layer) >= DIGITAL_PDF_MIN_CHARS:          # 전자 PDF: 텍스트 레이어 바로 사용
        return layer, [1.0], "pdf"
    texts, confs = [], []                             # 스캔 PDF: 렌더링 후 OCR
    for p in pdf:
        pix = p.get_pixmap(dpi=RENDER_DPI)
        arr = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)
        bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR if pix.n == 4 else cv2.COLOR_RGB2BGR)
        t, c = _ocr_array(bgr)
        texts.append(t); confs.extend(c)
    return "\n".join(texts), confs, "pdf"


def _assess_quality(text, confs):
    korean = sum(len(w) for w in re.findall(r"[가-힣]{2,}", text))
    mean_conf = sum(confs) / len(confs) if confs else 0.0
    if len(text.strip()) < MIN_CHARS or korean < MIN_KOREAN_CHARS:
        return True, "글자를 거의 인식하지 못했어요. 문서가 꽉 차도록 다시 찍어주세요."
    if mean_conf < MIN_MEAN_CONF:
        return True, "글자 인식 정확도가 낮아요. 흔들림 없이 밝은 곳에서 다시 찍어주세요."
    return False, ""


def run_ocr(uploaded_file, doc_id="uploaded"):
    """
    통합 앱이 호출하는 단일 진입점.
    이미지/PDF를 받아 OCR 결과 doc을 돌려준다. 파일은 메모리에서만 처리 후 폐기.
    needs_recapture가 True면 뒤 모듈을 돌리지 말고 recapture_reason을 사용자에게 보여주면 된다.
    """
    file_bytes, filename = _read_bytes(uploaded_file)
    try:
        is_pdf = filename.lower().endswith(".pdf") or file_bytes[:4] == _PDF_MAGIC
        if is_pdf:
            text, confs, input_type = _ocr_pdf(file_bytes)
        else:
            text, confs, input_type = _ocr_image(file_bytes)

        needs_recapture, reason = _assess_quality(text, confs)
        return {
            "doc_id": doc_id,
            "input_type": input_type,
            "ocr_text": text,
            "extracted_info": {},
            "severity": {},
            "easy_summary": "",
            "action_guide": [],
            "needs_recapture": needs_recapture,
            "recapture_reason": reason,
        }
    finally:
        del file_bytes  # 민감 문서 폐기
