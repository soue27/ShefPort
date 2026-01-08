import os

from loguru import logger


LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")

def setup_logging() -> None:
    logger.remove()
    # =========================
    # 1) вывод в Консоль
    # =========================
    # logger.add(
    #     sink=lambda msg: print(msg, end=""),
    #     format="<green>{time:HH:mm:ss}</green> | {name} | <level>{level}</level> | {message}",
    #     level="DEBUG",
    # )
    # =========================
    # 2) Файл debug.log — все уровни
    # =========================
    logger.add(
        "logs/debug.log",
        rotation="1 week",
        compression="zip",
        level="DEBUG",
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {name} | {level} | {message}",
    )
    # =========================
    # 3) Файл app.log — только ошибки
    # =========================
    logger.add(
        "logs/error.log",
        rotation="1 week",
        compression="zip",
        level="ERROR",
        enqueue=True,
        filter=lambda record: record["level"].no >= 40,
        format="{time:YYYY-MM-DD HH:mm:ss} | {name} | {level} | {message}",
    )