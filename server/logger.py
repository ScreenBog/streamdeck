"""Красивое и удобное логирование для Deck (loguru)."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logging(level: str = "INFO") -> None:
    """Настройка логгера один раз при старте."""
    log_dir = Path(__file__).resolve().parent.parent / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "deck.log"

    logger.remove()

    # Красивая консоль
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Файл с ротацией
    logger.add(
        log_path,
        level="DEBUG",
        rotation="5 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} — {message}",
        encoding="utf-8",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info("🚀 Логирование запущено | Файл: {}", log_path)
