from ultralytics import YOLO
import easyocr
import cv2
import numpy as np
from translator_manager import TranslatorManager
import json
import os
import argparse
from pathlib import Path


class TranslationSystem:
    def __init__(self, yolo_model_path='models/best.pt'):
        print("=" * 70)
        print("공문서 분석 시스템 초기화")
        print("=" * 70)

        print("\n[1/3] YOLO 문서 검출 모델 로드 중")
        if not os.path.exists(yolo_model_path):
            if os.path.exists(yolo_model_path):
                self.yolo_model = YOLO(yolo_model_path)
                print(f"문서 검출용 YOLO 모델 로드 완료: {yolo_model_path}")
            else:
                print("문서 검출용 best.pt가 없습니다. 기본 YOLO 모델을 사용합니다.")
                self.yolo_model = YOLO("yolo11n.pt")

        print("\n[2/3] EasyOCR 초기화 중")
        self.ocr_reader = easyocr.Reader(['ko', 'en'], gpu=False) # CUDA 세팅된 경우 gpu=True로 변경
        print("EasyOCR 초기화 완료")

        # 3. 번역/행동지침 모듈 (당신 모듈)
        print("\n[3/3] 번역 및 행동지침 모듈 로드 중")
        self.translator_manager = TranslatorManager()
        print("TranslatorManager 로드 완료")

        print("\n" + "=" * 70)
        print("시스템 초기화 완료")
        print("=" * 70 + "\n")

    def process_single_image(self, image_path, doc_type='general', save_output=True):
        print(f"\n{'='*70}")
        print(f"📄 처리 중: {os.path.basename(image_path)}")
        print(f"{'='*70}")

        # 이미지 로드
        print("\n[1/5] 이미지 로드 중")
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"이미지를 불러올 수 없습니다: {image_path}")
        print(f"이미지 크기: {img.shape[1]}x{img.shape[0]}")

        # YOLO로 paper 영역 검출
        print("\n[2/5] YOLO 문서 영역 검출 중")
        yolo_results = self.yolo_model(image_path)[0]

        if len(yolo_results.boxes) == 0:
            print("문서 영역 미검출 - 원본 이미지 사용")
            crop = img
            detection_info = {"detected": False}
        else:
            # 가장 신뢰도 높은 박스 선택
            best_box_idx = yolo_results.boxes.conf.argmax()
            box = yolo_results.boxes[best_box_idx].xyxy[0].cpu().numpy().astype(int)
            x1, y1, x2, y2 = box
            crop = img[y1:y2, x1:x2]
            confidence = float(yolo_results.boxes[best_box_idx].conf)

            detection_info = {
                "detected": True,
                "confidence": confidence,
                "bbox": [int(x1), int(y1), int(x2), int(y2)]
            }
            print(f"문서 영역 검출 (신뢰도: {confidence:.3f})")
            print(f"위치: x1={x1}, y1={y1}, x2={x2}, y2={y2}")

        # EasyOCR로 텍스트 추출
        print("\n[3/5] OCR 텍스트 추출 중")
        ocr_results = self.ocr_reader.readtext(crop, paragraph=True)
        ocr_text = "\n".join([result[1] for result in ocr_results])

        if not ocr_text.strip():
            print("텍스트를 추출할 수 없습니다")
            ocr_text = "[텍스트 추출 실패]"
        else:
            print(f"텍스트 추출 완료 (총 {len(ocr_text)}자)")
            # 첫 50자 미리보기
            preview = ocr_text[:50].replace('\n', ' ')

        # 문서 유형 자동 판별
        print("\n[4/5] 문서 분석 중")
        if doc_type == 'general':
            doc_type = self.classify_doc_type(ocr_text)
            print(f"문서 유형 자동 판별: {doc_type}")
        else:
            print(f"문서 유형: {doc_type} (수동 지정)")

        # 번역 및 행동 지침 생성
        print("번역 및 행동지침 생성 중")
        analysis = self.translator_manager.process_document(ocr_text, doc_type)
        print(f"분석 완료")
        print(f"    - 긴급도: {analysis['urgency']['level']}")
        print(f"    - 번역된 용어: {analysis['translation']['term_count']}개")
        print(f"    - 행동 지침: {len(analysis['actions'])}개")

        print("\n[5/5] 결과 통합 중")
        final_result = {
            'doc_id': Path(image_path).stem,
            'input_type': 'image',
            'image_path': image_path,
            'detection_info': detection_info,
            'ocr_text': ocr_text,
            'document_type': doc_type,
            'translated_text': analysis['translated_text'],
            'translation': analysis['translation'],
            'urgency': analysis['urgency'],
            'actions': analysis['actions'],
            'summary': analysis['summary'],
            'metadata': analysis.get('metadata', {})
        }

        # 결과 저장
        if save_output:
            output_file = f"output_{final_result['doc_id']}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_result, f, ensure_ascii=False, indent=2)
            print(f"결과 저장: {output_file}")

        return final_result

    def classify_doc_type(self, text):
        text_lower = text.lower()

        # 세금 관련 키워드
        tax_keywords = ['세금', '납부', '과세', '징수', '지방세', '재산세', '자동차세', '고지서', '체납', '가산', '과세표준', '연체', '미납', '완납', '결손처분']
        if any(keyword in text_lower for keyword in tax_keywords):
            return 'tax'

        # 법원 관련 키워드
        court_keywords = ['법원', '소장', '채권', '채무', '원고', '피고', '피의자', '원고', '판결', '송달', '답변서', '변론', '출석', '압류', '경매',
                          '원고', '피고', '기일', '답변서', '이의신청', '판결', '결정', '이행', '강제집행', '소멸시효']
        if any(keyword in text_lower for keyword in court_keywords):
            return 'court'

        # 부동산 관련 키워드
        real_estate_keywords = ['등기', '소유권', '임대차', '계약', '보증금', '명도', '임대인', '임차인', '월세', '전세', '관리비']
        if any(keyword in text_lower for keyword in real_estate_keywords):
            return 'real_estate'
        
        else:
            return 'general'

    def process_batch(self, image_dir, output_dir='batch_output', doc_type='general'):
        # 출력 폴더 생성
        os.makedirs(output_dir, exist_ok=True)

        # 이미지 파일 찾기
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']
        image_files = []
        for ext in image_extensions:
            image_files.extend(Path(image_dir).glob(ext))

        total = len(image_files)
        print(f"\n{'='*70}")
        print(f"배치 처리 시작: 총 {total}개 이미지")
        print(f"{'='*70}")

        results = []
        success_count = 0

        for i, image_path in enumerate(image_files, 1):
            print(f"\n\n{'#'*70}")
            print(f"진행률: [{i}/{total}] ({i/total*100:.1f}%)")
            print(f"{'#'*70}")

            try:
                result = self.process_single_image(
                    str(image_path), 
                    doc_type=doc_type,
                    save_output=False
                )
                results.append(result)
                success_count += 1

                # 개별 결과 저장
                output_file = os.path.join(output_dir, f"{result['doc_id']}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)

                print(f"\n성공: {output_file}")

            except Exception as e:
                print(f"\n오류 발생: {e}")
                results.append({
                    'doc_id': image_path.stem,
                    'error': str(e),
                    'image_path': str(image_path)
                })
                continue

        # 전체 결과 요약 저장
        summary_file = os.path.join(output_dir, '_batch_summary.json')
        summary = {
            'total': total,
            'success': success_count,
            'failed': total - success_count,
            'results': results
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n\n{'='*70}")
        print(f"배치 처리 완료")
        print(f"{'='*70}")
        print(f"총 {total}개 중 {success_count}개 성공 ({success_count/total*100:.1f}%)")
        print(f"실패: {total - success_count}개")
        print(f"\n전체 요약: {summary_file}")
        print(f"개별 결과: {output_dir}/")
        print(f"{'='*70}\n")

        return results

    def print_result(self, result):
        if 'error' in result:
            print(f"\n처리 실패: {result['error']}")
            return

        output = self.translator_manager.generate_user_friendly_output(result)
        print("\n" + output)


def main():
    parser = argparse.ArgumentParser(
        description='공문서 OCR 및 번역 시스템',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--image', type=str, 
                       help='단일 이미지 경로')
    parser.add_argument('--batch', type=str, 
                       help='이미지 폴더 경로 (배치 처리)')
    parser.add_argument('--model', type=str, default='models/best.pt',
                       help='YOLO 모델 경로 (기본: models/best.pt)')
    parser.add_argument('--type', type=str, default='general',
                       choices=['tax', 'court', 'real_estate', 'general'],
                       help='문서 유형 (기본: 자동 판별)')
    parser.add_argument('--output', type=str, default='batch_output',
                       help='배치 처리 결과 저장 폴더 (기본: batch_output)')

    args = parser.parse_args()

    # 시스템 초기화
    try:
        system = TranslationSystem(yolo_model_path=args.model)
    except FileNotFoundError as e:
        print(f"\n오류 발생: {e}")
        return
    except Exception as e:
        print(f"\n초기화 실패: {e}")
        print("\n필수 라이브러리 설치:")
        print("  pip install ultralytics easyocr opencv-python")
        return

    # 인자 확인
    if not args.image and not args.batch:
        parser.print_help()
        print("\n--image 또는 --batch 중 하나를 지정하세요")
        return

    # 단일 이미지 처리
    if args.image:
        if not os.path.exists(args.image):
            print(f"\n이미지 파일을 찾을 수 없습니다: {args.image}")
            return

        result = system.process_single_image(args.image, doc_type=args.type)
        system.print_result(result)

    # 배치 처리
    elif args.batch:
        if not os.path.isdir(args.batch):
            print(f"\n폴더를 찾을 수 없습니다: {args.batch}")
            return

        system.process_batch(args.batch, output_dir=args.output, doc_type=args.type)


if __name__ == "__main__":
    main()
