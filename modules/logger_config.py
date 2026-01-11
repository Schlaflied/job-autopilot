# Job Autopilot - Logging Configuration

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Log file paths
APP_LOG = os.path.join(LOG_DIR, "app.log")
STREAMLIT_LOG = os.path.join(LOG_DIR, "streamlit.log")
SCRAPER_LOG = os.path.join(LOG_DIR, "scraper.log")
GMAIL_LOG = os.path.join(LOG_DIR, "gmail.log")
ERROR_LOG = os.path.join(LOG_DIR, "error.log")

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name, log_file, level=logging.INFO):
    """
    Create a logger with both file and console handlers
    
    Args:
        name (str): Logger name
        log_file (str): Path to log file
        level (int): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # File handler (rotating, max 10MB, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Less verbose in console
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def setup_error_logger():
    """
    Create a separate logger for ERROR level messages only
    All ERROR logs from all modules will be aggregated here
    """
    error_logger = logging.getLogger("error_aggregator")
    error_logger.setLevel(logging.ERROR)
    
    # Avoid duplicate handlers
    if error_logger.handlers:
        return error_logger
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    error_handler = RotatingFileHandler(
        ERROR_LOG,
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    error_logger.addHandler(error_handler)
    return error_logger

# Pre-configured loggers for different modules
app_logger = setup_logger("app", APP_LOG, logging.DEBUG)
streamlit_logger = setup_logger("streamlit", STREAMLIT_LOG, logging.INFO)
scraper_logger = setup_logger("scraper", SCRAPER_LOG, logging.DEBUG)
gmail_logger = setup_logger("gmail", GMAIL_LOG, logging.INFO)
error_logger = setup_error_logger()

# Example usage:
# from modules.logger_config import app_logger, scraper_logger
# app_logger.info("Application started")
# scraper_logger.error("Failed to scrape job", exc_info=True)
