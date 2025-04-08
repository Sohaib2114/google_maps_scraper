"""
Configuration module for the Google Maps Scraper.
Loads environment variables and provides configuration settings.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# Load environment variables from .env file
env_path = PROJECT_ROOT / 'config' / '.env'
load_dotenv(dotenv_path=env_path if env_path.exists() else None)

# Proxy Configuration
USE_PROXIES = os.getenv('USE_PROXIES', 'false').lower() == 'true'
PROXY_API_KEY = os.getenv('PROXY_API_KEY', '')
PROXY_URL = os.getenv('PROXY_URL', '')

# CAPTCHA Solving
USE_CAPTCHA_SOLVER = os.getenv('USE_CAPTCHA_SOLVER', 'false').lower() == 'true'
CAPTCHA_API_KEY = os.getenv('CAPTCHA_API_KEY', '')

# Scraping Parameters
MIN_DELAY = int(os.getenv('MIN_DELAY', 10))
MAX_DELAY = int(os.getenv('MAX_DELAY', 30))
WEBSITE_MIN_DELAY = int(os.getenv('WEBSITE_MIN_DELAY', 2))
WEBSITE_MAX_DELAY = int(os.getenv('WEBSITE_MAX_DELAY', 5))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))

# Output Configuration
DATA_DIR = Path(os.getenv('DATA_DIR', PROJECT_ROOT / 'data'))
LOG_DIR = Path(os.getenv('LOG_DIR', PROJECT_ROOT / 'logs'))

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Email regex pattern
EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# Generic business email prefixes to prioritize
BUSINESS_EMAIL_PREFIXES = [
    'info', 'contact', 'hello', 'support', 'sales', 'business', 
    'admin', 'office', 'help', 'service', 'inquiry', 'team',
    'marketing', 'hr', 'jobs', 'careers', 'feedback', 'webmaster'
]
