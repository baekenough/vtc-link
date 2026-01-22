class PipelineError(Exception):
    """파이프라인 예외의 기본 클래스"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ParseError(PipelineError):
    """파싱 또는 정규화 실패 시 발생"""

    def __init__(self, field: str, message: str) -> None:
        super().__init__("TX_PARSE_001", f"{field}: {message}")
