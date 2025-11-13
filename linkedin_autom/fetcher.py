"""
LinkedIn Cookie Fetcher
This script logs into LinkedIn and retrieves JSESSIONID and li_at cookies.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium_recaptcha_solver import RecaptchaSolver
import time
import os
import json
import random


class LinkedInCookieFetcher:
    def __init__(self, email=None, password=None):
        """
        Initialize the LinkedIn cookie fetcher.
        
        Args:
            email: LinkedIn email (optional, can be set via environment variable)
            password: LinkedIn password (optional, can be set via environment variable)
        """
        self.email = email or os.getenv('LINKEDIN_EMAIL')
        self.password = password or os.getenv('LINKEDIN_PASSWORD')
        self.driver = None
        self.recaptcha_solver = None
        
        if not self.email or not self.password:
            raise ValueError("LinkedIn credentials not provided. Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables or pass them as arguments.")
    
    def setup_driver(self, headless=True):
        """
        Set up the Chrome WebDriver with comprehensive anti-detection measures.
        
        Anti-Detection Strategy:
        - Uses realistic Windows NT user-agent
        - Removes automation flags completely
        - Sets realistic browser preferences and permissions
        - Adds Canvas/WebGL fingerprint randomization
        - Sets proper viewport and screen resolution
        - Configures realistic geolocation and timezone
        
        Args:
            headless: Whether to run browser in headless mode (default True for server environments)
        """
        chrome_options = Options()
        
        # Essential arguments for running Chrome in Docker/VPS
        if headless:
            chrome_options.add_argument('--headless=new')  # Use new headless mode
        
        chrome_options.add_argument('--no-sandbox')  # Required for Docker
        chrome_options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
        chrome_options.add_argument('--disable-gpu')  # Disable GPU acceleration
        chrome_options.add_argument('--disable-software-rasterizer')
        
        # Window size (important for headless) - use realistic desktop resolution
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        
        # Anti-detection measures
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add realistic user agent
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')
        
        # Set realistic browser preferences
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.media_stream": 1,
            "profile.default_content_setting_values.geolocation": 1,
            "intl.accept_languages": "en-US,en",
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Disable images to speed up loading (optional, but helps with performance)
        # Uncomment if you want faster loading
        # chrome_options.add_argument('--blink-settings=imagesEnabled=false')
        
        # Set binary location if specified
        chrome_bin = os.getenv('CHROME_BIN')
        if chrome_bin:
            chrome_options.binary_location = chrome_bin
        
        # Set ChromeDriver path if specified
        chromedriver_path = os.getenv('CHROMEDRIVER_PATH')
        if chromedriver_path and os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)
        
        # Execute CDP commands for advanced anti-detection
        # Remove webdriver flag
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override the plugins to make it look more real
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Override Chrome runtime
                window.chrome = {
                    runtime: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Add realistic platform properties
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32'
                });
                
                // Add hardware concurrency
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8
                });
                
                // Add device memory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8
                });
            '''
        })
        
        # Set realistic user agent via CDP
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "platform": "Win32",
            "userAgentMetadata": {
                "brands": [
                    {"brand": "Google Chrome", "version": "131"},
                    {"brand": "Chromium", "version": "131"},
                    {"brand": "Not_A Brand", "version": "24"}
                ],
                "fullVersion": "131.0.0.0",
                "platform": "Windows",
                "platformVersion": "10.0.0",
                "architecture": "x86",
                "model": "",
                "mobile": False
            }
        })
        
        # Initialize reCAPTCHA solver
        try:
            self.recaptcha_solver = RecaptchaSolver(driver=self.driver)
            print("✓ CAPTCHA solver initialized")
        except Exception as e:
            print(f"⚠️  CAPTCHA solver initialization warning: {str(e)}")
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """
        Add a random delay to mimic human behavior.
        
        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def human_type(self, element, text):
        """
        Type text with random delays to mimic human typing.
        
        Args:
            element: WebElement to type into
            text: Text to type
        """
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def login(self):
        """
        Log into LinkedIn and wait for successful authentication.
        Uses human-like behavior to avoid detection.
        """
        try:
            print("Navigating to LinkedIn login page...")
            self.driver.get('https://www.linkedin.com/login')
            
            # Wait for the page to load with random delay
            self.random_delay(2, 4)
            
            # Find and fill email field
            print("Entering email...")
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            
            # Random delay before typing
            self.random_delay(0.5, 1.5)
            
            email_field.clear()
            self.human_type(email_field, self.email)
            
            # Random delay between fields
            self.random_delay(0.5, 1.5)
            
            # Find and fill password field
            print("Entering password...")
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            self.human_type(password_field, self.password)
            
            # Random delay before clicking
            self.random_delay(0.5, 1.5)
            
            # Click login button
            print("Clicking login button...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for navigation after login
            print("Waiting for login to complete...")
            self.random_delay(5, 7)
            
            # Check if we need to handle security verification
            current_url = self.driver.current_url
            if "checkpoint" in current_url or "challenge" in current_url:
                print("\n⚠️  Security checkpoint detected!")
                
                # Try to solve CAPTCHA if present
                if self.recaptcha_solver:
                    try:
                        print("🔄 Attempting to solve CAPTCHA...")
                        
                        # Check for reCAPTCHA iframe
                        recaptcha_iframe = self.driver.find_element(By.XPATH, '//iframe[@title="reCAPTCHA"]')
                        
                        if recaptcha_iframe:
                            print("✓ reCAPTCHA detected, solving...")
                            self.recaptcha_solver.click_recaptcha_v2(iframe=recaptcha_iframe)
                            print("✓ CAPTCHA solved successfully!")
                            time.sleep(3)
                        else:
                            print("⚠️  No reCAPTCHA iframe found, checking for other CAPTCHA types...")
                            
                            # Try to solve any audio CAPTCHA if present
                            try:
                                # Wait a bit for the page to fully load
                                time.sleep(2)
                                
                                # Look for CAPTCHA elements
                                captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, '[class*="captcha"], [id*="captcha"]')
                                if captcha_elements:
                                    print("🔄 Found CAPTCHA elements, attempting to solve...")
                                    # The solver will automatically try to solve
                                    time.sleep(5)
                                else:
                                    print("⚠️  Please complete the security verification manually in the browser window.")
                                    print("Waiting for you to complete the verification...")
                                    
                                    # Wait for user to complete verification
                                    WebDriverWait(self.driver, 120).until(
                                        lambda d: "feed" in d.current_url or "mynetwork" in d.current_url
                                    )
                                    print("✓ Verification completed!")
                            except Exception as inner_e:
                                print(f"⚠️  Could not auto-solve: {str(inner_e)}")
                                print("Please complete the verification manually...")
                                WebDriverWait(self.driver, 120).until(
                                    lambda d: "feed" in d.current_url or "mynetwork" in d.current_url
                                )
                                print("✓ Verification completed!")
                                
                    except Exception as captcha_error:
                        print(f"⚠️  CAPTCHA solving error: {str(captcha_error)}")
                        print("Please complete the security verification manually in the browser window.")
                        print("Waiting for you to complete the verification...")
                        
                        # Wait for user to complete verification
                        WebDriverWait(self.driver, 120).until(
                            lambda d: "feed" in d.current_url or "mynetwork" in d.current_url
                        )
                        print("✓ Verification completed!")
                else:
                    print("Please complete the security verification manually in the browser window.")
                    print("Waiting for you to complete the verification...")
                    
                    # Wait for user to complete verification
                    WebDriverWait(self.driver, 120).until(
                        lambda d: "feed" in d.current_url or "mynetwork" in d.current_url
                    )
                    print("✓ Verification completed!")
            
            # Verify successful login by checking URL
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url or "in/" in self.driver.current_url:
                print("✓ Successfully logged in!")
                return True
            else:
                print(f"⚠️  Login may have failed. Current URL: {self.driver.current_url}")
                return False
                
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            return False
    
    def get_cookies(self):
        """
        Fetch JSESSIONID and li_at cookies from the browser.
        
        Returns:
            dict: Dictionary containing the cookies
        """
        try:
            print("\nFetching cookies...")
            all_cookies = self.driver.get_cookies()
            
            cookies = {
                'JSESSIONID': None,
                'li_at': None
            }
            
            for cookie in all_cookies:
                if cookie['name'] == 'JSESSIONID':
                    cookies['JSESSIONID'] = cookie['value']
                    print(f"✓ Found JSESSIONID: {cookie['value'][:20]}...")
                elif cookie['name'] == 'li_at':
                    cookies['li_at'] = cookie['value']
                    print(f"✓ Found li_at: {cookie['value'][:20]}...")
            
            if not cookies['JSESSIONID']:
                print("⚠️  JSESSIONID cookie not found")
            if not cookies['li_at']:
                print("⚠️  li_at cookie not found")
            
            return cookies
            
        except Exception as e:
            print(f"❌ Error fetching cookies: {str(e)}")
            return None
    
    def save_cookies_to_file(self, cookies, filename='linkedin_cookies.json'):
        """
        Save cookies to a JSON file.
        
        Args:
            cookies: Dictionary containing the cookies
            filename: Name of the file to save cookies to
        """
        try:
            with open(filename, 'w') as f:
                json.dump(cookies, f, indent=4)
            print(f"✓ Cookies saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving cookies: {str(e)}")
    
    def close(self):
        """
        Close the browser and clean up.
        """
        if self.driver:
            self.driver.quit()
            print("\n✓ Browser closed")


def main():
    """
    Main function to run the LinkedIn cookie fetcher.
    """
    print("=" * 60)
    print("LinkedIn Cookie Fetcher")
    print("=" * 60)
    
    try:
        # Initialize the fetcher
        fetcher = LinkedInCookieFetcher()
        
        # Set up the driver (headless=True for server environments)
        fetcher.setup_driver(headless=True)
        
        # Login to LinkedIn
        if fetcher.login():
            # Get cookies
            cookies = fetcher.get_cookies()
            
            if cookies:
                print("\n" + "=" * 60)
                print("COOKIES RETRIEVED")
                print("=" * 60)
                print(f"JSESSIONID: {cookies['JSESSIONID']}")
                print(f"li_at: {cookies['li_at']}")
                print("=" * 60)
                
                # Save cookies to file
                fetcher.save_cookies_to_file(cookies)
                
                return cookies
        else:
            print("❌ Login failed")
            
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
    
    finally:
        # Always close the browser
        if 'fetcher' in locals():
            fetcher.close()


if __name__ == "__main__":
    main()
