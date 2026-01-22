import logging


def configure_logging(level: str) -> None:
    """애플리케이션 로깅을 설정

    Args:
        level: 로깅 레벨 문자열
    """

    class _SafeFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            if not hasattr(record, "event"):
                record.event = "system"
            if not hasattr(record, "hospital_id"):
                record.hospital_id = "-"
            if not hasattr(record, "stage"):
                record.stage = "-"
            return super().format(record)

    handler = logging.StreamHandler()
    handler.setFormatter(
        _SafeFormatter(
            "%(asctime)s %(levelname)s %(name)s "
            "event=%(event)s hospital_id=%(hospital_id)s "
            "stage=%(stage)s %(message)s"
        )
    )

    logging.basicConfig(level=level.upper(), handlers=[handler])
