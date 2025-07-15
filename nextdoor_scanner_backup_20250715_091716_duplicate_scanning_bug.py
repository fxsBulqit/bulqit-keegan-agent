#!/usr/bin/env python3
"""
Automated Nextdoor Scanner for Bulqit Service Opportunities
Uses Selenium + BeautifulSoup approach proven with Facebook

BACKUP CREATED: 2025-07-15 09:17:16
REASON: Duplicate scanning bug fix

CURRENT SITUATION:
- Scanner works perfectly and sends email successfully
- BUT crashes at the end with "'bool' object is not iterable"
- Issue: _login_to_nextdoor() contains complete scanning workflow (from backup)
- BUT run_scan() also tries to scan afterward, causing duplicate work
- _search_for_term() returns boolean but run_scan() expects list
- Fix: Remove duplicate scanning logic from run_scan() method
"""

import time
import random
import re
import os
import requests
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from nextdoor_groq_filter import NextdoorGroqFilter

class NextdoorScanner:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.service_opportunities = []
        self.groq_filter = NextdoorGroqFilter()
        self.github_token = os.getenv('GIST_TOKEN')
        self.current_gist_id = None
        
    def _setup_headless_driver(self):
        """Setup headless Chrome driver for Nextdoor"""
        print("🔧 Setting up Chrome for GitHub Actions environment")
            
        chrome_options = Options()
        
        # Always headless for GitHub Actions
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        # GitHub Actions specific setup - don't use user-data-dir
        chrome_options.add_argument("--remote-debugging-port=0")
        # Remove user-data-dir entirely for GitHub Actions
        # self.temp_dir = None  # No temp dir needed
        
        # Additional arguments to prevent conflicts
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-renderer-backgrounding") 
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Block notifications
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2
        })
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Clear all cookies and data
            self.driver.get("chrome://settings/clearBrowserData")
            time.sleep(2)
            self.driver.delete_all_cookies()
            
            self.wait = WebDriverWait(self.driver, 20)
            print("✅ Chrome driver initialized for Nextdoor (cookies cleared)")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Chrome driver: {str(e)}")
            return False

    def _type_letter_by_letter(self, element, text):
        """Type text letter by letter with human-like delays"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))

    def _login_to_nextdoor(self):
        """Login to Nextdoor automatically"""
        try:
            print("🌍 Navigating to Nextdoor news feed...")
            self.driver.get("https://nextdoor.com/news_feed/")
            
            # Wait for page to load
            time.sleep(5)
            
            print(f"📍 Current URL: {self.driver.current_url}")
            
            # Check if already logged in (successful access to news feed)
            if "news_feed" in self.driver.current_url and "login" not in self.driver.current_url:
                print("✅ Already logged in! Skipping login process.")
                # Continue to scanning workflow below
            else:
                # Check if redirected to login page (with next parameter pointing to news_feed)
                if "login" in self.driver.current_url:
                    print(f"🔐 Redirected to login page: {self.driver.current_url}")
                    print("🔑 Need to login to access news feed - proceeding with login...")
                else:
                    # If not redirected to login, manually go there
                    print("🌍 Navigating to login page...")
                    self.driver.get("https://nextdoor.com/login/")
                    time.sleep(3)
                    print(f"📍 Login page URL: {self.driver.current_url}")
                        
                # Find and fill email field
                email_selectors = [
                    'input[type="email"]',
                    'input[name="email"]',
                    '#email',
                    'input[placeholder*="email"]'
                ]
                
                email_field = None
                for selector in email_selectors:
                    try:
                        email_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        print(f"✅ Found email field with selector: {selector}")
                        break
                    except:
                        continue
                
                if not email_field:
                    print("❌ Could not find email field")
                    return False
                    
                print("📧 Typing email letter by letter...")
                self._type_letter_by_letter(email_field, "fxs@bulqit.com")
                
                # Human-like delay
                time.sleep(random.uniform(1, 2))
                
                # Find and fill password field
                password_selectors = [
                    'input[type="password"]',
                    'input[name="password"]',
                    '#password',
                    'input[placeholder*="password"]'
                ]
                
                password_field = None
                for selector in password_selectors:
                    try:
                        password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"✅ Found password field with selector: {selector}")
                        break
                    except:
                        continue
                
                if not password_field:
                    print("❌ Could not find password field")
                    return False
                    
                print("🔒 Typing password letter by letter...")
                self._type_letter_by_letter(password_field, "@Bulqit123!")
                
                # Another delay
                time.sleep(random.uniform(1, 2))
                
                # Find and click login button
                login_selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button:contains("Log in")',
                    'button:contains("Sign in")',
                    '[data-testid="login-button"]'
                ]
                
                login_button = None
                for selector in login_selectors:
                    try:
                        login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        print(f"✅ Found login button with selector: {selector}")
                        break
                    except:
                        continue
                
                if not login_button:
                    print("❌ Could not find login button")
                    return False
                    
                print("🔐 Clicking login button...")
                login_button.click()
                
                # Wait for login to process
                time.sleep(8)  # Longer wait for login processing
                
                # Check if browser is still alive
                try:
                    current_url = self.driver.current_url
                    print(f"📍 After login URL: {current_url}")
                except Exception as e:
                    print(f"❌ Browser session lost during login: {str(e)}")
                    return False
                
                # Check for 2FA requirement
                try:
                    needs_2fa = self._check_for_2fa()
                except Exception as e:
                    print(f"❌ Error checking for 2FA (browser may have crashed): {str(e)}")
                    return False
                    
                if needs_2fa:
                    print("🚨 2FA verification required - capturing HTML for analysis")
                    
                    # Save the 2FA page HTML for debugging
                    try:
                        with open('2fa_page.html', 'w', encoding='utf-8') as f:
                            f.write(self.driver.page_source)
                        print("✅ Saved 2FA page HTML as 2fa_page.html")
                    except Exception as e:
                        print(f"⚠️ Could not save HTML: {str(e)}")
                    
                    print("🚨 Attempting polling solution")
                    
                    # Wait for 2FA code via file polling (this will create file and send email)
                    two_fa_code = self._wait_for_2fa_code()
                    
                    if two_fa_code:
                        print("✅ 2FA code received - attempting to continue login")
                        if self._enter_2fa_code(two_fa_code):
                            print("✅ 2FA verification successful - continuing scan")
                            time.sleep(5)  # Wait for login to complete
                        else:
                            print("❌ 2FA verification failed - stopping scan")
                            return False
                    else:
                        print("❌ 2FA code not received within timeout - stopping scan")
                        return False
                
                # Handle password save popup
                self._handle_password_save_popup()
            
            print(f"📍 After login URL: {self.driver.current_url}")
            
            # Search multiple terms with anti-detection
            search_terms = [
                "pool cleaning",
                "window washing", 
                "bin cleaning",
                "lawn care",
                "spa cleaning",
                "pest control",
                "exterminator",
                "pressure washing",
                "house cleaning",
                "gutter cleaning"
            ]
            
            all_posts = []
            for i, term in enumerate(search_terms):
                print(f"\n🔍 Search {i+1}/{len(search_terms)}: '{term}'")
                
                if self._search_for_term(term):
                    print("✅ Search completed")
                    
                    # Anti-detection: random delay after search
                    time.sleep(random.uniform(2, 4))
                    
                    # Collect posts for this search term
                    posts = self._scroll_and_collect_posts()
                    if posts:
                        # Tag posts with search term
                        for post in posts:
                            post['search_term'] = term
                        all_posts.extend(posts)
                        print(f"✅ Found {len(posts)} posts for '{term}'")
                    
                    # Anti-detection: longer delay between searches
                    if i < len(search_terms) - 1:  # Don't delay after last search
                        delay = random.uniform(20, 35)
                        print(f"⏳ Waiting {delay:.1f}s before next search...")
                        time.sleep(delay)
                        
                        # Handle any popups that might appear
                        self._handle_popups()
                else:
                    print("❌ Search failed")
            
            # Remove duplicates across all searches
            unique_posts = []
            seen_texts = set()
            
            for post in all_posts:
                text_key = post['text'][:50].lower().strip()
                if text_key not in seen_texts:
                    unique_posts.append(post)
                    seen_texts.add(text_key)
            
            print(f"\n📊 Total unique posts across all searches: {len(unique_posts)}")
            
            if unique_posts:
                self._save_results(unique_posts)
                print(f"✅ Saved {len(unique_posts)} unique posts")
                
                # Filter posts through Groq for relevance
                print(f"🤖 Analyzing posts with Groq for Bulqit relevance...")
                relevant_posts = self.groq_filter.filter_posts(unique_posts)
                
                if relevant_posts:
                    print(f"📧 Sending email report with {len(relevant_posts)} relevant opportunities")
                    self.groq_filter.send_email_report(relevant_posts)
                else:
                    print("📧 No relevant posts found - no email sent")
            else:
                print("❌ No posts found")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during login: {str(e)}")
            return False

    def _check_for_2fa(self):
        """Check if 2FA verification is required"""
        try:
            print("🔍 Checking for 2FA requirement...")
            
            # More specific 2FA indicators - look for actual form elements or visible text
            try:
                # Check if we're actually at the news feed (successful login)
                if "news_feed" in self.driver.current_url:
                    print("✅ Successfully logged in - at news feed")
                    return False
                
                # Check for visible 2FA elements only
                two_fa_selectors = [
                    'input[type="text"][placeholder*="code"]',
                    'input[placeholder*="verification"]',
                    'input[placeholder*="security"]',
                    'input[name*="code"]',
                    'input[name*="verify"]',
                    'form[action*="verify"]',
                    'div[class*="verification"]',
                    'div[class*="2fa"]'
                ]
                
                for selector in two_fa_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element and element.is_displayed():
                            print(f"🚨 2FA detected: Found visible input field with selector {selector}")
                            return True
                    except:
                        continue
                        
                # Check for specific 2FA text in visible elements only
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    visible_text = body.text.lower()
                    critical_2fa_phrases = [
                        "enter the verification code",
                        "enter your verification code", 
                        "security code",
                        "authentication code",
                        "verify your account"
                    ]
                    
                    for phrase in critical_2fa_phrases:
                        if phrase in visible_text:
                            print(f"🚨 2FA detected: Found visible text '{phrase}'")
                            return True
                except:
                    pass
                    
            except Exception as e:
                print(f"⚠️ Error in specific 2FA check: {str(e)}")
                pass
            # Check current URL for 2FA paths (more specific)
            current_url = self.driver.current_url.lower()
            if any(path in current_url for path in ['/verify', '/2fa', '/authenticate']):
                print(f"🚨 2FA detected: URL contains 2FA path - {current_url}")
                return True
            
            print("✅ No 2FA requirement detected")
            return False
            
        except Exception as e:
            print(f"⚠️ Error checking for 2FA: {str(e)}")
            return False

    def _create_2fa_gist(self):
        """Create a private GitHub Gist for 2FA code input"""
        if not self.github_token:
            print("❌ GitHub token not found for Gist creation")
            return None
            
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            gist_data = {
                "description": f"Nextdoor 2FA Code Input - {timestamp}",
                "public": False,
                "files": {
                    "nextdoor_2fa_code.txt": {
                        "content": f"""ENTER_2FA_CODE_HERE

Instructions:
1. Replace "ENTER_2FA_CODE_HERE" above with your 6-digit Nextdoor verification code
2. Save this gist
3. The scanner will automatically detect your code and continue

Created: {timestamp}
This gist will be automatically deleted after use.
"""
                    }
                }
            }
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.post('https://api.github.com/gists', 
                                   json=gist_data, headers=headers)
            
            if response.status_code == 201:
                gist_info = response.json()
                self.current_gist_id = gist_info['id']
                gist_url = gist_info['html_url']
                print(f"✅ Created private gist: {gist_url}")
                return gist_url
            else:
                print(f"❌ Failed to create gist: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating gist: {str(e)}")
            return None

    def _poll_gist_for_code(self):
        """Poll the GitHub Gist for 2FA code updates"""
        if not self.github_token or not self.current_gist_id:
            print("❌ Missing GitHub token or gist ID")
            return None
            
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            url = f'https://api.github.com/gists/{self.current_gist_id}'
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                gist_data = response.json()
                file_content = gist_data['files']['nextdoor_2fa_code.txt']['content']
                
                print(f"📖 Gist content preview: '{file_content[:50]}...'")
                
                # Look for 6-digit code
                lines = file_content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and line.isdigit() and len(line) == 6:
                        print(f"✅ Found 2FA code in gist: {line}")
                        return line
                    elif line and line != 'ENTER_2FA_CODE_HERE' and not line.startswith('Instructions:'):
                        # Extract digits from the line
                        digits = ''.join(c for c in line if c.isdigit())
                        if len(digits) == 6:
                            print(f"✅ Found 2FA code in gist: {digits}")
                            return digits
                
                return None
            else:
                print(f"❌ Failed to read gist: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error polling gist: {str(e)}")
            return None

    def _delete_2fa_gist(self):
        """Delete the 2FA gist after use"""
        if not self.github_token or not self.current_gist_id:
            return
            
        try:
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            url = f'https://api.github.com/gists/{self.current_gist_id}'
            response = requests.delete(url, headers=headers)
            
            if response.status_code == 204:
                print(f"🗑️ Deleted 2FA gist: {self.current_gist_id}")
            else:
                print(f"⚠️ Failed to delete gist: {response.status_code}")
                
            self.current_gist_id = None
            
        except Exception as e:
            print(f"⚠️ Error deleting gist: {str(e)}")

    def _wait_for_2fa_code(self):
        """Wait for 2FA code to be provided via GitHub Gist polling"""
        try:
            print("🔄 Creating GitHub Gist for 2FA code input...")
            
            # Create private gist
            gist_url = self._create_2fa_gist()
            if not gist_url:
                print("❌ Failed to create gist - stopping")
                return None
            
            # Send notification email with gist URL
            self.groq_filter.send_2fa_notification_with_gist(gist_url)
            
            # Poll for 2FA code for up to 3 minutes (180 seconds)
            max_attempts = 6  # 6 attempts * 30 seconds = 3 minutes
            attempt = 0
            
            while attempt < max_attempts:
                code = self._poll_gist_for_code()
                if code:
                    print(f"✅ 2FA code received from gist - cleaning up")
                    self._delete_2fa_gist()
                    return code
                
                attempt += 1
                remaining_time = (max_attempts - attempt) * 30
                print(f"⏳ Attempt {attempt}/{max_attempts} - Waiting for 2FA code... ({remaining_time}s remaining)")
                time.sleep(30)
            
            print("❌ Timeout waiting for 2FA code (3 minutes)")
            self._delete_2fa_gist()
            return None
            
        except Exception as e:
            print(f"⚠️ Error in 2FA gist polling: {str(e)}")
            self._delete_2fa_gist()
            return None

    def _enter_2fa_code(self, code):
        """Enter the 2FA code into the form (Nextdoor uses 6 separate input fields)"""
        try:
            print(f"🔐 Entering 2FA code: {code}")
            
            # Nextdoor uses 6 separate input fields - get them dynamically
            try:
                # Find all input fields with IDs starting with _r and ending with _
                input_elements = self.driver.find_elements(By.CSS_SELECTOR, 'input[id^="_r"][id$="_"]')
                input_ids = [elem.get_attribute('id') for elem in input_elements if elem.is_displayed()]
                input_ids.sort()  # Sort to ensure correct order
                print(f"📝 Found {len(input_ids)} 2FA input fields: {input_ids}")
            except Exception as e:
                print(f"⚠️ Error finding input fields, using fallback: {str(e)}")
                input_ids = ['_rd_', '_re_', '_rf_', '_rg_', '_rh_', '_ri_']
            
            if len(code) != 6:
                print(f"❌ 2FA code must be 6 digits, got {len(code)}: {code}")
                return False
            
            # Enter each digit into its respective field
            for i, digit in enumerate(code):
                try:
                    input_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, input_ids[i]))
                    )
                    input_field.clear()
                    input_field.send_keys(digit)
                    print(f"✅ Entered digit {digit} into field {input_ids[i]}")
                    time.sleep(0.2)  # Small delay between digits
                except Exception as e:
                    print(f"❌ Could not enter digit {digit} into field {input_ids[i]}: {str(e)}")
                    return False
            
            print("✅ All 6 digits entered successfully")
            
            # Wait a bit for any auto-submission or page changes
            time.sleep(3)
            
            # More robust verification that 2FA worked
            try:
                current_url = self.driver.current_url
                print(f"📍 URL after entering code: {current_url}")
                
                # If URL changed away from login, check for specific success indicators
                if "/login/" not in current_url:
                    print("✅ URL changed from login page - verifying successful login...")
                    
                    # Look for elements that indicate successful login
                    success_indicators = [
                        'div[data-test-id*="search"]',  # Search box
                        'button[aria-label*="menu"]',   # User menu
                        'nav',                          # Navigation bar
                        'header',                       # Header with user info
                        'input[placeholder*="search"]'  # Search input
                    ]
                    
                    for indicator in success_indicators:
                        try:
                            element = self.driver.find_element(By.CSS_SELECTOR, indicator)
                            if element and element.is_displayed():
                                print(f"✅ Found success indicator: {indicator}")
                                return True
                        except:
                            continue
                    
                    # If news_feed in URL, it's probably successful even without specific elements
                    if "news_feed" in current_url or "feed" in current_url:
                        print("✅ At news feed - 2FA successful")
                        return True
                    
                    print("⚠️ URL changed but couldn't confirm successful login")
                    return True  # Assume success if URL changed
                    
            except Exception as e:
                print(f"⚠️ Could not check URL: {str(e)}")
            
            # Try to find and click Login button if still on login page
            try:
                # Look for the Login button with different selectors
                login_selectors = [
                    "//button[contains(text(), 'Login')]",
                    "//button[contains(text(), 'Continue')]", 
                    "//button[contains(text(), 'Submit')]",
                    "//button[@type='submit']",
                    "//input[@type='submit']"
                ]
                
                login_button = None
                for selector in login_selectors:
                    try:
                        login_button = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        print(f"✅ Found login button with: {selector}")
                        break
                    except:
                        continue
                
                if login_button:
                    login_button.click()
                    print("✅ Clicked Login button")
                    time.sleep(5)
                    return True
                else:
                    print("⚠️ No login button found - checking if already logged in")
                    # Sometimes Nextdoor auto-submits after entering all digits
                    time.sleep(3)
                    
                    # Check URL again to see if we've moved past login
                    try:
                        final_url = self.driver.current_url
                        if "/login/" not in final_url:
                            print("✅ Login successful - moved past login page")
                            return True
                        else:
                            print("❌ Still on login page without submit button")
                            return False
                    except:
                        print("❌ Could not verify final login status")
                        return False
                
            except Exception as e:
                print(f"❌ Error during login button search: {str(e)}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error entering 2FA code: {str(e)}")
            return False

    def _handle_password_save_popup(self):
        """Handle 'Do you want to save this password' popup (both Nextdoor and Chrome)"""
        try:
            print("🔍 Checking for password save popup...")
            
            # Handle Chrome's built-in password save popup via JavaScript
            try:
                self.driver.execute_script("""
                    // Try to dismiss Chrome's password save notification
                    var chromePasswordBubble = document.querySelector('div[data-automation-id="password-manager-ui"]');
                    if (chromePasswordBubble) {
                        chromePasswordBubble.style.display = 'none';
                    }
                    
                    // Press Escape to dismiss any browser popups
                    document.dispatchEvent(new KeyboardEvent('keydown', {'key': 'Escape'}));
                """)
                print("✅ Attempted to dismiss Chrome password popup via JavaScript")
            except:
                pass
            
            # Handle Nextdoor's own password save popups
            dismiss_selectors = [
                'button:contains("Not now")',
                'button:contains("No thanks")', 
                'button:contains("Never")',
                'button:contains("Nee")',  # "Nee" for Dutch/international
                '[data-testid="password-save-dismiss"]',
                '.password-save-dismiss',
                'button[aria-label*="dismiss"]',
                'button[aria-label*="not now"]',
                '.close-button',
                '[aria-label="Close"]'
            ]
            
            popup_dismissed = False
            for selector in dismiss_selectors:
                try:
                    dismiss_button = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ Found password save dismiss button: {selector}")
                    dismiss_button.click()
                    print("✅ Dismissed password save popup")
                    popup_dismissed = True
                    time.sleep(1)
                    break
                except:
                    continue
            
            if not popup_dismissed:
                print("ℹ️ No password save popup found (or already dismissed)")
            
        except Exception as e:
            print(f"⚠️ Error handling password save popup: {str(e)}")

    def _search_for_term(self, search_term):
        """Search for a specific term in Nextdoor search box"""
        try:
            print(f"🔍 Searching for: {search_term}")
            
            # Wait a bit for page to fully load after login
            time.sleep(3)
            
            # Try different search box selectors
            search_selectors = [
                '#search-input-field',
                'input[aria-label="Search Nextdoor"]',
                'input[placeholder*="Search"]',
                'input[placeholder*="search"]', 
                'input[type="search"]',
                '[data-testid="search-input"]',
                '.search-input',
                'input[name="search"]',
                '#search',
                'input[aria-label*="Search"]'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"✅ Found search box with selector: {selector}")
                    break
                except:
                    continue
            
            if not search_box:
                print("❌ Could not find search box")
                return False
            
            # Click to focus and type search term
            search_box.click()
            time.sleep(1)
            
            print(f"⌨️ Typing '{search_term}' letter by letter...")
            self._type_letter_by_letter(search_box, search_term)
            
            # Wait a bit after typing
            time.sleep(2)
            
            # Find and click search button or press Enter
            search_button_selectors = [
                'button[type="submit"]',
                'button[aria-label*="Search"]',
                '[data-testid="search-button"]',
                '.search-button',
                'button:contains("Search")'
            ]
            
            search_clicked = False
            for selector in search_button_selectors:
                try:
                    search_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    print(f"✅ Found search button with selector: {selector}")
                    search_button.click()
                    search_clicked = True
                    break
                except:
                    continue
            
            if not search_clicked:
                # Try pressing Enter instead
                print("🔍 No search button found, pressing Enter...")
                search_box.send_keys('\n')
            
            # Wait for search results to load
            time.sleep(5)
            
            print(f"📍 After search URL: {self.driver.current_url}")
            
            # Click Posts tab
            if self._click_posts_tab():
                print("✅ Posts tab clicked")
            else:
                print("❌ Failed to click Posts tab")
            
            # Click time filter and select Today
            if self._set_time_filter_to_today():
                print("✅ Time filter set to Today")
            else:
                print("❌ Failed to set time filter")
            
            
            return True
            
        except Exception as e:
            print(f"❌ Error during search: {str(e)}")
            return False

    def _click_posts_tab(self):
        """Click the Posts tab in search results"""
        try:
            print("📝 Looking for Posts tab...")
            
            # Try different Posts tab selectors based on the HTML
            posts_tab_selectors = [
                '[data-testid="tab-posts"]',
                '#id-209-posts',
                'a[role="tab"][aria-controls*="posts-panel"]',
                'a:contains("Posts")',
                '[href*="/search/posts/"]'
            ]
            
            for selector in posts_tab_selectors:
                try:
                    posts_tab = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    print(f"✅ Found Posts tab with selector: {selector}")
                    posts_tab.click()
                    time.sleep(3)
                    print(f"📍 After Posts click URL: {self.driver.current_url}")
                    return True
                except:
                    continue
            
            print("❌ Could not find Posts tab")
            return False
            
        except Exception as e:
            print(f"❌ Error clicking Posts tab: {str(e)}")
            return False

    def _set_time_filter_to_today(self):
        """Click time filter button and select Today"""
        try:
            print("📅 Looking for time filter button...")
            
            # Try to find the time filter button with "All Time" text
            time_filter_selectors = [
                'span:contains("All Time")',
                'div:contains("All Time")',
                '.BaseButton__emelwr2:has(span:contains("All Time"))',
                'div[data-part="button"]:has(span:contains("All Time"))',
                'button:has(svg[data-icon="calendar"])',
                'div:has(svg[data-icon="calendar"]):has(span:contains("All Time"))'
            ]
            
            time_filter_clicked = False
            for selector in time_filter_selectors:
                try:
                    # Use JavaScript to find and click since :contains() and :has() are limited
                    time_filter_found = self.driver.execute_script(f"""
                        var elements = document.querySelectorAll('span');
                        for (var i = 0; i < elements.length; i++) {{
                            if (elements[i].textContent.includes('All Time')) {{
                                var button = elements[i].closest('.BaseButton__emelwr2') || elements[i].closest('div[data-part="button"]');
                                if (button) {{
                                    button.click();
                                    return true;
                                }}
                            }}
                        }}
                        return false;
                    """)
                    
                    if time_filter_found:
                        print("✅ Found and clicked time filter button")
                        time_filter_clicked = True
                        time.sleep(2)
                        break
                except:
                    continue
            
            if not time_filter_clicked:
                print("❌ Could not find time filter button")
                return False
            
            # Now look for "Today" option in the dropdown
            print("📅 Looking for 'Today' option...")
            
            today_selectors = [
                'span:contains("Today")',
                'div:contains("Today")',
                'button:contains("Today")',
                '[data-testid*="today"]',
                'li:contains("Today")'
            ]
            
            today_found = self.driver.execute_script("""
                var elements = document.querySelectorAll('span, div, button, li');
                for (var i = 0; i < elements.length; i++) {
                    if (elements[i].textContent.trim() === 'Today') {
                        elements[i].click();
                        return true;
                    }
                }
                return false;
            """)
            
            if today_found:
                print("✅ Selected 'Today' option")
                time.sleep(2)
                return True
            else:
                print("❌ Could not find 'Today' option")
                return False
            
        except Exception as e:
            print(f"❌ Error setting time filter: {str(e)}")
            return False

    def _extract_nextdoor_posts(self):
        """Extract main posts from Nextdoor page - fixed to distinguish main posts from replies"""
        try:
            print("📝 Extracting posts from page...")
            
            # Wait a bit for page to load after filters
            time.sleep(3)
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, "html.parser")
            posts_data = []
            
            # Look for main content area first
            main_content = soup.find('div', {'id': 'main_content'})
            if not main_content:
                print("❌ Could not find main content area")
                return []
            
            # Find all post containers - look for the main post structure
            post_containers = main_content.find_all('div', class_='_7uk7474')
            
            print(f"🔍 Found {len(post_containers)} potential post containers")
            
            for i, container in enumerate(post_containers):
                try:
                    # Look for the main post card structure
                    main_post_card = container.find('div', {'data-block': '22'})
                    if not main_post_card:
                        continue
                    
                    # Extract post URL from the link
                    post_url = ""
                    post_link = container.find('a', {'data-block': '17'})
                    if post_link and post_link.get('href'):
                        href = post_link.get('href')
                        if href.startswith('/p/'):
                            post_url = f"https://nextdoor.com{href}"
                        else:
                            post_url = href
                    
                    # Extract author - look for the detailTitle styled text (author name)
                    author = "Unknown"
                    author_spans = container.find_all('span', {'data-testid': 'styled-text'})
                    
                    for span in author_spans:
                        # Check if this span has the author name styling
                        style = span.get('style', '')
                        if 'detailTitle' in style:
                            author_text = span.get_text(strip=True)
                            if len(author_text) > 2 and len(author_text) < 50:
                                author = author_text
                                break
                    
                    # Extract main post content - look for the longer text content
                    post_text = ""
                    
                    # Try multiple potential content containers
                    content_divs = [
                        container.find('div', class_='blocks-1avh7al'),
                        container.find('div', class_='blocks-1q6x145'),
                        container.find('div', class_=lambda x: x and 'Styled_marginRight-sm__zpop7kx' in x)
                    ]
                    
                    for content_div in content_divs:
                        if content_div and not post_text:
                            content_spans = content_div.find_all('span', {'data-testid': 'styled-text'})
                            text_parts = []
                            for span in content_spans:
                                text = span.get_text(strip=True)
                                # Skip author names and metadata
                                if (text and text != author and 
                                    '·' not in text and 'ago' not in text and 
                                    not text.isdigit() and len(text) > 3):
                                    text_parts.append(text)
                            if text_parts:
                                post_text = ' '.join(text_parts)
                                break
                    
                    # Only process if we have substantial main post content
                    if (post_text and len(post_text) > 30 and 
                        author != "Unknown" and 
                        not post_text.startswith('…')):  # Skip replies that start with ...
                        
                        # Additional filtering for main posts
                        is_main_post = True
                        
                        # Skip very short posts (likely replies)
                        if len(post_text) < 40:
                            is_main_post = False
                        
                        # Skip obvious replies
                        reply_indicators = ['@', 'Reply to', 'Thanks', 'Thank you', 'Yes', 'No', 'Agree', 'Same here']
                        if any(indicator in post_text[:30] for indicator in reply_indicators):
                            is_main_post = False
                        
                        if is_main_post:
                            post_data = {
                                'text': post_text,
                                'author': author,
                                'url': post_url
                            }
                            
                            posts_data.append(post_data)
                            print(f"✅ Main Post {len(posts_data)}: {post_text[:60]}... (by {author})")
                            if post_url:
                                print(f"   🔗 URL: {post_url}")
                        else:
                            print(f"🔄 Skipped reply: {post_text[:30]}... (by {author})")
                    
                except Exception as e:
                    print(f"⚠️ Error processing container {i+1}: {str(e)}")
                    continue
            
            # Remove duplicates
            unique_posts = []
            seen_texts = set()
            
            for post in posts_data:
                text_key = post['text'][:50].lower().strip()
                if text_key not in seen_texts:
                    unique_posts.append(post)
                    seen_texts.add(text_key)
                else:
                    print(f"🔄 Skipped duplicate: {post['text'][:30]}...")
            
            print(f"📝 Successfully extracted {len(unique_posts)} unique main posts")
            return unique_posts
            
        except Exception as e:
            print(f"❌ Error extracting posts: {str(e)}")
            return []

    def _handle_popups(self):
        """Handle Nextdoor popups and overlays"""
        try:
            popup_closed = self.driver.execute_script("""
                var popupsFound = 0;
                
                // Close modals and overlays
                var closeSelectors = [
                    '[aria-label="Close"]',
                    'button[aria-label="Close"]',
                    '.close-button',
                    '[data-testid="close-button"]',
                    '.modal-close',
                    '[aria-label="Dismiss"]'
                ];
                
                closeSelectors.forEach(function(selector) {
                    var elements = document.querySelectorAll(selector);
                    elements.forEach(function(element) {
                        if (element.offsetParent !== null) {
                            try {
                                element.click();
                                popupsFound++;
                            } catch (e) {}
                        }
                    });
                });
                
                return popupsFound;
            """)
            
            if popup_closed > 0:
                print(f"✅ Closed {popup_closed} popups")
                time.sleep(2)
                
        except Exception as e:
            print(f"⚠️ Error handling popups: {str(e)}")

    def _extract_posts_with_bs(self):
        """Extract posts using BeautifulSoup - similar to Facebook approach"""
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")
        posts_data = []
        
        # Try multiple potential Nextdoor post selectors
        post_selectors = [
            '[data-testid="post"]',
            '.post-container',
            '.feed-item',
            '[role="article"]',
            '.post-card',
            '.nd-post'
        ]
        
        all_posts = []
        for selector in post_selectors:
            found_posts = soup.select(selector)
            all_posts.extend(found_posts)
            print(f"🔍 Selector '{selector}' found {len(found_posts)} posts")
        
        # Remove duplicates
        unique_posts = []
        seen_posts = set()
        for post in all_posts:
            post_html = str(post)[:200]
            if post_html not in seen_posts:
                unique_posts.append(post)
                seen_posts.add(post_html)
        
        print(f"🔍 Found {len(unique_posts)} unique post containers")
        
        for post in unique_posts:
            try:
                # Extract post text
                post_text = ""
                
                # Try multiple text extraction methods
                text_selectors = [
                    '.post-content',
                    '.post-text',
                    '.post-body',
                    '[data-testid="post-content"]',
                    'p', 'div'
                ]
                
                for text_selector in text_selectors:
                    elements = post.select(text_selector)
                    if elements:
                        for element in elements:
                            text = element.get_text(strip=True)
                            if len(text) > 20:  # Meaningful content
                                post_text = text
                                break
                        if post_text:
                            break
                
                if not post_text or len(post_text) < 20:
                    continue
                
                # Extract author
                author = "Unknown"
                author_selectors = [
                    '.author-name',
                    '.post-author',
                    '[data-testid="author"]',
                    '.user-name',
                    'strong',
                    'h4', 'h5', 'h6'
                ]
                
                for author_selector in author_selectors:
                    author_elements = post.select(author_selector)
                    if author_elements:
                        author_text = author_elements[0].get_text(strip=True)
                        if author_text and len(author_text) > 2 and len(author_text) < 100:
                            author = author_text
                            break
                
                # Store post data
                post_data = {
                    'post_text': post_text.strip(),
                    'author': author,
                    'platform': 'Nextdoor'
                }
                
                posts_data.append(post_data)
                print(f"✅ Extracted Nextdoor post by {author}: {post_text[:60]}...")
                
            except Exception as e:
                print(f"⚠️ Error extracting post: {str(e)}")
                continue
        
        return posts_data

    def _scroll_and_collect_posts(self, max_scrolls=20):
        """Scroll through Nextdoor feed until bottom is reached"""
        all_posts = []
        scroll_count = 0
        no_new_posts_count = 0
        
        print(f"📜 Starting to scroll and collect posts (max {max_scrolls} scrolls)")
        
        while scroll_count < max_scrolls:
            scroll_count += 1
            print(f"📍 Scroll {scroll_count}")
            
            # Get current page height before scrolling
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Extract posts from current view
            posts = self._extract_nextdoor_posts()
            
            # Add new posts (check for duplicates)
            new_posts_added = 0
            for post in posts:
                # Check if we already have this post
                if not any(existing['text'][:50] == post['text'][:50] for existing in all_posts):
                    post['scroll_found'] = scroll_count
                    all_posts.append(post)
                    new_posts_added += 1
                    
            print(f"📊 Added {new_posts_added} new posts, total: {len(all_posts)}")
            
            # Track if we're getting new posts
            if new_posts_added == 0:
                no_new_posts_count += 1
            else:
                no_new_posts_count = 0
            
            # Stop if no new posts for 3 consecutive scrolls
            if no_new_posts_count >= 3:
                print("🔚 No new posts found for 3 scrolls - likely reached bottom")
                break
            
            # Scroll down
            scroll_amount = random.randint(500, 800)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(3, 5))  # Wait for content to load
            
            # Check if page height changed (new content loaded)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == current_height:
                print("📏 Page height unchanged - double checking...")
                # Wait a bit longer and try one more scroll to be sure
                time.sleep(3)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(3)
                final_height = self.driver.execute_script("return document.body.scrollHeight")
                if final_height == new_height:
                    print("📏 Confirmed at bottom - no more content")
                    break
                else:
                    print("📏 Found more content after double check")
                    current_height = final_height
            
            # Handle any popups that appear
            self._handle_popups()
        
        print(f"✅ Scrolling complete after {scroll_count} scrolls")
        return all_posts

    def _save_results(self, posts):
        """Save extracted posts to clean file format"""
        if not posts:
            print("⚠️ No posts to save")
            return
            
        output_file = f"nextdoor_posts_all_services_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.txt"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("Nextdoor Posts - All Home Services Search\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                
                for i, post in enumerate(posts, 1):
                    f.write(f"Post {i}:\n")
                    f.write(f"Author: {post['author']}\n")
                    if post.get('search_term'):
                        f.write(f"Search Term: {post['search_term']}\n")
                    f.write(f"Text: {post['text']}\n")
                    if post.get('url'):
                        f.write(f"URL: {post['url']}\n")
                    f.write("-" * 50 + "\n\n")
                
                f.write(f"\nTotal posts: {len(posts)}\n")
                
            print(f"✅ Saved {len(posts)} posts to {output_file}")
            
        except Exception as e:
            print(f"⚠️ Error saving results: {str(e)}")

    def run_scan(self):
        """Main scanning workflow - login only for now"""
        print("🚀 Starting Nextdoor login test...")
        print("🔍 Manual login required...")
        print("=" * 60)
        
        if not self._setup_headless_driver():
            return False
            
        try:
            # Login to Nextdoor
            if not self._login_to_nextdoor():
                print("❌ Failed to login to Nextdoor")
                return False
                
            print("\n✅ Login completed! Starting scan...")
            
            # Actually run the scan instead of just waiting
            search_terms = ["pool cleaning", "landscaping", "lawn care", "pest control", "window washing"]
            all_posts = []
            
            for term in search_terms:
                print(f"🔍 Searching for: {term}")
                posts = self._search_for_term(term)
                all_posts.extend(posts)
                time.sleep(3)  # Brief pause between searches
            
            # Save results
            if all_posts:
                self._save_results(all_posts)
                print(f"\n🎉 Scan completed! Found {len(all_posts)} posts")
            else:
                print("\n📭 No posts found")
            
            time.sleep(5)  # Keep browser open briefly to see results
            return True
            
        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            return True
            
        except Exception as e:
            print(f"❌ Scan failed: {str(e)}")
            return False
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    print(f"⚠️ Error closing browser: {str(e)}")
                    # Force cleanup if needed
                    import os
                    os.system("pkill -f chrome || true")
            

def main():
    print("🏠 NEXTDOOR SCANNER - BULQIT SERVICE OPPORTUNITIES")
    scanner = NextdoorScanner()
    
    # Login test only
    success = scanner.run_scan()
    
    if success:
        print("\n✅ Nextdoor login test completed!")
    else:
        print("\n❌ Nextdoor login test failed")

if __name__ == "__main__":
    main()