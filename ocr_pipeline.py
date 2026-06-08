# ================================================
# 3단계: 학습된 모델 + EasyOCR 연결
# 흐린 사진 → 복원 → OCR → JSON 출력
# ================================================

# ── 셀 1: 패키지 설치 ──
!pip install easyocr pdf2image pillow torch torchvision opencv-python-headless -q
!apt-get install -y poppler-utils -q

# ── 셀 2: 라이브러리 import ──
import torch
import torch.nn as nn
import easyocr
import json
import uuid
import os
import numpy as np
from PIL import Image
from torchvision import transforms
from pdf2image import convert_from_path
from pathlib import Path

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── 셀 3: 모델 구조 정의 (step2와 동일해야 해요) ──
class DeblurNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(3, 64, 3, padding=1), nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
            nn.Conv2d(64, 128, 3, stride=2, padding=1), nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1), nn.ReLU(),
            nn.Conv2d(128, 256, 3, stride=2, padding=1), nn.ReLU(),
        )
        self.middle = nn.Sequential(
            nn.Conv2d(256, 256, 3, padding=1), nn.ReLU(),
            nn.Conv2d(256, 256, 3, padding=1), nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(256, 128, 4, stride=2, padding=1), nn.ReLU(),
            nn.Conv2d(128, 128, 3, padding=1), nn.ReLU(),
            nn.ConvTranspose2d(128, 64, 4, stride=2, padding=1), nn.ReLU(),
            nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(),
            nn.Conv2d(64, 3, 3, padding=1),
            nn.Sigmoid()
        )

    def forward(self, x):
        x = self.encoder(x)
        x = self.middle(x)
        x = self.decoder(x)
        return x

# ── 셀 4: 학습된 모델 불러오기 ──
# 방법 A: 코랩에 저장되어 있는 경우
deblur_model = DeblurNet().to(DEVICE)
deblur_model.load_state_dict(torch.load("deblur_model.pth", map_location=DEVICE))
deblur_model.eval()
print("복원 모델 로드 완료!")

# 방법 B: 내 PC에서 업로드하는 경우 (위 코드 대신 사용)
# from google.colab import files
# uploaded = files.upload()  # deblur_model.pth 업로드
# deblur_model = DeblurNet().to(DEVICE)
# deblur_model.load_state_dict(torch.load("deblur_model.pth", map_location=DEVICE))
# deblur_model.eval()

# ── 셀 5: EasyOCR 초기화 ──
print("OCR 모델 로딩 중...")
ocr_reader = easyocr.Reader(['ko', 'en'])
print("OCR 모델 로딩 완료!")

# ── 셀 6: 이미지 복원 함수 ──
def restore_image(image_path: str) -> Image.Image:
    """흐린 이미지를 학습된 모델로 선명하게 복원"""
    original = Image.open(image_path).convert("RGB")
    original_size = original.size  # 원래 크기 저장

    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
    ])

    input_tensor = transform(original).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        output_tensor = deblur_model(input_tensor).squeeze(0).cpu()

    # 원래 크기로 복원
    output_img = transforms.ToPILImage()(output_tensor)
    output_img = output_img.resize(original_size, Image.LANCZOS)
    return output_img

# ── 셀 7: OCR 함수 ──
def extract_text(image: Image.Image) -> str:
    """PIL 이미지에서 텍스트 추출"""
    img_array = np.array(image)
    results = ocr_reader.readtext(img_array)
    text = "\n".join([r[1] for r in results])
    return text.strip()

# ── 셀 8: 전체 파이프라인 (핵심 함수) ──
def run_ocr(file_path: str) -> dict:
    """
    흐린 사진 또는 PDF를 받아서:
    1. 복원 모델로 선명하게 만들고
    2. EasyOCR로 텍스트 추출
    3. 공통 JSON 형식으로 반환

    Args:
        file_path: 이미지(JPG, PNG) 또는 PDF 파일 경로

    Returns:
        공통 JSON 형식 딕셔너리
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없어요: {file_path}")

    extension = path.suffix.lower()

    if extension == ".pdf":
        input_type = "pdf"
        print("PDF → 이미지 변환 중...")
        pages = convert_from_path(file_path, dpi=200)
        all_text = []
        for i, page in enumerate(pages):
            print(f"  {i+1}/{len(pages)} 페이지 복원 + OCR 중...")
            temp_path = f"_temp_page_{i}.jpg"
            page.save(temp_path)
            restored = restore_image(temp_path)
            text = extract_text(restored)
            if text:
                all_text.append(text)
            os.remove(temp_path)
        ocr_text = "\n".join(all_text).strip()

    elif extension in [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]:
        input_type = "image"
        print("이미지 복원 중...")
        restored = restore_image(file_path)
        print("OCR 추출 중...")
        ocr_text = extract_text(restored)

    else:
        raise ValueError(f"지원하지 않는 파일 형식: {extension}")

    result = {
        "doc_id": f"doc_{uuid.uuid4().hex[:6]}",
        "input_type": input_type,
        "ocr_text": ocr_text,
        # 다음 모듈에서 채울 부분
        "extracted_info": {},
        "severity": {},
        "easy_summary": "",
        "action_guide": []
    }

    print("완료!")
    return result

# ── 셀 9: 실행 ──
from google.colab import files

print("파일을 업로드하세요 (이미지 또는 PDF)")
uploaded = files.upload()
file_name = list(uploaded.keys())[0]

result = run_ocr(file_name)

print("\n===== 결과 =====")
print(json.dumps(result, ensure_ascii=False, indent=2))

# ── 셀 10 (선택): JSON 파일로 저장 & 다운로드 ──
# with open("ocr_result.json", "w", encoding="utf-8") as f:
#     json.dump(result, f, ensure_ascii=False, indent=2)
# files.download("ocr_result.json")
