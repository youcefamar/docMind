"""Logging helpers that keep terminal output focused on user actions."""

from __future__ import annotations

import logging


class SuccessfulPollingAccessLogFilter(logging.Filter):
    """Hide successful UI polling requests from Uvicorn's access logger.

    The Knowledge Base polls a few read-only endpoints while a document is
    processing. Those requests are useful to the browser but bury the actual
    extraction and embedding progress in the terminal. Failed responses and
    every non-polling request remain visible.
    """

    polling_paths = frozenset(
        {
            "/api/docs",
            "/api/runtime/status",
            "/api/sources/status",
        }
    )

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if not isinstance(args, tuple) or len(args) < 5:
            return True

        _client, method, path, _http_version, status_code = args[:5]
        try:
            is_success = 200 <= int(status_code) < 400
        except (TypeError, ValueError):
            return True

        is_polling_request = (
            str(method).upper() == "GET"
            and str(path).split("?", maxsplit=1)[0] in self.polling_paths
        )
        return not (is_success and is_polling_request)


def configure_uvicorn_access_logs() -> None:
    """Attach the polling filter once when the FastAPI application is imported."""

    access_logger = logging.getLogger("uvicorn.access")
    if any(isinstance(item, SuccessfulPollingAccessLogFilter) for item in access_logger.filters):
        return
    access_logger.addFilter(SuccessfulPollingAccessLogFilter())
