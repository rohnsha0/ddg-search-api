# LinkedIn Cookie Fetcher

A Python script that automates logging into LinkedIn and fetches the `JSESSIONID` and `li_at` cookies.

## Features

- Automated LinkedIn login using Selenium WebDriver
- Fetches `JSESSIONID` and `li_at` cookies
- Handles security checkpoints and 2FA verification
- Saves cookies to a JSON file for later use
- Anti-detection measures to avoid bot detection

## Prerequisites

1. **Python 3.7+**
2. **Chrome Browser** installed on your system
3. **ChromeDriver** (Selenium will try to manage this automatically)

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Method 1: Using Environment Variables (Recommended)

Set your LinkedIn credentials as environment variables:

```bash
export LINKEDIN_EMAIL="your-email@example.com"
export LINKEDIN_PASSWORD="your-password"
```

Then run the script:

```bash
python mainn.py
```

### Method 2: Modify the Script

You can also modify the script to pass credentials directly:

```python
# In the main() function, change:
fetcher = LinkedInCookieFetcher(
    email="your-email@example.com",
    password="your-password"
)
```

## How It Works

1. **Browser Setup**: Opens Chrome with anti-detection settings
2. **Login**: Navigates to LinkedIn login page and enters credentials
3. **Security Verification**: If LinkedIn requires verification (2FA, captcha, etc.), the script will pause and wait for you to complete it manually
4. **Cookie Extraction**: Once logged in, extracts the cookies
5. **Save to File**: Saves cookies to `linkedin_cookies.json`

## Output

The script will:
- Display progress messages in the console
- Print the retrieved cookies
- Save cookies to `linkedin_cookies.json` in the following format:

```json
{
    "JSESSIONID": "ajax:1234567890123456789",
    "li_at": "AQEDATxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

## Configuration Options

You can modify the script behavior:

- **Headless Mode**: Set `headless=True` in `setup_driver()` to run without opening a browser window
- **Cookie File Name**: Change `filename` parameter in `save_cookies_to_file()`

## Important Notes

⚠️ **Security Considerations:**
- Never commit your credentials to version control
- Store credentials securely using environment variables
- The cookies provide access to your LinkedIn account - keep them secure
- Cookies typically expire after some time

⚠️ **LinkedIn Terms of Service:**
- This script is for educational purposes
- Be aware of LinkedIn's terms of service regarding automation
- Use responsibly and don't abuse the platform

⚠️ **Rate Limiting:**
- LinkedIn may detect automated behavior and require verification
- The script handles security checkpoints by pausing for manual intervention
- If you see frequent security checks, reduce usage frequency

## Troubleshooting

### ChromeDriver Issues
If you get ChromeDriver errors, you may need to install it manually:
```bash
# Ubuntu/Debian
sudo apt-get install chromium-chromedriver

# Arch Linux
sudo pacman -S chromium chromedriver
```

### Browser Not Found
Ensure Chrome/Chromium is installed on your system.

### Login Fails
- Check your credentials are correct
- LinkedIn may require manual verification - complete it when prompted
- Try running with `headless=False` to see what's happening

## License

MIT License - Use at your own risk.
