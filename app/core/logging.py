"""
Structured logging configuration with sensitive data redaction
"""
import logging
import re
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor


def redact_sensitive_data(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Redact sensitive information from log messages

    Patterns redacted:
    - Authorization headers (Bearer tokens)
    - Cookie values
    - Google session cookies (SID, HSID, SSID, APISID, SAPISID)
    - Encryption keys
    - Passwords
    - API tokens

    Args:
        logger: Logger instance
        method_name: Method name
        event_dict: Event dictionary

    Returns:
        Modified event dictionary with redacted sensitive data
    """
    sensitive_patterns = [
        # Authorization headers
        (r"(Authorization:\s*Bearer\s+)([^\s]+)", r"\1***REDACTED***"),
        (r"(authorization:\s*bearer\s+)([^\s]+)", r"\1***REDACTED***"),
        (r"(Bearer\s+)([A-Za-z0-9\-._~+/]+=*)", r"\1***REDACTED***"),
        # Cookie headers
        (r"(Cookie:\s*)([^\n]+)", r"\1***REDACTED***"),
        (r"(cookie:\s*)([^\n]+)", r"\1***REDACTED***"),
        # Specific Google cookies
        (r"(SID|HSID|SSID|APISID|SAPISID)=([^;,\s]+)", r"\1=***REDACTED***"),
        (r"(__Secure-[13]PSID)=([^;,\s]+)", r"\1=***REDACTED***"),
        # Encryption keys and tokens
        (r"(encryption_key['\"]?\s*[:=]\s*['\"]?)([^'\"}\s,]+)", r"\1***REDACTED***"),
        (r"(ENCRYPTION_KEY['\"]?\s*[:=]\s*['\"]?)([^'\"}\s,]+)", r"\1***REDACTED***"),
        (r"(api_token['\"]?\s*[:=]\s*['\"]?)([^'\"}\s,]+)", r"\1***REDACTED***"),
        (r"(access_token['\"]?\s*[:=]\s*['\"]?)([^'\"}\s,]+)", r"\1***REDACTED***"),
        # Passwords
        (r"(password['\"]?\s*[:=]\s*['\"]?)([^'\"}\s,]+)", r"\1***REDACTED***"),
        (r"(PASSWORD['\"]?\s*[:=]\s*['\"]?)([^'\"}\s,]+)", r"\1***REDACTED***"),
        # Client secrets
        (r"(client_secret['\"]?\s*[:=]\s*['\"]?)([^'\"}\s,]+)", r"\1***REDACTED***"),
        (r"(CLIENT_SECRET['\"]?\s*[:=]\s*['\"]?)([^'\"}\s,]+)", r"\1***REDACTED***"),
    ]

    # Redact in event message
    message = str(event_dict.get("event", ""))
    for pattern, replacement in sensitive_patterns:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
    event_dict["event"] = message

    # Redact in additional context fields
    for key, value in event_dict.items():
        if key == "event":
            continue
        if isinstance(value, str):
            for pattern, replacement in sensitive_patterns:
                value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
            event_dict[key] = value

    return event_dict


def add_app_context(
    logger: Any, method_name: str, event_dict: EventDict
) -> EventDict:
    """
    Add application context to log messages

    Args:
        logger: Logger instance
        method_name: Method name
        event_dict: Event dictionary

    Returns:
        Modified event dictionary with app context
    """
    event_dict["app"] = "classroom-downloader-api"
    return event_dict


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "text",
    log_redact_fields: list[str] | None = None,
) -> None:
    """
    Configure structured logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ("text" or "json")
        log_redact_fields: Additional field names to redact (optional)
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Build processor chain
    processors: list[Processor] = [
        # Add log level and logger name
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        # Add timestamp
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # Add app context
        add_app_context,
        # Redact sensitive data
        redact_sensitive_data,
        # Add stack info on exceptions
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # Add call site info (filename, function, line number)
        structlog.processors.CallsiteParameterAdder(
            [
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]

    # Choose renderer based on format
    if log_format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


# Example usage in other modules:
# from app.core.logging import get_logger
# logger = get_logger(__name__)
# logger.info("user_login", user_id=123, email="user@example.com")
# logger.error("download_failed", job_id=456, error=str(e), exc_info=True)
