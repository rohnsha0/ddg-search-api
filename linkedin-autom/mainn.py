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
import time
import os
import json


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
        
        if not self.email or not self.password:
            raise ValueError("LinkedIn credentials not provided. Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables or pass them as arguments.")
    
    def setup_driver(self, headless=False):
        """
        Set up the Chrome WebDriver with appropriate options.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent to avoid detection
        chrome_options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def login(self):
        """
        Log into LinkedIn and wait for successful authentication.
        """
        try:
            print("Navigating to LinkedIn login page...")
            self.driver.get('https://www.linkedin.com/login')
            
            # Wait for the page to load
            time.sleep(2)
            
            # Find and fill email field
            print("Entering email...")
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            
            # Find and fill password field
            print("Entering password...")
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            print("Clicking login button...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for navigation after login
            print("Waiting for login to complete...")
            time.sleep(5)
            
            # Check if we need to handle security verification
            current_url = self.driver.current_url
            if "checkpoint" in current_url or "challenge" in current_url:
                print("\n⚠️  Security checkpoint detected!")
                print("Please complete the security verification in the browser window.")
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
        
        # Set up the driver (set headless=False to see the browser)
        fetcher.setup_driver(headless=False)
        
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
