from __future__ import annotations

import logging


def parse_log_level(level_str: str) -> int:
    mapping = {
        "CRITICAL": logging.CRITICAL,
        "ERROR": logging.ERROR,
        "WARNING": logging.WARNING,
        "INFO": logging.INFO,
        "DEBUG": logging.DEBUG,
        "NOTSET": logging.NOTSET,
    }
    return mapping.get(level_str.upper(), logging.INFO)


def configure_logging(level: int, use_rich: bool = True, rich_tracebacks: bool = True) -> None:
    handlers = []
    if use_rich:
        try:
            from rich.logging import RichHandler
            if rich_tracebacks:
                try:
                    from rich.traceback import install as rich_traceback_install
                    rich_traceback_install(show_locals=False)
                except Exception:
                    pass
            handlers = [RichHandler(rich_tracebacks=rich_tracebacks, markup=False)]
        except Exception:
            handlers = [logging.StreamHandler()]
    else:
        handlers = [logging.StreamHandler()]

    if use_rich and handlers and isinstance(handlers[0], logging.Handler):
        logging.basicConfig(
            level=level,
            format="%(message)s",
            handlers=handlers,
            force=True,
        )
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
            handlers=handlers,
            force=True,
        )


