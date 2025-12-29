import logging
import os
import sys
import time
from typing import Optional

import structlog
from flask import Flask, g, request


def _add_static_fields(service: Optional[str], env: Optional[str]):
    """Return a processor that adds static fields like service/env."""
    def processor(logger, method_name, event_dict):  # type: ignore[no-untyped-def]
        if service:
            event_dict.setdefault("service", service)
        if env:
            event_dict.setdefault("env", env)
        event_dict.setdefault("pid", os.getpid())
        return event_dict
    return processor


def configure_logging(level: str = "INFO", *, service: Optional[str] = None, env: Optional[str] = None) -> None:
    """Configure JSON structured logging for app, gunicorn, and celery."""
    log_level = getattr(logging, level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    pre_chain = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
        _add_static_fields(service, env),
    ]

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Reduce noisy loggers commonly seen on PaaS
    for noisy in ("boto3", "botocore", "urllib3", "celery.app.trace"):
        try:
            logging.getLogger(noisy).setLevel(logging.WARNING)
        except Exception:
            pass

    structlog.configure(
        processors=
        pre_chain
        + [
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def instrument_flask(app: Flask) -> None:
    """Add request/response logging middleware to Flask app."""
    log = get_logger("http")

    @app.before_request
    def _before_request():  # type: ignore[no-redef]
        g._start_time = time.perf_counter()
        # Generate simple request id and propagate as header
        rid = request.headers.get("X-Request-ID") or os.urandom(8).hex()
        g._request_id = rid
        structlog.contextvars.bind_contextvars(request_id=rid)

    @app.after_request
    def _after_request(response):  # type: ignore[no-redef]
        try:
            # Skip very noisy endpoints
            path = request.path or ""
            if not (path.endswith("/health") or path.endswith("/metrics")):
                dur_ms = None
                try:
                    dur_ms = int((time.perf_counter() - getattr(g, "_start_time", time.perf_counter())) * 1000)
                except Exception:
                    pass
                log.info(
                    "http_request",
                    method=request.method,
                    path=path,
                    query=request.query_string.decode("utf-8", errors="ignore"),
                    status=response.status_code,
                    remote_addr=request.headers.get("X-Forwarded-For") or request.remote_addr,
                    user_agent=request.headers.get("User-Agent"),
                    duration_ms=dur_ms,
                    request_id=getattr(g, "_request_id", None),
                )
        finally:
            # Always set request id header back
            if getattr(g, "_request_id", None):
                response.headers["X-Request-ID"] = g._request_id
            # Clear contextvars to avoid leaking across requests in worker
            structlog.contextvars.clear_contextvars()
        return response

    @app.errorhandler(Exception)
    def _on_error(e):  # type: ignore[no-redef]
        import traceback
        import os
        
        error_details = {
            "error": "internal server error",
            "error_type": type(e).__name__,
            "timestamp": __import__('datetime').datetime.utcnow().isoformat(),
            "railway_deployment": os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown'),
            "request_id": getattr(g, "_request_id", None),
        }
        
        # Log detailed error for Railway logs
        log.error(
            "http_error",
            method=getattr(request, "method", None),
            path=getattr(request, "path", None),
            request_id=getattr(g, "_request_id", None),
            error_type=type(e).__name__,
            error_message=str(e),
            railway_deployment=os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown'),
            exc_info=True,
        )
        
        # Print to stdout for Railway console logs
        print(f"❌ HTTP ERROR: {type(e).__name__}: {str(e)}")
        print(f"🌐 Request: {getattr(request, 'method', 'UNKNOWN')} {getattr(request, 'path', 'UNKNOWN')}")
        print(f"🆔 Request ID: {getattr(g, '_request_id', 'unknown')}")
        print(f"🚂 Railway Deployment: {os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown')}")
        print("📋 Error Traceback:")
        traceback.print_exc()
        
        # Return detailed error in development, generic in production
        if os.environ.get('ENV', '').lower() in ('development', 'dev', 'debug'):
            error_details["details"] = str(e)
            error_details["traceback"] = traceback.format_exc().split('\n')
        
        return error_details, 500


def get_logger(name: str | None = None):
    return structlog.get_logger(name)
