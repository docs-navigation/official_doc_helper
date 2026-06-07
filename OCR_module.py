from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='korean')

result = ocr.ocr("test.jpg")

for line in result[0]:
    print(line[1][0])