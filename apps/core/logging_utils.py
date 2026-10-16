import json
import logging
import re
import threading

_local = threading.local()

# Matches the *value* half of a sensitive field appearing in an already
# rendered message, e.g. `password=hunter2` or `token: eyJhbGci...`.
# Deliberately does NOT match on the bare word alone ("Password changed for
# user X" must log unchanged), only on "<key><=|:><value>" shapes, so our own
# event-description messages are never mistaken for a leaked secret.
_REDACT_VALUE = re.compile(
    r"(?i)\b(password|refresh|access[_-]?token|secret|authorization|card[_-]?number|cvv)\b\s*[:=]\s*\S+"
)


def set_request_id(request_id: str | None) -> None:
    _local.request_id = request_id


def get_request_id() -> str:
    return getattr(_local, "request_id", "-") or "-"


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def _redact(rendered_message: str) -> str:
    """Redact only an actual key=value / key: value secret pair, post-rendering."""
    return _REDACT_VALUE.sub(lambda m: f"{m.group(1)}=[redacted]", rendered_message)


class RedactingFormatter(logging.Formatter):
    """Human-readable formatter for local dev that still strips obvious secrets."""

    def format(self, record: logging.LogRecord) -> str:
        # Let the base class apply record.args to record.msg first (standard
        # %-style logging), then redact the fully rendered text. Mutating
        # record.msg beforehand would break %-substitution for any message
        # that happens to mention a sensitive field name as a topic.
        formatted = super().format(record)
        return _redact(formatted)


class JsonFormatter(logging.Formatter):
    """Structured JSON logs for production (stdout -> log aggregator)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact(record.getMessage()),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)
