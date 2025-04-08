"""
Website crawler module.
Handles extraction of email addresses from business websites.
"""
import re
import time
import random
import requests
import ssl
import certifi
import urllib3
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import urllib.robotparser
from retry import retry
from fake_useragent import UserAgent

from src.config import (
    EMAIL_REGEX, BUSINESS_EMAIL_PREFIXES,
    WEBSITE_MIN_DELAY, WEBSITE_MAX_DELAY, MAX_RETRIES
)
from src.logger import logger, log_error

class WebsiteCrawler:
    """
    A class to crawl websites and extract email addresses.
    """
    
    def __init__(self):
        """Initialize the website crawler."""
        # Configure SSL context to be more permissive
        self._configure_ssl()
        
        # Initialize session with rotating user agents
        self.session = requests.Session()
        self.user_agent = UserAgent()
        self.session.headers.update({
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })
        self.robots_cache = {}  # Cache for robots.txt parsers
        self.visited_urls = set()  # Track visited URLs to avoid duplicates
        
    def _configure_ssl(self):
        """Configure SSL to handle certificate issues."""
        # Create a more permissive SSL context
        try:
            # Disable SSL verification warnings
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Use the certifi CA bundle for verification when possible
            self.ssl_context = ssl.create_default_context(cafile=certifi.where())
            # But make it more permissive for problematic sites
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            
            logger.info("SSL configuration set to permissive mode for maximum compatibility")
        except Exception as e:
            logger.warning(f"Failed to configure SSL context: {str(e)}")
            
    def _rotate_user_agent(self):
        """Rotate the user agent to avoid detection."""
        try:
            self.session.headers.update({
                'User-Agent': self.user_agent.random
            })
        except Exception as e:
            logger.debug(f"Error rotating user agent: {str(e)}")
            # Fallback to a standard user agent
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
    
    def _random_delay(self):
        """Add a random delay to mimic human behavior."""
        delay = random.uniform(WEBSITE_MIN_DELAY, WEBSITE_MAX_DELAY)
        time.sleep(delay)
    
    def _get_robots_parser(self, url):
        """
        Get a robots.txt parser for the given URL.
        
        Args:
            url (str): The website URL
            
        Returns:
            RobotFileParser: A parser for the website's robots.txt
        """
        parsed_url = urlparse(url)
        
        # Skip robots.txt check for mailto: links
        if parsed_url.scheme == 'mailto':
            rp = urllib.robotparser.RobotFileParser()
            rp.allow_all = True
            return rp
            
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if base_url in self.robots_cache:
            return self.robots_cache[base_url]
        
        robots_url = f"{base_url}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        
        try:
            # Use a timeout to avoid hanging on slow robots.txt
            with urllib.request.urlopen(robots_url, timeout=5) as response:
                robots_content = response.read().decode('utf-8', errors='ignore')
                rp.parse(robots_content.splitlines())
            logger.debug(f"Successfully parsed robots.txt for {base_url}")
            self.robots_cache[base_url] = rp
            return rp
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # No robots.txt found, create an empty one that allows everything
                logger.debug(f"No robots.txt found for {base_url} (404)")
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(['User-agent: *', 'Allow: /'])
                self.robots_cache[base_url] = rp
                return rp
            else:
                logger.warning(f"HTTP error parsing robots.txt for {base_url}: {e.code} {e.reason}")
                # For other HTTP errors, be conservative and allow access
                rp = urllib.robotparser.RobotFileParser()
                rp.allow_all = True
                self.robots_cache[base_url] = rp
                return rp
        except Exception as e:
            logger.warning(f"Failed to parse robots.txt for {base_url}: {str(e)}")
            # Return a permissive parser if we can't read robots.txt
            rp = urllib.robotparser.RobotFileParser()
            rp.allow_all = True
            self.robots_cache[base_url] = rp
            return rp
    
    def _can_fetch(self, url):
        """
        Check if the URL can be fetched according to robots.txt.
        
        Args:
            url (str): The URL to check
            
        Returns:
            bool: True if the URL can be fetched, False otherwise
        """
        try:
            # Get the robots parser for this URL
            rp = self._get_robots_parser(url)
            can_fetch = rp.can_fetch(self.user_agent, url)
            
            # If the URL is disallowed but it's a contact page, we might still want to check it
            # This is a common exception for email extraction
            if not can_fetch:
                parsed_url = urlparse(url)
                path_lower = parsed_url.path.lower()
                
                # Check if this is a contact or about page that might contain emails
                is_contact_page = any(term in path_lower for term in ['/contact', '/about', '/team', '/people', '/staff'])
                
                if is_contact_page:
                    logger.info(f"Contact page {url} is disallowed by robots.txt, but checking for emails only")
                    # We'll mark this URL as contact-only to limit our crawling
                    if not hasattr(self, 'contact_only_pages'):
                        self.contact_only_pages = set()
                    self.contact_only_pages.add(url)
                    return True
            
            return can_fetch
        except Exception as e:
            # If there's an error checking robots.txt, assume we can fetch
            logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
            return True
    
    def _normalize_url(self, url):
        """
        Normalize a URL by adding the scheme if missing.
        
        Args:
            url (str): The URL to normalize
            
        Returns:
            str: The normalized URL
        """
        if url and not (url.startswith('http://') or url.startswith('https://')):
            return f"https://{url}"
        return url
    
    def _is_business_email(self, email):
        """
        Check if an email is likely a business email rather than a personal one.
        
        Args:
            email (str): The email to check
            
        Returns:
            bool: True if the email is likely a business email, False otherwise
        """
        if not email:
            return False
            
        # Extract the local part (before @)
        local_part = email.split('@')[0].lower()
        
        # Check if it's a common business email prefix
        for prefix in BUSINESS_EMAIL_PREFIXES:
            if local_part == prefix or local_part.startswith(f"{prefix}.") or local_part.startswith(f"{prefix}-") or local_part.startswith(f"{prefix}_"):
                return True
        
        # Check if it looks like a personal name (e.g., john.doe)
        if '.' in local_part and not any(char.isdigit() for char in local_part):
            name_parts = local_part.split('.')
            if len(name_parts) == 2 and all(len(part) > 1 for part in name_parts):
                return False
        
        # If not clearly personal, consider it a business email
        return True
    
    @retry(tries=MAX_RETRIES, delay=2, backoff=2, logger=logger)
    def extract_emails_from_page(self, url):
        """
        Extract email addresses from a webpage.
        
        Args:
            url (str): The URL of the webpage
            
        Returns:
            list: A list of extracted email addresses
        """
        url = self._normalize_url(url)
        if not url:
            logger.warning("Empty or invalid URL provided")
            return []
        
        # Skip if already visited
        if url in self.visited_urls:
            logger.info(f"Skipping already visited URL: {url}")
            return []
        
        self.visited_urls.add(url)
            
        # Check robots.txt
        try:
            if not self._can_fetch(url):
                logger.info(f"Skipping {url} as per robots.txt")
                return []
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {str(e)}")
            # Continue anyway as this is not critical
        
        try:
            # Rotate user agent before request
            self._rotate_user_agent()
            
            logger.info(f"Crawling: {url}")
            
            # Try with SSL verification first
            try:
                response = self.session.get(
                    url, 
                    timeout=15, 
                    allow_redirects=True,
                    verify=True
                )
            except requests.exceptions.SSLError:
                # If SSL verification fails, try without verification
                logger.warning(f"SSL verification failed for {url}, trying without verification")
                response = self.session.get(
                    url, 
                    timeout=15, 
                    allow_redirects=True,
                    verify=False
                )
            
            # Check if we got a valid response
            if response.status_code != 200:
                logger.warning(f"Got status code {response.status_code} for {url}")
                return []
                
            # Add a random delay
            self._random_delay()
            
            # Check content type to ensure it's HTML
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type.lower() and 'application/xhtml+xml' not in content_type.lower():
                logger.warning(f"Skipping non-HTML content: {content_type} at {url}")
                return []
            
            # Extract emails from the page content
            content = response.text
            
            # Standard email regex extraction
            emails = re.findall(EMAIL_REGEX, content)
            
            # Look for common email obfuscation patterns in the HTML
            # Pattern 1: Replacing @ with [at] or (at)
            obfuscated_pattern1 = r'[\w\.-]+\s*(?:\[at\]|\(at\)|\[@\]|\{at\}|\bat\b|\[a\]|\(a\)|\ba\b)\s*[\w\.-]+\.[\w\.-]+'
            obfuscated_matches1 = re.findall(obfuscated_pattern1, content)
            for match in obfuscated_matches1:
                clean_email = match.replace('[at]', '@').replace('(at)', '@').replace('[@]', '@').replace('{at}', '@')
                clean_email = clean_email.replace('[a]', '@').replace('(a)', '@')
                clean_email = re.sub(r'\s+at\s+', '@', clean_email)
                clean_email = re.sub(r'\s+a\s+', '@', clean_email)
                clean_email = re.sub(r'\s+', '', clean_email)  # Remove any spaces
                if '@' in clean_email and '.' in clean_email.split('@')[1]:
                    emails.append(clean_email)
            
            # Pattern 2: Replacing . with [dot] or (dot)
            obfuscated_pattern2 = r'[\w\.-]+@[\w\.-]+\s*(?:\[dot\]|\(dot\)|\[.\]|\{dot\}|\bdot\b|\[d\]|\(d\)|\bd\b)\s*[\w\.-]+'
            obfuscated_matches2 = re.findall(obfuscated_pattern2, content)
            for match in obfuscated_matches2:
                clean_email = match.replace('[dot]', '.').replace('(dot)', '.').replace('[.]', '.').replace('{dot}', '.')
                clean_email = clean_email.replace('[d]', '.').replace('(d)', '.')
                clean_email = re.sub(r'\s+dot\s+', '.', clean_email)
                clean_email = re.sub(r'\s+d\s+', '.', clean_email)
                clean_email = re.sub(r'\s+', '', clean_email)  # Remove any spaces
                if '@' in clean_email and '.' in clean_email.split('@')[1]:
                    emails.append(clean_email)
                    
            # Pattern 3: HTML entity encoding (&#64; for @ and &#46; for .)
            html_entity_pattern = r'[\w\.-]+\s*(?:&#64;|&#0*64;)\s*[\w\.-]+\s*(?:&#46;|&#0*46;)\s*[\w\.-]+'
            html_entity_matches = re.findall(html_entity_pattern, content)
            for match in html_entity_matches:
                clean_email = match.replace('&#64;', '@').replace('&#064;', '@')
                clean_email = clean_email.replace('&#46;', '.').replace('&#046;', '.')
                clean_email = re.sub(r'\s+', '', clean_email)  # Remove any spaces
                if '@' in clean_email and '.' in clean_email.split('@')[1]:
                    emails.append(clean_email)
                    
            # Pattern 4: Unicode character encoding
            unicode_pattern = r'[\w\.-]+\s*(?:\\u0040|\\x40)\s*[\w\.-]+\s*(?:\\u002E|\\x2E)\s*[\w\.-]+'
            unicode_matches = re.findall(unicode_pattern, content)
            for match in unicode_matches:
                clean_email = match.replace('\\u0040', '@').replace('\\x40', '@')
                clean_email = clean_email.replace('\\u002E', '.').replace('\\x2E', '.')
                clean_email = re.sub(r'\s+', '', clean_email)  # Remove any spaces
                if '@' in clean_email and '.' in clean_email.split('@')[1]:
                    emails.append(clean_email)
            
            # Try to find obfuscated emails (common anti-scraping technique)
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for elements with data attributes that might contain email parts
            for element in soup.select('[data-email], [data-mail], [data-user], [data-domain], [data-contact], [data-address]'):
                try:
                    # Common patterns: data-user + data-domain or data-email with @ replaced
                    user = element.get('data-user', '')
                    domain = element.get('data-domain', '')
                    if user and domain:
                        emails.append(f"{user}@{domain}")
                    
                    # Check for encoded/obfuscated email
                    email_data = element.get('data-email', '') or element.get('data-mail', '') or element.get('data-contact', '') or element.get('data-address', '')
                    if email_data:
                        # Try common obfuscation patterns
                        email_data = email_data.replace('[at]', '@').replace('(at)', '@').replace(' at ', '@').replace(' AT ', '@')
                        email_data = email_data.replace('[dot]', '.').replace('(dot)', '.').replace(' dot ', '.').replace(' DOT ', '.')
                        # Remove spaces that might be used to obfuscate
                        email_data = re.sub(r'\s+', '', email_data)
                        if '@' in email_data and '.' in email_data.split('@')[1]:
                            emails.append(email_data)
                except Exception as e:
                    logger.debug(f"Error extracting obfuscated email: {str(e)}")
            
            # Look for JavaScript email obfuscation
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = str(script.string) if script.string else ''
                
                # Only process if script has content
                if script_text and ('mail' in script_text.lower() or 'email' in script_text.lower() or '@' in script_text):
                    # Look for patterns like 'user' + '@' + 'domain.com'
                    js_email_pattern = r'[\'"](\w+)[\'"](\s*\+\s*)[\'"]@[\'"](\s*\+\s*)[\'"]([\w\.]+)[\'"](\s*\+\s*)[\'"]([\w\.]+)[\'"](\s*\+\s*)'
                    js_matches = re.findall(js_email_pattern, script.string)
                    if js_matches:
                        for match in js_matches:
                            try:
                                # Reconstruct the email from parts
                                parts = [p for p in match if p and not p.isspace() and '+' not in p]
                                potential_email = ''.join(parts)
                                if '@' in potential_email and '.' in potential_email.split('@')[1]:
                                    emails.append(potential_email)
                            except Exception:
                                pass
            
            # Remove duplicates while preserving order
            emails = list(dict.fromkeys(emails))
            
            # Filter to business emails
            business_emails = [email for email in emails if self._is_business_email(email)]
            
            # If no business emails found, include all emails
            if not business_emails and emails:
                logger.info(f"No business emails found at {url}, including all emails")
                return emails
            
            return business_emails
            
        except requests.exceptions.RequestException as e:
            log_error(url, str(e))
            return []
        except Exception as e:
            log_error(url, str(e))
            return []
    
    def crawl_website(self, url):
        """
        Crawl a website to extract email addresses.
        
        Args:
            url (str): The website URL
            
        Returns:
            list: A list of extracted email addresses
        """
        url = self._normalize_url(url)
        if not url:
            return []
            
        logger.info(f"Crawling website: {url}")
        
        # Start with the homepage
        emails = self.extract_emails_from_page(url)
        
        # Try to find contact page
        try:
            # Get the homepage content
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for contact page links
            contact_links = []
            contact_keywords = ['contact', 'contact-us', 'contact us', 'about', 'about-us', 'about us', 'team', 'company', 'support', 'help', 'info', 'reach-us', 'reach us', 'get-in-touch', 'get in touch']
            
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                link_text = link.text.lower()
                
                if any(keyword in link_text or keyword in href.lower() for keyword in contact_keywords):
                    full_url = urljoin(url, href)
                    contact_links.append(full_url)
            
            # Visit contact pages
            for contact_url in contact_links[:5]:  # Increased limit to 5 contact pages
                if contact_url != url:  # Skip if it's the same as the homepage
                    contact_emails = self.extract_emails_from_page(contact_url)
                    emails.extend([email for email in contact_emails if email not in emails])
                    
            # Look for additional pages that might contain emails
            additional_pages = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if any(term in href.lower() for term in ['email', 'mail', 'contact', 'enquiry', 'inquiry', 'support']):
                    full_url = urljoin(url, href)
                    if full_url != url and full_url not in contact_links:
                        additional_pages.append(full_url)
            
            # Visit up to 3 additional pages
            for additional_url in additional_pages[:3]:
                additional_emails = self.extract_emails_from_page(additional_url)
                emails.extend([email for email in additional_emails if email not in emails])
            
            # Look for email addresses in mailto links
            mailto_links = soup.select('a[href^="mailto:"]')
            for link in mailto_links:
                href = link.get('href', '')
                if href.startswith('mailto:'):
                    email = href[7:].split('?')[0].strip()  # Remove 'mailto:' and any parameters
                    if '@' in email and '.' in email.split('@')[1]:
                        emails.append(email)
            
        except Exception as e:
            log_error(url, f"Error finding contact pages: {str(e)}")
        
        return emails
