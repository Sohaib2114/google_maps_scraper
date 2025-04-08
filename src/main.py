"""
Main script for the Google Maps Scraper.
Ties together all modules to extract business data and email addresses.
"""
import argparse
import sys
import time
import logging
from tqdm import tqdm

from src.maps_scraper import GoogleMapsScraper
from src.website_crawler import WebsiteCrawler
from src.data_persistence import DataPersistence
from src.logger import logger

def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Extract business data from Google Maps and crawl websites for email addresses.'
    )
    
    parser.add_argument(
        'query',
        type=str,
        help='Search query (e.g., "software houses in Pakistan")'
    )
    
    parser.add_argument(
        '--output-format',
        type=str,
        choices=['json', 'csv', 'excel', 'all'],
        default='all',
        help='Output format for the data (default: all)'
    )
    
    parser.add_argument(
        '--max-businesses',
        type=int,
        default=20,
        help='Maximum number of businesses to extract (default: 20)'
    )
    
    parser.add_argument(
        '--simulate',
        action='store_true',
        help='Run in simulation mode with test data (no actual web scraping)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--skip-scraped',
        action='store_true',
        help='Skip websites that have been scraped before'
    )
    
    parser.add_argument(
        '--ignore-ssl-errors',
        action='store_true',
        help='Ignore SSL certificate errors when crawling websites'
    )
    
    parser.add_argument(
        '--output-prefix',
        type=str,
        help='Prefix for output filenames'
    )
    
    return parser.parse_args()

def generate_test_data(query, count=5):
    """
    Generate test data for simulation mode.
    
    Args:
        query (str): The search query
        count (int): Number of test businesses to generate
        
    Returns:
        list: A list of test business data
    """
    logger.info(f"Generating test data for query: {query}")
    
    test_businesses = []
    domains = ['example.com', 'testcompany.pk', 'softwarehouse.com.pk', 'techfirm.pk', 'devshop.io']
    
    for i in range(1, count + 1):
        domain = domains[i % len(domains)]
        business = {
            'name': f"Test Software House {i}",
            'website': f"https://www.{domain}",
            'phone_number': f"+92 300 555{i:04d}",
            'email_addresses': [f"info@{domain}", f"contact@{domain}"] if i % 2 == 0 else [f"info@{domain}"]
        }
        test_businesses.append(business)
    
    return test_businesses

def main():
    """Main function to run the Google Maps scraper."""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info(f"Starting Google Maps Scraper with query: {args.query}")
    
    # Initialize data persistence
    data_persistence = DataPersistence()
    
    try:
        # Check if running in simulation mode
        if args.simulate:
            logger.info("Running in simulation mode with test data")
            businesses = generate_test_data(args.query, count=args.max_businesses)
        else:
            # Initialize components for actual scraping
            maps_scraper = GoogleMapsScraper()
            website_crawler = WebsiteCrawler()
            
            # Extract business data from Google Maps
            logger.info("Extracting business data from Google Maps...")
            businesses = maps_scraper.search_businesses(args.query)
            
            if not businesses:
                logger.error("No businesses found. Exiting.")
                return
            
            # Limit the number of businesses if specified
            if args.max_businesses and len(businesses) > args.max_businesses:
                logger.info(f"Limiting to {args.max_businesses} businesses")
                businesses = businesses[:args.max_businesses]
            
            logger.info(f"Found {len(businesses)} businesses")
            
            # Crawl websites for email addresses
            logger.info("Crawling websites for email addresses...")
            
            for business in tqdm(businesses, desc="Crawling websites"):
                website_url = business.get('website')
                
                if website_url:
                    # Check if we should skip this website
                    if args.skip_scraped and data_persistence.is_website_scraped(website_url):
                        logger.info(f"Skipping previously scraped website: {website_url}")
                        business['email_addresses'] = []
                        business['skipped'] = True
                        continue
                        
                    logger.info(f"Crawling website for {business['name']}: {website_url}")
                    email_addresses = website_crawler.crawl_website(website_url)
                    
                    if email_addresses:
                        logger.info(f"Found {len(email_addresses)} email addresses for {business['name']}")
                        business['email_addresses'] = email_addresses
                        # Add to scraped websites history
                        data_persistence.add_scraped_website(website_url)
                    else:
                        logger.info(f"No email addresses found for {business['name']}")
                        business['email_addresses'] = []
                        # Still add to scraped websites to avoid recrawling
                        data_persistence.add_scraped_website(website_url)
                else:
                    logger.info(f"No website found for {business['name']}")
                    business['email_addresses'] = []
        
        # Display summary of found businesses
        logger.info(f"\nSummary of {len(businesses)} businesses:")
        for i, business in enumerate(businesses, 1):
            email_count = len(business.get('email_addresses', []))
            logger.info(f"{i}. {business['name']} - Website: {business.get('website', 'None')} - Emails: {email_count}")
        
        # Save the data
        logger.info("\nSaving extracted data...")
        
        # Create filename prefix if specified
        filename_prefix = args.output_prefix if args.output_prefix else None
        
        if args.output_format == 'json' or args.output_format == 'all':
            json_path = data_persistence.save_to_json(businesses, query=args.query, 
                                                    filename=filename_prefix+'.json' if filename_prefix else None)
            logger.info(f"JSON data saved to: {json_path}")
        
        if args.output_format == 'csv' or args.output_format == 'all':
            csv_path = data_persistence.save_to_csv(businesses, query=args.query,
                                                  filename=filename_prefix+'.csv' if filename_prefix else None)
            logger.info(f"CSV data saved to: {csv_path}")
        
        if args.output_format == 'excel' or args.output_format == 'all':
            excel_path = data_persistence.save_to_excel(businesses, query=args.query,
                                                      filename=filename_prefix+'.xlsx' if filename_prefix else None)
            logger.info(f"Excel data saved to: {excel_path}")
        
        logger.info("Data extraction and saving completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
    finally:
        # Clean up
        if not args.simulate and 'maps_scraper' in locals():
            maps_scraper.close()

if __name__ == "__main__":
    main()
