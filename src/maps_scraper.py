"""
Google Maps scraper module.
Handles extraction of business data from Google Maps using Selenium.
"""
import time
import random
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from retry import retry

from src.config import (
    MIN_DELAY, MAX_DELAY, MAX_RETRIES, 
    USE_PROXIES, PROXY_API_KEY, PROXY_URL,
    USE_CAPTCHA_SOLVER, CAPTCHA_API_KEY
)
import difflib
from src.logger import logger, log_error

class GoogleMapsScraper:
    """
    A class to scrape business data from Google Maps.
    """
    
    def __init__(self):
        """Initialize the Google Maps scraper."""
        self.driver = None
        self.user_agent = UserAgent()
        
    def setup_driver(self):
        """
        Set up the Selenium WebDriver with appropriate options.
        """
        options = Options()
        
        # Using a non-headless browser can help avoid detection
        # But for production, we'll use headless with additional anti-detection measures
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Use a realistic user agent
        user_agent = self.user_agent.random
        options.add_argument(f"user-agent={user_agent}")
        logger.info(f"Using User-Agent: {user_agent}")
        
        # Additional options to avoid detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=en-US,en;q=0.9")
        
        # Add experimental options
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "intl.accept_languages": "en-US,en"
        })
        
        # Add proxy if enabled
        if USE_PROXIES and PROXY_API_KEY and PROXY_URL:
            try:
                # This is a placeholder for proxy integration
                # In a real implementation, you would fetch a proxy from your service
                proxy = self._get_proxy()
                if proxy:
                    options.add_argument(f'--proxy-server={proxy}')
                    logger.info(f"Using proxy: {proxy}")
            except Exception as e:
                logger.warning(f"Failed to set up proxy: {str(e)}")
        
        try:
            # Try direct Chrome initialization without ChromeDriverManager
            driver = webdriver.Chrome(options=options)
            
            # Execute JavaScript to make WebDriver detection harder
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            driver.execute_script(
                "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})"
            )
            driver.execute_script(
                "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})"
            )
            
            # Add a custom permission to avoid location permission dialogs
            driver.execute_cdp_cmd("Browser.grantPermissions", {
                "origin": "https://www.google.com",
                "permissions": ["geolocation"]
            })
            
            self.driver = driver
            logger.info("WebDriver set up successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Chrome directly: {str(e)}")
            
            try:
                # Fallback to ChromeDriverManager
                from selenium.webdriver.chrome.service import Service as ChromeService
                from webdriver_manager.chrome import ChromeDriverManager
                
                service = ChromeService(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=options)
                
                # Execute JavaScript to make WebDriver detection harder
                driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
                driver.execute_script(
                    "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})"
                )
                driver.execute_script(
                    "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})"
                )
                
                # Add a custom permission to avoid location permission dialogs
                driver.execute_cdp_cmd("Browser.grantPermissions", {
                    "origin": "https://www.google.com",
                    "permissions": ["geolocation"]
                })
                
                self.driver = driver
                logger.info("WebDriver set up successfully using ChromeDriverManager")
                return True
            except Exception as e2:
                log_error("Driver setup", f"Direct init failed: {str(e)}. ChromeDriverManager failed: {str(e2)}")
                return False
    
    def _get_proxy(self):
        """
        Get a proxy from the proxy service.
        This is a placeholder - implement according to your proxy service.
        
        Returns:
            str: A proxy in the format ip:port
        """
        # Placeholder for actual proxy service integration
        # In a real implementation, you would make an API call to your proxy service
        return None
    
    def _solve_captcha(self):
        """
        Solve CAPTCHA if detected.
        This is a placeholder - implement according to your CAPTCHA solving service.
        
        Returns:
            bool: True if CAPTCHA was solved, False otherwise
        """
        if not USE_CAPTCHA_SOLVER or not CAPTCHA_API_KEY:
            logger.warning("CAPTCHA detected but solver not configured")
            return False
            
        # Placeholder for actual CAPTCHA solving integration
        # In a real implementation, you would:
        # 1. Detect the CAPTCHA
        # 2. Take a screenshot or get the CAPTCHA image
        # 3. Send it to the CAPTCHA solving service
        # 4. Input the solution
        
        logger.info("CAPTCHA solving attempted")
        return False  # Replace with actual implementation
    
    def _random_delay(self):
        """Add a random delay to mimic human behavior."""
        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        time.sleep(delay)
    
    def _simulate_human_behavior(self):
        """
        Simulate human-like behavior to avoid detection.
        """
        if not self.driver:
            return
            
        # Move mouse to random positions (in headless mode this is just for the logs)
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            actions = ActionChains(self.driver)
            
            # Move to random positions a few times
            for _ in range(random.randint(2, 5)):
                x_coord = random.randint(100, 1000)
                y_coord = random.randint(100, 600)
                actions.move_by_offset(x_coord, y_coord).perform()
                time.sleep(random.uniform(0.3, 1.0))
                
            # Reset position
            actions.move_to_element(self.driver.find_element(By.TAG_NAME, "body")).perform()
        except Exception as e:
            logger.debug(f"Mouse movement simulation failed: {str(e)}")
            
        # Scroll down slowly a few times with variable speed
        for _ in range(random.randint(2, 5)):
            # Random scroll amount
            scroll_amount = random.randint(300, 700)
            # Scroll with a smooth effect by doing multiple small scrolls
            steps = random.randint(5, 15)
            for step in range(steps):
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount/steps});")
                time.sleep(random.uniform(0.05, 0.2))
            time.sleep(random.uniform(0.7, 2.5))
        
        # Sometimes scroll horizontally too
        if random.random() < 0.3:  # 30% chance
            self.driver.execute_script(f"window.scrollBy({random.randint(50, 200)}, 0);")
            time.sleep(random.uniform(0.5, 1.5))
            self.driver.execute_script("window.scrollBy(-100, 0);")
            
        # Scroll back up gradually
        current_position = self.driver.execute_script("return window.pageYOffset;")
        steps = random.randint(5, 15)
        for step in range(steps):
            self.driver.execute_script(f"window.scrollTo(0, {current_position - (current_position/steps) * step});")
            time.sleep(random.uniform(0.05, 0.2))
        
        time.sleep(random.uniform(0.5, 1.5))
    
    def _is_duplicate_business(self, business_data, existing_businesses):
        """
        Check if a business is a duplicate of an existing one.
        
        Args:
            business_data (dict): The business data to check
            existing_businesses (list): List of existing business data dictionaries
            
        Returns:
            bool: True if the business is a duplicate, False otherwise
        """
        if not business_data or not existing_businesses:
            return False
            
        # Get business name and website for comparison
        name = business_data.get('name', '').lower()
        website = business_data.get('website', '').lower()
        phone = business_data.get('phone', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        address = business_data.get('address', '').lower()
        
        logger.debug(f"Checking for duplicates: {name}")
        
        for i, existing in enumerate(existing_businesses):
            existing_name = existing.get('name', '').lower()
            existing_website = existing.get('website', '').lower()
            existing_phone = existing.get('phone', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            existing_address = existing.get('address', '').lower()
            
            # Check for duplicates based on multiple criteria
            # 1. Same website (strongest indicator)
            if website and existing_website and website == existing_website:
                logger.info(f"Duplicate business detected by website match:")
                logger.info(f"  New: {business_data.get('name')} - {website}")
                logger.info(f"  Existing: {existing.get('name')} - {existing_website}")
                return True
                
            # 2. Same phone number (strong indicator)
            if phone and existing_phone and phone == existing_phone:
                logger.info(f"Duplicate business detected by phone match:")
                logger.info(f"  New: {business_data.get('name')} - {phone}")
                logger.info(f"  Existing: {existing.get('name')} - {existing_phone}")
                return True
                
            # 3. Similar name and address
            name_similarity = self._calculate_similarity(name, existing_name)
            if name_similarity > 0.8:
                logger.debug(f"High name similarity ({name_similarity:.2f}): {name} vs {existing_name}")
                
                if address and existing_address:
                    address_similarity = self._calculate_similarity(address, existing_address)
                    if address_similarity > 0.7:
                        logger.info(f"Duplicate business detected by name/address similarity:")
                        logger.info(f"  New: {business_data.get('name')} - {address}")
                        logger.info(f"  Existing: {existing.get('name')} - {existing_address}")
                        logger.info(f"  Name similarity: {name_similarity:.2f}, Address similarity: {address_similarity:.2f}")
                        return True
                    elif address_similarity > 0.5:
                        logger.debug(f"Moderate address similarity ({address_similarity:.2f}): {address} vs {existing_address}")
                    
        logger.debug(f"No duplicates found for: {name}")
        return False
        
    def _calculate_similarity(self, str1, str2):
        """
        Calculate similarity between two strings using a simple ratio.
        
        Args:
            str1 (str): First string
            str2 (str): Second string
            
        Returns:
            float: Similarity ratio between 0 and 1
        """
        if not str1 or not str2:
            return 0
            
        # Use difflib's SequenceMatcher for string similarity
        return difflib.SequenceMatcher(None, str1, str2).ratio()
    
    def format_search_url(self, query):
        """
        Format a search query into a valid Google Maps search URL.
        
        Args:
            query (str): The search query (e.g., "software houses in Pakistan")
            
        Returns:
            str: A formatted Google Maps URL
        """
        # Encode the query for URL
        encoded_query = urllib.parse.quote_plus(query)
        return f"https://www.google.com/maps/search/{encoded_query}/"
    
    @retry(tries=MAX_RETRIES, delay=2, backoff=2, logger=logger)
    def search_businesses(self, query):
        """
        Search for businesses on Google Maps using the provided query.
        
        Args:
            query (str): The search query (e.g., "software houses in Pakistan")
            
        Returns:
            list: A list of dictionaries containing business data
        """
        if not self.driver and not self.setup_driver():
            logger.error("Failed to set up WebDriver")
            return []
            
        search_url = self.format_search_url(query)
        logger.info(f"Searching for: {query}")
        logger.info(f"URL: {search_url}")
        
        try:
            # First navigate to Google homepage to set cookies
            self.driver.get("https://www.google.com")
            self._random_delay()
            
            # Now navigate to the search URL
            logger.info("Navigating to Google Maps search URL")
            self.driver.get(search_url)
            
            # Add a longer initial delay to let the page fully load
            time.sleep(random.uniform(5, 8))
            
            # Check if CAPTCHA is present and try to solve it
            if "recaptcha" in self.driver.page_source.lower() or "captcha" in self.driver.page_source.lower():
                logger.warning("CAPTCHA detected")
                if not self._solve_captcha():
                    logger.error("Failed to solve CAPTCHA")
                    return []
            
            # Simulate human behavior
            self._simulate_human_behavior()
            
            # Wait for results to load with a longer timeout
            try:
                logger.info("Waiting for search results to load...")
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='article']")),
                )
                logger.info("Search results loaded successfully")
            except TimeoutException:
                logger.warning("Timeout waiting for search results")
                
                # Try an alternative selector
                try:
                    logger.info("Trying alternative selector...")
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@aria-label, 'Results for')]"))
                    )
                    logger.info("Found results container with alternative selector")
                except TimeoutException:
                    logger.error("Could not find any search results with alternative selector")
                    
                    # Save screenshot for debugging
                    screenshot_path = f"logs/screenshot_{int(time.time())}.png"
                    try:
                        self.driver.save_screenshot(screenshot_path)
                        logger.info(f"Saved screenshot to {screenshot_path}")
                    except Exception as e:
                        logger.error(f"Failed to save screenshot: {str(e)}")
                        
                    # Log page source for debugging
                    logger.debug(f"Page source: {self.driver.page_source[:500]}...")
                    return []
            
            # Extract business listings
            businesses = []
            
            # Try different selectors for business listings
            business_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
            
            if not business_elements:
                logger.info("Trying alternative selectors for business listings")
                business_elements = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'Nv2PK')]|//div[contains(@class, 'THOPZb')]")
            
            if not business_elements:
                logger.error("Could not find any business listings")
                return []
                
            logger.info(f"Found {len(business_elements)} business listings")
            
            for i, element in enumerate(business_elements):
                try:
                    logger.info(f"Processing business #{i+1}")
                    
                    # Try to scroll the element into view before clicking
                    self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    # Click on the business to view details
                    element.click()
                    logger.info(f"Clicked on business #{i+1}")
                    
                    # Add a longer delay to let the details page load
                    time.sleep(random.uniform(3, 6))
                    
                    # Extract business data
                    business_data = self._extract_business_data()
                    if business_data:
                        # Check if this is a duplicate business
                        if not self._is_duplicate_business(business_data, businesses):
                            businesses.append(business_data)
                            logger.info(f"Extracted data for: {business_data.get('name', 'Unknown Business')}")
                        else:
                            logger.info(f"Skipping duplicate business: {business_data.get('name', 'Unknown Business')}")
                    else:
                        logger.warning(f"Failed to extract data for business #{i+1}")
                    
                    # Go back to results if not the last item
                    if i < len(business_elements) - 1:
                        self.driver.back()
                        logger.info("Navigated back to search results")
                        
                        # Add delay after going back
                        time.sleep(random.uniform(2, 4))
                        
                        # Re-find elements as the DOM has changed
                        business_elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='article']")
                        
                        if not business_elements:
                            logger.info("Re-finding elements with alternative selector after back navigation")
                            business_elements = self.driver.find_elements(
                                By.XPATH, "//div[contains(@class, 'Nv2PK')]|//div[contains(@class, 'THOPZb')]")
                        
                        if not business_elements:
                            logger.error("Lost business listings after back navigation")
                            break
                        
                except Exception as e:
                    log_error(search_url, f"Error extracting business #{i+1}: {str(e)}")
                    continue
            
            return businesses
            
        except Exception as e:
            log_error(search_url, str(e))
            return []
        finally:
            # Close the driver
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _extract_business_data(self):
        """
        Extract business data from the current page.
        
        Returns:
            dict: A dictionary containing business data
        """
        if not self.driver:
            return None
            
        try:
            # Wait for business details to load with a longer timeout
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1, h2"))
                )
                logger.info("Business details loaded successfully")
            except TimeoutException:
                logger.warning("Timeout waiting for business details to load")
                # Try to continue anyway
            
            # Extract business name - try multiple selectors
            name = None
            
            # First attempt - try to extract from the URL which often contains the business name
            try:
                current_url = self.driver.current_url
                if "maps/place/" in current_url:
                    place_part = current_url.split("maps/place/")[1].split("/")[0]
                    # URL decode the name (convert %7C to |, %20 to space, etc.)
                    url_name = urllib.parse.unquote(place_part).replace("+", " ").title()
                    if url_name and url_name.lower() not in ["results", "sponsored"] and len(url_name) > 3:
                        name = url_name
                        logger.info(f"Extracted name from URL: {name}")
            except Exception as e:
                logger.debug(f"Failed to extract name from URL: {str(e)}")
            
            # Second attempt - standard h1 heading
            if not name:
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, "h1")
                    potential_name = name_element.text.strip()
                    if potential_name and potential_name.lower() not in ["results", "sponsored"] and len(potential_name) > 3:
                        name = potential_name
                except NoSuchElementException:
                    pass
                
            # Third attempt - try to find the business name in any heading element
            if not name:
                try:
                    name_elements = self.driver.find_elements(By.XPATH, "//h1 | //h2 | //h3")
                    for element in name_elements:
                        potential_name = element.text.strip()
                        if potential_name and potential_name.lower() not in ["results", "sponsored"] and len(potential_name) > 3:
                            name = potential_name
                            break
                except Exception:
                    pass
                    
            if not name:
                try:
                    # Try another approach - look for the first large text element
                    name_element = self.driver.find_element(
                        By.XPATH, "//div[contains(@class, 'fontHeadlineLarge') or contains(@class, 'fontTitleLarge')]")
                    name = name_element.text.strip()
                except NoSuchElementException:
                    pass
                    
            if not name:
                try:
                    # Last resort - try to find any prominent text that might be a business name
                    # Look for elements with large font or prominent position
                    elements = self.driver.find_elements(
                        By.XPATH, "//div[contains(@class, 'font') and not(contains(., 'Results'))]")
                    for element in elements:
                        text = element.text.strip()
                        if text and text.lower() != "results" and len(text) > 3 and len(text) < 50:
                            name = text
                            break
                except Exception:
                    pass
                    
            # Fourth attempt - try to extract from meta tags
            if not name:
                try:
                    meta_title = self.driver.execute_script("return document.title")
                    if meta_title and "Google Maps" in meta_title:
                        # Format is usually "Business Name - Google Maps"
                        business_part = meta_title.split(" - Google Maps")[0].strip()
                        if business_part and business_part.lower() not in ["results", "sponsored"] and len(business_part) > 3:
                            name = business_part
                            logger.info(f"Extracted name from page title: {name}")
                except Exception as e:
                    logger.debug(f"Failed to extract name from meta tags: {str(e)}")
            
            # Fifth attempt - look for business card elements
            if not name:
                try:
                    # Look for elements that might contain business info
                    card_elements = self.driver.find_elements(
                        By.XPATH, "//div[contains(@class, 'card')]//span | //div[contains(@class, 'section')]//span")
                    for element in card_elements:
                        text = element.text.strip()
                        if text and text.lower() not in ["results", "sponsored"] and len(text) > 3 and len(text) < 50:
                            name = text
                            logger.info(f"Extracted name from business card: {name}")
                            break
                except Exception as e:
                    logger.debug(f"Failed to extract name from business card: {str(e)}")
                    
            # Last resort - if we still don't have a name, try to generate one from the website domain
            if not name or name.lower() in ["results", "sponsored"]:
                try:
                    # Try to extract from website URL if available
                    website_element = self.driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']")
                    website_url = website_element.get_attribute("href")
                    if website_url:
                        from urllib.parse import urlparse
                        domain = urlparse(website_url).netloc
                        # Remove www. and .com/.org etc.
                        domain_parts = domain.split('.')
                        if len(domain_parts) > 1:
                            if domain_parts[0].lower() == 'www':
                                name = domain_parts[1].title()
                            else:
                                name = domain_parts[0].title()
                            logger.info(f"Generated name from website domain: {name}")
                except Exception as e:
                    logger.debug(f"Failed to generate name from website: {str(e)}")
                    
            # If all else fails, use a generic name with the current timestamp
            if not name or name.lower() in ["results", "sponsored"]:
                import time
                name = f"Business_{int(time.time())}"  
                logger.warning(f"Using generic name: {name}")
            
            if not name:
                logger.error("Business name is empty")
                return None
                
            logger.info(f"Extracted business name: {name}")
            
            # Initialize data dictionary
            business_data = {
                "name": name,
                "website": None,
                "phone_number": None
            }
            
            # Extract website URL if available - try multiple approaches
            website_found = False
            
            # Approach 1: Look for authority link
            try:
                website_element = self.driver.find_element(
                    By.CSS_SELECTOR, "a[data-item-id='authority']"
                )
                website_url = website_element.get_attribute("href")
                if website_url:
                    business_data["website"] = website_url
                    website_found = True
                    logger.info(f"Found website (method 1): {website_url}")
            except NoSuchElementException:
                pass
            
            # Approach 2: Look for website text
            if not website_found:
                try:
                    website_elements = self.driver.find_elements(
                        By.XPATH, "//a[contains(., 'Website') or contains(., 'website')]"
                    )
                    if website_elements:
                        website_url = website_elements[0].get_attribute("href")
                        if website_url:
                            business_data["website"] = website_url
                            website_found = True
                            logger.info(f"Found website (method 2): {website_url}")
                except Exception:
                    pass
            
            # Approach 3: Look for any non-Google link
            if not website_found:
                try:
                    # Find all links and filter out Google links
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in all_links:
                        href = link.get_attribute("href")
                        if href and "google.com" not in href and href.startswith("http"):
                            business_data["website"] = href
                            website_found = True
                            logger.info(f"Found website (method 3): {href}")
                            break
                except Exception as e:
                    logger.debug(f"Error in website extraction method 3: {str(e)}")
            
            # Extract phone number if available - try multiple approaches
            phone_found = False
            
            # Approach 1: Look for phone button
            try:
                phone_elements = self.driver.find_elements(
                    By.XPATH, "//button[contains(@data-item-id, 'phone:')]"
                )
                if phone_elements:
                    phone_number = phone_elements[0].text.strip()
                    if phone_number:
                        business_data["phone_number"] = phone_number
                        phone_found = True
                        logger.info(f"Found phone (method 1): {phone_number}")
            except Exception:
                pass
            
            # Approach 2: Look for phone text
            if not phone_found:
                try:
                    phone_elements = self.driver.find_elements(
                        By.XPATH, "//button[contains(., 'phone') or contains(., 'Phone')]"
                    )
                    if phone_elements:
                        phone_number = phone_elements[0].text.strip()
                        if phone_number:
                            business_data["phone_number"] = phone_number
                            phone_found = True
                            logger.info(f"Found phone (method 2): {phone_number}")
                except Exception:
                    pass
            
            # Approach 3: Look for any text that looks like a phone number
            if not phone_found:
                try:
                    # Find all text on the page
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    # Use regex to find phone numbers
                    import re
                    phone_pattern = r'\+?\d{1,4}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
                    phone_matches = re.findall(phone_pattern, page_text)
                    if phone_matches:
                        business_data["phone_number"] = phone_matches[0]
                        logger.info(f"Found phone (method 3): {phone_matches[0]}")
                except Exception as e:
                    logger.debug(f"Error in phone extraction method 3: {str(e)}")
                
            return business_data
            
        except Exception as e:
            logger.error(f"Error extracting business data: {str(e)}")
            return None
            
    def close(self):
        """Close the WebDriver if it's open."""
        if self.driver:
            self.driver.quit()
            self.driver = None
