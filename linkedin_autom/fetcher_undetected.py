"""
LinkedIn Cookie Fetcher - Undetected Version
This script uses undetected-chromedriver to bypass LinkedIn's bot detection.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_recaptcha_solver import RecaptchaSolver
import time
import os
import json
import random


class LinkedInCookieFetcherUndetected:
    def __init__(self, email=None, password=None):
        """
        Initialize the LinkedIn cookie fetcher with undetected-chromedriver.
        
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
        Set up undetected Chrome WebDriver.
        
        undetected-chromedriver handles most anti-detection automatically:
        - Removes automation flags
        - Patches webdriver property
        - Uses stealth mode by default
        - Rotates user agents
        
        Args:
            headless: Whether to run browser in headless mode (default True for server environments)
        """
        options = uc.ChromeOptions()
        
        # Essential arguments for running Chrome in Docker/VPS
        if headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # Window size
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # Additional stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # Set preferences
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Set binary location if specified
        chrome_bin = os.getenv('CHROME_BIN')
        if chrome_bin:
            options.binary_location = chrome_bin
        
        try:
            # Initialize undetected Chrome
            # version_main parameter helps ensure compatibility
            driver_path = os.getenv('CHROMEDRIVER_PATH')
            
            # Check if driver_path exists and is accessible
            if driver_path and os.path.exists(driver_path):
                try:
                    # Check if we have execute permissions
                    if os.access(driver_path, os.X_OK):
                        self.driver = uc.Chrome(
                            options=options,
                            driver_executable_path=driver_path,
                            use_subprocess=True,
                            version_main=None  # Auto-detect Chrome version
                        )
                    else:
                        print(f"⚠️  No execute permission for {driver_path}, using auto-detection")
                        self.driver = uc.Chrome(
                            options=options,
                            use_subprocess=True,
                            version_main=None
                        )
                except Exception as e:
                    print(f"⚠️  Error using specified driver path: {str(e)}")
                    print("⚠️  Falling back to auto-detection")
                    self.driver = uc.Chrome(
                        options=options,
                        use_subprocess=True,
                        version_main=None
                    )
            else:
                self.driver = uc.Chrome(
                    options=options,
                    use_subprocess=True,
                    version_main=None
                )
            
            print("✓ Undetected Chrome initialized")
            
            # Additional anti-detection measures
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": self.driver.execute_script("return navigator.userAgent").replace("Headless", ""),
                "platform": "Win32"
            })
            
            # Initialize reCAPTCHA solver
            try:
                self.recaptcha_solver = RecaptchaSolver(driver=self.driver)
                print("✓ CAPTCHA solver initialized")
            except Exception as e:
                print(f"⚠️  CAPTCHA solver initialization warning: {str(e)}")
                
        except Exception as e:
            print(f"❌ Error initializing undetected Chrome: {str(e)}")
            raise
    
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
                        recaptcha_iframes = self.driver.find_elements(By.XPATH, '//iframe[@title="reCAPTCHA"]')
                        
                        if recaptcha_iframes:
                            print("✓ reCAPTCHA detected, solving...")
                            self.recaptcha_solver.click_recaptcha_v2(iframe=recaptcha_iframes[0])
                            print("✓ CAPTCHA solved successfully!")
                            time.sleep(3)
                        else:
                            print("⚠️  No standard CAPTCHA detected")
                            print("⚠️  This may require manual verification")
                            print("Waiting for verification to complete...")
                            
                            # Wait for user to complete verification or automatic redirect
                            WebDriverWait(self.driver, 120).until(
                                lambda d: "feed" in d.current_url or "mynetwork" in d.current_url
                            )
                            print("✓ Verification completed!")
                                
                    except Exception as captcha_error:
                        print(f"⚠️  CAPTCHA solving error: {str(captcha_error)}")
                        print("⚠️  Waiting for manual verification or automatic resolution...")
                        
                        # Wait for verification to complete
                        try:
                            WebDriverWait(self.driver, 120).until(
                                lambda d: "feed" in d.current_url or "mynetwork" in d.current_url
                            )
                            print("✓ Verification completed!")
                        except Exception:
                            print("❌ Verification timeout")
                            return False
                else:
                    print("⚠️  No CAPTCHA solver available")
                    print("Waiting for manual verification...")
                    
                    try:
                        WebDriverWait(self.driver, 120).until(
                            lambda d: "feed" in d.current_url or "mynetwork" in d.current_url
                        )
                        print("✓ Verification completed!")
                    except Exception:
                        print("❌ Verification timeout")
                        return False
            
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
    Main function to run the LinkedIn cookie fetcher with undetected-chromedriver.
    """
    print("=" * 60)
    print("LinkedIn Cookie Fetcher (Undetected)")
    print("=" * 60)
    
    try:
        # Initialize the fetcher
        fetcher = LinkedInCookieFetcherUndetected()
        
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
