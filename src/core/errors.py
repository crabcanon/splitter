from __future__ import annotations


class SplitterError(Exception):
    code = "INTERNAL_ERROR"
    status_code = 500

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class InvalidRequestError(SplitterError):
    code = "INVALID_REQUEST"
    status_code = 400


class UnsupportedStrategyError(SplitterError):
    code = "UNSUPPORTED_STRATEGY"
    status_code = 400


class StrategyExecutionError(SplitterError):
    code = "STRATEGY_EXECUTION_ERROR"
    status_code = 400
