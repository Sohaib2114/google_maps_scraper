"""
Logging module for the Google Maps Scraper.
Provides logging functionality with colorized output and file logging.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
import colorlog
from src.config import LOG_DIR

# Create a custom logger
logger = logging.getLogger('google_maps_scraper')
logger.setLevel(logging.INFO)

# Create handlers
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = LOG_DIR / f'scraper_{timestamp}.log'
error_file = LOG_DIR / 'error.log'

# Create formatters
file_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Color formatter for console output
console_formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(asctime)s - %(levelname)s - %(message)s%(reset)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

# Setup console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Setup file handler for all logs
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Setup error file handler for errors only
error_handler = logging.FileHandler(error_file)
error_handler.setFormatter(file_formatter)
error_handler.setLevel(logging.ERROR)
logger.addHandler(error_handler)

def log_error(url, error_message):
    """
    Log an error with the URL and error message.
    
    Args:
        url (str): The URL where the error occurred
        error_message (str): The error message
    """
    logger.error(f"Error at {url}: {error_message}")
