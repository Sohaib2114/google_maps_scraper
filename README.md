# Google Maps Business Data Scraper

A production-grade Python tool to extract business data from Google Maps and crawl the corresponding websites for public email addresses. This tool uses advanced techniques to detect and handle duplicate businesses, extract obfuscated email addresses, and respect website crawling rules while maximizing data collection.

## Features

- **Google Maps Data Extraction**:
  - Extracts business names, website URLs, phone numbers, and addresses from Google Maps
  - Uses Selenium with headless browser to simulate human-like behavior
  - Implements anti-bot detection mechanisms
  - Supports proxy rotation and CAPTCHA solving (configurable)
  - Detects and filters duplicate businesses using multiple criteria
  - Handles URL encoding issues in business names

- **Website Crawling**:
  - Extracts email addresses from business websites
  - Filters for business emails (e.g., info@, contact@) vs. personal emails
  - Intelligently respects robots.txt rules while still finding important contact information
  - Implements rate limiting to avoid overloading servers
  - Handles SSL certificate issues gracefully
  - Detects and extracts obfuscated email addresses using multiple techniques:
    - Standard email pattern matching
    - HTML entity encoding detection (&#64; for @ and &#46; for .)
    - Unicode character encoding detection
    - Common obfuscation patterns ([at], (at), [dot], etc.)
    - JavaScript obfuscation techniques
  - Avoids scraping the same websites multiple times
  - Prioritizes contact and about pages for email extraction

- **Data Persistence**:
  - Saves data in JSON, CSV, and Excel formats
  - Timestamped filenames with query hashes for easy tracking
  - Structured data output
  - Maintains history of scraped websites to avoid duplicates
  - Organizes data in dedicated data and logs directories

- **Error Handling & Logging**:
  - Comprehensive error logging with timestamps
  - Retry mechanism for failed requests
  - Detailed console and file logging

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd google_maps_scraper
   ```

2. Create a virtual environment (recommended):
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip3 install -r requirements.txt
   ```

4. Configure environment variables:
   ```
   cp config/.env.example config/.env
   ```
   Edit the `.env` file to configure proxy settings, CAPTCHA solving, and other parameters.

## Usage

### Basic Usage

```bash
python3 -m src.main "software houses in Pakistan"
```

This will search for "software houses in Pakistan" on Google Maps, extract business information, and crawl their websites for email addresses. Results will be saved in all available formats (JSON, CSV, Excel) in the `data` directory.

### Advanced Options

```bash
python3 -m src.main "software houses in Pakistan" --output-format excel --max-businesses 50 --skip-scraped --ignore-ssl-errors
```

This command will:
- Search for "software houses in Pakistan"
- Extract data for up to 50 businesses
- Save results in Excel format only
- Skip websites that have been scraped before
- Ignore SSL certificate errors when crawling websites

### Custom Output Filename

```bash
python3 -m src.main "software houses in Pakistan" --output-prefix "pak_software_houses_2023" --skip-scraped
```

This will save the output files with the prefix "pak_software_houses_2023" instead of the default timestamp-based naming.

### Verbose Mode for Debugging

```bash
python3 -m src.main "software houses in Pakistan" --max-businesses 10 --verbose
```

This will show detailed debug information during the scraping process, which is useful for troubleshooting.

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|--------|
| `query` | The search query (e.g., "software houses in Pakistan") | (Required) |
| `--output-format` | Output format for the data (json, csv, excel, or all) | all |
| `--max-businesses` | Maximum number of businesses to extract | 100 |
| `--skip-scraped` | Skip websites that have been scraped before | False |
| `--ignore-ssl-errors` | Ignore SSL certificate errors when crawling websites | False |
| `--output-prefix` | Custom prefix for output filenames | (timestamp-based) |
| `--verbose` | Enable verbose logging for debugging | False |
| `--simulate` | Run in simulation mode with test data (no actual web scraping) | False |

## Configuration

Edit the `config/.env` file to configure:

- Proxy settings (if using a proxy service)
- CAPTCHA solving (if needed)
- Delay parameters for scraping
- Output directories

## Project Structure

```
google_maps_scraper/
├── config/                 # Configuration files
│   └── .env.example        # Example environment variables
├── data/                   # Output data directory
├── logs/                   # Log files directory
├── src/                    # Source code
│   ├── config.py           # Configuration module
│   ├── data_persistence.py # Data saving module
│   ├── logger.py           # Logging module
│   ├── main.py             # Main script
│   ├── maps_scraper.py     # Google Maps scraper
│   └── website_crawler.py  # Website crawler
├── gmapscraper.py          # Command line entry point
└── requirements.txt        # Python dependencies
```

## Best Practices

This tool implements several best practices for web scraping:

- **Rate Limiting**: Random delays between requests to avoid overloading servers
- **Intelligent robots.txt Handling**: Checking and following robots.txt rules while still accessing important contact information
- **Error Handling**: Comprehensive error handling and logging
- **Anti-Bot Detection**: Simulating human-like behavior to avoid detection
- **Data Privacy**: Filtering out personal email addresses
- **SSL Handling**: Gracefully handling SSL certificate issues
- **User Agent Rotation**: Rotating user agents to avoid detection
- **Duplicate Business Detection**: Sophisticated detection of duplicate businesses using multiple criteria:
  - Website URL matching
  - Phone number matching
  - Business name and address similarity analysis
- **Duplicate Crawling Avoidance**: Avoiding scraping the same websites multiple times
- **Advanced Email Extraction**: Detecting and extracting emails that use various obfuscation techniques
- **Timeout Handling**: Properly handling timeouts for robots.txt and website crawling

## Legal Considerations

Please use this tool responsibly and in accordance with:

1. Google's Terms of Service
2. The target websites' Terms of Service
3. Applicable data protection laws (GDPR, CCPA, etc.)

This tool is intended for legitimate business research purposes only. The authors do not endorse or encourage any use of this tool that violates terms of service or applicable laws. Users are responsible for ensuring their use of this tool complies with all relevant regulations and policies.

## Troubleshooting

### Common Issues

1. **CAPTCHA Detection**: If Google Maps is showing CAPTCHA challenges frequently:
   - Try using a proxy service
   - Reduce the number of requests by setting a lower `--max-businesses` value
   - Configure CAPTCHA solving in the `.env` file if you have a service

2. **No Emails Found**: If the tool isn't finding emails on websites:
   - Check if the websites actually contain public email addresses
   - Try with `--ignore-ssl-errors` if websites have SSL certificate issues
   - Use `--verbose` to see detailed logs of the crawling process

3. **Slow Performance**: If the tool is running slowly:
   - Reduce the number of businesses to scrape
   - Check your internet connection
   - Consider using a faster proxy service

## License

[MIT License](LICENSE)
