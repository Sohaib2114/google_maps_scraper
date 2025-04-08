"""
Data persistence module.
Handles saving extracted data to various formats.
"""
import json
import csv
import os
import hashlib
from datetime import datetime
import pandas as pd
from pathlib import Path

from src.config import DATA_DIR
from src.logger import logger

class DataPersistence:
    """
    A class to handle data persistence for extracted business data.
    """
    
    def __init__(self):
        """Initialize the data persistence handler."""
        # Format: YYYY-MM-DD_HH-MM-SS for better readability
        self.timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        self.scraped_websites = self._load_scraped_websites()
    
    def _load_scraped_websites(self):
        """
        Load previously scraped websites from history file to avoid duplicates.
        
        Returns:
            set: Set of website URLs that have been previously scraped
        """
        history_file = DATA_DIR / 'scraped_websites_history.json'
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except Exception as e:
                logger.error(f"Error loading scraped websites history: {str(e)}")
        return set()
    
    def _save_scraped_websites(self):
        """
        Save the set of scraped websites to a history file.
        """
        history_file = DATA_DIR / 'scraped_websites_history.json'
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.scraped_websites), f, indent=4, ensure_ascii=False)
            logger.info(f"Updated scraped websites history: {len(self.scraped_websites)} websites")
        except Exception as e:
            logger.error(f"Error saving scraped websites history: {str(e)}")
    
    def is_website_scraped(self, url):
        """
        Check if a website has been scraped before.
        
        Args:
            url (str): The website URL to check
            
        Returns:
            bool: True if the website has been scraped before, False otherwise
        """
        return url in self.scraped_websites
    
    def add_scraped_website(self, url):
        """
        Add a website to the set of scraped websites.
        
        Args:
            url (str): The website URL to add
        """
        self.scraped_websites.add(url)
        self._save_scraped_websites()
    
    def save_to_json(self, data, filename=None, query=None):
        """
        Save data to a JSON file.
        
        Args:
            data (list): The data to save
            filename (str, optional): The filename to use
            query (str, optional): The search query used to get this data
            
        Returns:
            str: The path to the saved file
        """
        if not filename:
            # Create a more descriptive filename with the query
            query_part = ""
            if query:
                # Create a short hash of the query to avoid filename issues
                query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
                query_part = f"{query_hash}_"
            
            filename = f"gmaps_{query_part}{self.timestamp}.json"
            
        file_path = DATA_DIR / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            # Convert path to a more user-friendly format for display
            display_path = str(file_path).replace('../', '')
            logger.info(f"JSON data saved to: {display_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving to JSON: {str(e)}")
            return None
    
    def save_to_csv(self, data, filename=None, query=None):
        """
        Save data to a CSV file.
        
        Args:
            data (list): The data to save
            filename (str, optional): The filename to use
            query (str, optional): The search query used to get this data
            
        Returns:
            str: The path to the saved file
        """
        if not filename:
            # Create a more descriptive filename with the query
            query_part = ""
            if query:
                # Create a short hash of the query to avoid filename issues
                query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
                query_part = f"{query_hash}_"
            
            filename = f"gmaps_{query_part}{self.timestamp}.csv"
            
        file_path = DATA_DIR / filename
        
        try:
            # Flatten the email_addresses list to a comma-separated string
            flattened_data = []
            for item in data:
                flattened_item = item.copy()
                if 'email_addresses' in flattened_item and isinstance(flattened_item['email_addresses'], list):
                    flattened_item['email_addresses'] = ', '.join(flattened_item['email_addresses'])
                flattened_data.append(flattened_item)
            
            # Write to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if not data:
                    writer = csv.writer(f)
                    writer.writerow(['No data found'])
                else:
                    fieldnames = flattened_data[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flattened_data)
            
            # Convert path to a more user-friendly format for display
            display_path = str(file_path).replace('../', '')
            logger.info(f"CSV data saved to: {display_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving to CSV: {str(e)}")
            return None
    
    def save_to_excel(self, data, filename=None, query=None):
        """
        Save data to an Excel file.
        
        Args:
            data (list): The data to save
            filename (str, optional): The filename to use
            query (str, optional): The search query used to get this data
            
        Returns:
            str: The path to the saved file
        """
        if not filename:
            # Create a more descriptive filename with the query
            query_part = ""
            if query:
                # Create a short hash of the query to avoid filename issues
                query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
                query_part = f"{query_hash}_"
            
            filename = f"gmaps_{query_part}{self.timestamp}.xlsx"
            
        file_path = DATA_DIR / filename
        
        try:
            # Flatten the email_addresses list to a comma-separated string
            flattened_data = []
            for item in data:
                flattened_item = item.copy()
                if 'email_addresses' in flattened_item and isinstance(flattened_item['email_addresses'], list):
                    flattened_item['email_addresses'] = ', '.join(flattened_item['email_addresses'])
                flattened_data.append(flattened_item)
            
            # Convert to DataFrame and save to Excel
            df = pd.DataFrame(flattened_data)
            df.to_excel(file_path, index=False)
            
            # Convert path to a more user-friendly format for display
            display_path = str(file_path).replace('../', '')
            logger.info(f"Excel data saved to: {display_path}")
            return str(file_path)
        except Exception as e:
            logger.error(f"Error saving to Excel: {str(e)}")
            return None
