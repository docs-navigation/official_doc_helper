# 심각도 분류 관리 모듈

from classifier import classify_severity


# 외부에서 호출하는 진입점
class ClassificationManager:

    def process(self, doc):
        return classify_severity(doc)

    # 심각도 레벨 문자열 반환
    def get_level(self, doc):
        result = self.process(doc)
        return result["severity"]["level"]

    # 심각도 판단 근거 리스트 반환
    def get_reasons(self, doc):
        result = self.process(doc)
        return result["severity"]["reason"]