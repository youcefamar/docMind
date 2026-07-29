import logging

from services.logging_filters import SuccessfulPollingAccessLogFilter


def access_record(method: str, path: str, status_code: int) -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %s',
        args=("127.0.0.1:54321", method, path, "1.1", status_code),
        exc_info=None,
    )


def test_successful_polling_access_logs_are_hidden():
    log_filter = SuccessfulPollingAccessLogFilter()

    assert log_filter.filter(access_record("GET", "/api/docs", 200)) is False
    assert log_filter.filter(access_record("GET", "/api/sources/status?refresh=1", 200)) is False
    assert log_filter.filter(access_record("GET", "/api/runtime/status", 304)) is False


def test_errors_and_non_polling_access_logs_remain_visible():
    log_filter = SuccessfulPollingAccessLogFilter()

    assert log_filter.filter(access_record("GET", "/api/docs", 500)) is True
    assert log_filter.filter(access_record("POST", "/api/sources/sync", 202)) is True
    assert log_filter.filter(access_record("GET", "/docs", 200)) is True
