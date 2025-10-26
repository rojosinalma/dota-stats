import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file_path: str = "/app/logs/app.log"):
    """
    Configure logging to output to both stdout and log file.

    Args:
        log_level: Either "INFO" or "DEBUG"
            - INFO: Logs INFO and above to both stdout and file
            - DEBUG: Logs DEBUG and above (everything) to both stdout and file
        log_file_path: Path to the log file

    File logs are rotated (max 10MB, keep 5 backups)
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Check if our handlers are already present to avoid duplicates
    # Don't clear all handlers as this removes Celery's logging
    has_console = any(isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
                      for h in root_logger.handlers)
    has_file = any(isinstance(h, RotatingFileHandler) and h.baseFilename == str(log_path)
                   for h in root_logger.handlers)

    if has_console and has_file:
        # Already configured, just update levels
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
                handler.setLevel(numeric_level)
            elif isinstance(handler, RotatingFileHandler) and handler.baseFilename == str(log_path):
                handler.setLevel(numeric_level)
        return root_logger

    # Console handler (stdout) - matches root logger level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler - matches root logger level
    # Rotate when file reaches 10MB, keep 5 backup files
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Log startup
    logging.info(f"Logging configured: {log_level}+ to stdout and file")
    logging.info(f"Log file: {log_file_path}")

    return root_logger
