#!/usr/bin/env python3
"""
Google Maps Scraper - Command line tool to extract business data and email addresses.
"""
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main function
from src.main import main

if __name__ == "__main__":
    main()
