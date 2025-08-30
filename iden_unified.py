#!/usr/bin/env python3
"""
Iden Challenge Automation Script
Combines robust authentication ,navigation with efficient table extraction.

This script:
1. Checks for existing session and attempts to reuse it
2. Authenticates with the application if no session exists
3. Navigates through the hidden path to access product data
4. Captures all product data using efficient infinite scroll strategy
5. Exports data to structured JSON format
"""

import json
import os
import time
import re
from typing import Dict, List, Optional, Any, Set, Tuple
import logging
from pathlib import Path
import argparse
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration constants
LOGIN_URL = "https://hiring.idenhq.com/"
CHALLENGE_URL = "https://hiring.idenhq.com/challenge"
SESSION_FILE = "session.json"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



class IdenUnifiedAutomation:
   

    def __init__(self):
        self.base_url = LOGIN_URL.rstrip('/')
        self.credentials = {
            "username": os.getenv("IDEN_USERNAME"),
            "password": os.getenv("IDEN_PASSWORD")
        }
        self.session_file = SESSION_FILE
        self.output_file = "product_data.json"
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.pw = None
        # Button navigation path
        self.buttons_path = [
            ("button", "Start Journey"),
            ("button", "Continue Search"),
            ("button", "Inventory Section"),
            ("button", "Show Product Table"),
        ]

    def cleanup_invalid_session_files(self):
        """Remove invalid session files to force fresh login."""
        try:
            files_to_remove = [self.session_file, "session_storage.json", "local_storage.json"]
            for file_path in files_to_remove:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed invalid session file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup session files: {e}")

    def setup_browser(self, headless: bool = False) -> bool:
        """
        Initialize browser and context.
        Returns True if an existing session was reused successfully, False otherwise.
        """
        try:
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch(
                headless=headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )

            if self.has_valid_session_files():
                try:
                    logger.info("Found existing session files, attempting to reuse...")

                    # Open a fresh context without storage_state
                    self.context = self.browser.new_context()
                    self.page = self.context.new_page()

                    # Navigate to the base domain first
                    self.page.goto(self.base_url, wait_until="domcontentloaded")

                    # Inject saved sessionStorage before going to challenge
                    with open("session_storage.json", "r", encoding="utf-8") as f:
                        session_storage = json.load(f)

                    restored_count = 0
                    for k, v in session_storage.items():
                        safe_value = json.dumps(v)  # handles quotes safely
                        self.page.evaluate(f"sessionStorage.setItem('{k}', {safe_value})")
                        restored_count += 1
                    logger.info(f"Restored {restored_count} sessionStorage keys")

                    # Reload challenge page with session data in place
                    self.page.goto(CHALLENGE_URL, wait_until="networkidle")

                    if "challenge" in self.page.url:
                        logger.info("Existing session valid, skipping login")
                        print("Session reused successfully! Skipping authentication...")
                        return True
                    else:
                        logger.info("Session invalid, forcing fresh login")
                        self.cleanup_invalid_session_files()
                        self.context.close()
                        return False

                except Exception as e:
                    logger.warning(f"Failed to reuse existing session: {e}")
                    self.cleanup_invalid_session_files()
                    return False

            # No valid session found,login needed
            logger.info("Creating fresh browser context")
            print("No valid session found, creating fresh browser context...")
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            return False

        except Exception as e:
            logger.error(f"Browser setup failed: {e}")
            raise

    def save_session(self) -> None:
        """Save current session after a successful login on the challenge page."""
        try:
            if not self.context or not self.page:
                logger.error("No context or page to save session from")
                return

            # Ensure we are on an authenticated page
            if "challenge" not in self.page.url:
                logger.warning("Not on challenge page, skipping session save")
                return

            # Save Playwright cookies and localStorage 
            self.context.storage_state(path=self.session_file)
            logger.info(f"Session saved to {self.session_file}")

            # Save sessionStorage separately (this is where the auth tokens are)
            try:
                session_storage = self.page.evaluate(
                    "() => Object.entries(sessionStorage).reduce((obj,[k,v]) => (obj[k]=v,obj), {})"
                )
                with open("session_storage.json", "w", encoding="utf-8") as f:
                    json.dump(session_storage, f, indent=2, ensure_ascii=False)
                
                # Also save localStorage as backup
                localStorage = self.page.evaluate(
                    "() => Object.entries(localStorage).reduce((obj,[k,v]) => (obj[k]=v,obj), {})"
                )
                with open("local_storage.json", "w", encoding="utf-8") as f:
                    json.dump(localStorage, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Storage saved: {len(session_storage)} sessionStorage, {len(localStorage)} localStorage keys")
                
            except Exception as e:
                logger.warning(f"Failed to save storage: {e}")

        except Exception as e:
            logger.error(f"Failed to save storage state: {e}")

    def has_valid_session_files(self) -> bool:
        """Check if we have valid session files with actual data."""
        try:
            # Check if main session file exists (even if empty, use sessionStorage)
            if not os.path.exists(self.session_file):
                return False
            
            # Check if sessionStorage file exists and has content
            if not os.path.exists("session_storage.json") or os.path.getsize("session_storage.json") <= 10:
                return False
            
            # Verify sessionStorage has actual keys
            with open("session_storage.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                if not session_data or len(session_data) == 0:
                    return False
            
            logger.info(f"Found valid session files with {len(session_data)} sessionStorage keys")
            return True
            
        except Exception as e:
            logger.warning(f"Error checking session files: {e}")
            return False

    def validate_session(self) -> bool:
        """Validate if the current session is still valid."""
        try:
            if not self.page:
                return False
            
            # Try to navigate to a protected page to check session validity
            self.page.goto(CHALLENGE_URL)
            self.wait_for_idle_network()
            
            # Check if we're redirected to login or if we can access the challenge
            if "challenge" in self.page.url:
                logger.info("Session is still valid")
                return True
            else:
                logger.info("Session has expired")
                return False
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return False

    def wait_for_idle_network(self, timeout_ms=10000):
        """Wait for network to be idle."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout_ms)
        except Exception:
            pass

    def wait_for_auth_data(self, timeout_ms=10000) -> bool:
        """Wait for authentication data to be present before saving session."""
        try:
            logger.info("Waiting for authentication data to be present...")
            
            # Wait for either cookies, localStorage auth token, or sessionStorage auth token
            result = self.page.wait_for_function(
                """() => {
                    // Check if we have any cookies
                    if (document.cookie && document.cookie.length > 0) return true;
                    
                    // Check if we have any localStorage items
                    if (Object.keys(localStorage).length > 0) return true;
                    
                    // Check if we have any sessionStorage items
                    if (Object.keys(sessionStorage).length > 0) return true;
                    
                    // Check for specific auth-related keys
                    if (localStorage.getItem("authToken") !== null) return true;
                    if (localStorage.getItem("session") !== null) return true;
                    if (localStorage.getItem("token") !== null) return true;
                    
                    return false;
                }""",
                timeout=timeout_ms
            )
            
            if result:
                logger.info("Authentication data detected")
                return True
            else:
                logger.warning("No authentication data detected after timeout")
                return False
                
        except Exception as e:
            logger.warning(f"Error waiting for auth data: {e}")
            return False

    def authenticate(self) -> bool:
        """Authenticate only if no valid session exists."""
        try:
            self.page.goto(LOGIN_URL)
            self.wait_for_idle_network()

            if not (self.credentials["username"] and self.credentials["password"]):
                logger.error("Credentials missing")
                return False

            # Fill username
            self.page.fill('input[type="email"]', self.credentials["username"])
            self.page.fill('input[type="password"]', self.credentials["password"])
            self.page.click('button[type="submit"]')

            self.wait_for_idle_network()
            time.sleep(2)

            # Go to challenge page after login
            self.page.goto(CHALLENGE_URL)
            self.wait_for_idle_network()

            if "challenge" in self.page.url:
                logger.info("Authentication successful, saving session")
                # Wait a bit longer to ensure all session data is stored
                time.sleep(3)
                
                # Wait for authentication data to be present
                if self.wait_for_auth_data(timeout_ms=15000):
                    logger.info("Authentication data confirmed, saving session")
                    self.save_session()
                    return True
                else:
                    logger.warning("Authentication data not detected, but proceeding anyway")
                    self.save_session()
                    return True
            else:
                logger.error("Failed to reach challenge page after login")
                return False
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False

    def smart_click(self, page: Page, role: str, name: str, timeout: int = 30000):
        """Click button with robust waiting and error handling using regex for resiliency."""
        try:
            locator = page.get_by_role(role, name=re.compile(rf"^{re.escape(name)}$", re.I))
            locator.wait_for(state="visible", timeout=timeout)
            locator.click()
            logger.info(f"Successfully clicked '{name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to click '{name}': {e}")
            return False

    def navigate_hidden_path(self, page: Page) -> bool:
        """Navigate through the hidden path to access product table."""
        try:
            logger.info("Navigating hidden path...")
            for role, name in self.buttons_path:
                logger.info(f"Attempting to click button for: {name}")
                if not self.smart_click(page, role, name):
                    if name == "Show Product Table":
                        logger.info("Show Product Table button not found, continuing")
                        break
                    else:
                        logger.error(f"Failed to click {name} button")
                        return False
                time.sleep(1)
                self.wait_for_idle_network()
            try:
                page.wait_for_selector("table >> tbody tr", timeout=20000)
                logger.info("Table found successfully")
                return True
            except PlaywrightTimeoutError:
                logger.error("Table not found after navigation")
                return False
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    def get_scrollable_parent_selector(self, page: Page, table_selector: str = "table") -> str:
        """Find the closest scrollable ancestor of the table."""
        script = """
        (sel) => {
            const el = document.querySelector(sel);
            if (!el) return "body";
            function isScrollable(node) {
                const style = window.getComputedStyle(node);
                const overflowY = style.overflowY;
                const canScroll = node.scrollHeight > node.clientHeight + 2;
                return canScroll && (overflowY === 'auto' || overflowY === 'scroll');
            }
            let p = el.parentElement;
            while (p && p !== document.body) {
                if (isScrollable(p)) {
                    if (p.id) return '#' + p.id;
                    if (p.className && typeof p.className === 'string') {
                        const firstClass = p.className.trim().split(/\\s+/)[0];
                        if (firstClass) return p.tagName.toLowerCase() + '.' + firstClass;
                    }
                    return p.tagName.toLowerCase();
                }
                p = p.parentElement;
            }
            return "body";
        }
        """
        try:
            sel = page.evaluate(script, table_selector)
            return sel
        except Exception:
            return "body"

    def extract_headers(self, page: Page) -> List[str]:
        """Extract table headers."""
        try:
            headers = []
            ths = page.locator("table thead th")
            if ths.count() > 0:
                for i in range(ths.count()):
                    headers.append(ths.nth(i).inner_text().strip())
            else:
                # Fallback: use first row as headers
                tds = page.locator("table tbody tr").first.locator("td")
                for i in range(tds.count()):
                    headers.append(f"Column_{i+1}")
            return headers
        except Exception:
            return []

    def infinite_scroll_table(self, page: Page, target_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Extract all table data using DOM-only approach for virtualized tables."""
        try:
            logger.info("Starting DOM-only infinite scroll extraction")
            page.wait_for_selector("table", state="visible")
            scroll_container = self.get_scrollable_parent_selector(page, "table")
            container = page.locator(scroll_container)
            container.first.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)

            headers = self.extract_headers(page)
            rows_data = []

            stagnant_rounds = 0
            max_stagnant = 3

            while stagnant_rounds < max_stagnant:
                current_count = page.locator("table tbody tr").count()
                if target_count and current_count >= target_count:
                    break
                
                # Show progress every 100 rows
                if current_count % 100 == 0 and current_count > 0:
                    logger.info(f"Progress: {current_count} rows extracted")
                try:
                    if scroll_container == "body":
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    else:
                        container.first.evaluate("(el) => el.scrollTop += el.clientHeight * 5")
                except Exception:
                    pass
                try:
                    page.wait_for_function(
                        f"document.querySelectorAll('table tbody tr').length > {current_count}", timeout=2000
                    )
                    grew = True
                except PlaywrightTimeoutError:
                    grew = False
                new_count = page.locator("table tbody tr").count()
                if new_count == current_count:
                    stagnant_rounds += 1
                else:
                    stagnant_rounds = 0
                if target_count and new_count >= target_count:
                    break

            raw_rows = page.eval_on_selector_all(
                "table tbody tr", "els => els.map(tr => Array.from(tr.cells, td => td.innerText.trim()))"
            )
            for row_cells in raw_rows:
                # Pad row_cells with None if it's shorter than headers
                padded_cells = row_cells + [None] * max(0, len(headers) - len(row_cells))
                # Truncate if longer than headers
                padded_cells = padded_cells[:len(headers)]
                
                if len(headers) > 0:
                    row_dict = dict(zip(headers, [c.strip() if c else None for c in padded_cells]))
                else:
                    # Fallback if no headers
                    row_dict = {f"Column_{j+1}": c.strip() if c else None for j, c in enumerate(padded_cells)}
                rows_data.append(row_dict)
            logger.info(f" Scraped {len(rows_data)} rows")
            return rows_data
        except Exception as e:
            logger.error(f"Error in infinite_scroll_table: {e}")
            return []

    def extract_product_data(self, target_count: int = 2332) -> List[Dict]:
        """Extract product data using efficient infinite scroll strategy."""
        try:
            logger.info("Starting data extraction...")
            products = self.infinite_scroll_table(self.page, target_count=target_count)
            clean_products = []
            for product in products:
                if isinstance(product, dict):
                    clean_product = {}
                    for k, v in product.items():
                        if isinstance(v, (str, int, float, bool, type(None))):
                            clean_product[k] = v
                        else:
                            clean_product[k] = str(v)
                    clean_products.append(clean_product)
            logger.info(f"Total extracted: {len(clean_products)}")
            return clean_products
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            return []

    def export_to_json(self, data: List[Dict]) -> None:
        """Export extracted data to JSON file."""
        try:
            output = {
                "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_products": len(data),
                "target_products": 2332,
                "products": data
            }
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            logger.info(f"Data exported successfully to {self.output_file}")
        except Exception as e:
            logger.error(f"Failed to export data: {e}")

    def check_session_status(self) -> Dict[str, Any]:
        """Check current session status for debugging."""
        try:
            if not self.context:
                return {"status": "no_context", "cookies": 0, "localStorage": 0}
            
            cookies = self.context.cookies()
            
            # Check localStorage
            localStorage_count = 0
            try:
                if self.page:
                    localStorage_count = self.page.evaluate("() => Object.keys(localStorage).length")
            except Exception:
                localStorage_count = 0
            
            return {
                "status": "active",
                "cookies": len(cookies),
                "localStorage": localStorage_count,
                "cookie_names": [c.get("name", "") for c in cookies[:5]],  # First 5 cookie names
                "url": self.page.url if self.page else "no_page"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def debug_storage_state(self) -> Dict[str, Any]:
        """Comprehensive debugging of all storage mechanisms."""
        try:
            if not self.page:
                return {"error": "No page available"}
            
            debug_info = {}
            
            # Check cookies
            try:
                cookies = self.context.cookies()
                debug_info['cookies'] = {
                    'count': len(cookies),
                    'details': cookies
                }
            except Exception as e:
                debug_info['cookies'] = {'error': str(e)}
            
            # Check localStorage
            try:
                localStorage_keys = self.page.evaluate("() => Object.keys(localStorage)")
                localStorage_values = {}
                for key in localStorage_keys:
                    try:
                        value = self.page.evaluate(f"() => localStorage.getItem('{key}')")
                        localStorage_values[key] = value
                    except:
                        localStorage_values[key] = "error_reading"
                debug_info['localStorage'] = {
                    'keys': localStorage_keys,
                    'values': localStorage_values
                }
            except Exception as e:
                debug_info['localStorage'] = {'error': str(e)}
            
            # Check sessionStorage
            try:
                sessionStorage_keys = self.page.evaluate("() => Object.keys(sessionStorage)")
                sessionStorage_values = {}
                for key in sessionStorage_keys:
                    try:
                        value = self.page.evaluate(f"() => sessionStorage.getItem('{key}')")
                        sessionStorage_values[key] = value
                    except:
                        sessionStorage_values[key] = "error_reading"
                debug_info['sessionStorage'] = {
                    'keys': sessionStorage_keys,
                    'values': sessionStorage_values
                }
            except Exception as e:
                debug_info['sessionStorage'] = {'error': str(e)}
            
            # Check if there are any authentication headers or tokens in the page
            try:
                auth_elements = self.page.evaluate("""
                    () => {
                        const elements = document.querySelectorAll('*');
                        const authRelated = [];
                        for (let el of elements) {
                            if (el.id && el.id.toLowerCase().includes('auth')) authRelated.push({type: 'id', value: el.id, text: el.textContent?.substring(0, 100)});
                            if (el.className && el.className.toLowerCase().includes('auth')) authRelated.push({type: 'class', value: el.className, text: el.textContent?.substring(0, 100)});
                        }
                        return authRelated;
                    }
                """)
                debug_info['auth_elements'] = auth_elements
            except Exception as e:
                debug_info['auth_elements'] = {'error': str(e)}
            
            # Check current URL and page title
            debug_info['current_url'] = self.page.url
            debug_info['page_title'] = self.page.title()
            
            return debug_info
            
        except Exception as e:
            return {"error": f"Debug failed: {str(e)}"}

    def cleanup_browser_resources(self):
        """Clean up browser resources."""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if hasattr(self, "pw") and self.pw:
                self.pw.stop()
            logger.info("Browser resources cleaned up")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")

    def show_detailed_session_info(self):
        """Show detailed information about current session state."""
        try:
            print("\nDETAILED SESSION STATUS:")
            print("=" * 50)
            
            # Check main session file
            if os.path.exists(self.session_file):
                size = os.path.getsize(self.session_file)
                print(f"Main session file: {self.session_file} ({size} bytes)")
                if size > 20:
                    with open(self.session_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        cookies_count = len(data.get("cookies", []))
                        origins_count = len(data.get("origins", []))
                        print(f"Cookies: {cookies_count}")
                        print(f"Origins: {origins_count}")
                else:
                    print("File too small (likely empty)")
            else:
                print(f"Main session file: {self.session_file} (not found)")
            
            # Check sessionStorage file
            if os.path.exists("session_storage.json"):
                size = os.path.getsize("session_storage.json")
                print(f"SessionStorage file: session_storage.json ({size} bytes)")
                if size > 10:
                    with open("session_storage.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                        print(f"Keys: {len(data)}")
                        if data:
                            print(f"Sample keys: {list(data.keys())[:5]}")
                else:
                    print("File too small (likely empty)")
            else:
                print("SessionStorage file: session_storage.json (not found)")
            
            # Check localStorage file
            if os.path.exists("local_storage.json"):
                size = os.path.getsize("local_storage.json")
                print(f"LocalStorage file: local_storage.json ({size} bytes)")
                if size > 10:
                    with open("local_storage.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                        print(f"Keys: {len(data)}")
                        if data:
                            print(f"Sample keys: {list(data.keys())[:5]}")
                else:
                    print("File too small (likely empty)")
            else:
                print("LocalStorage file: local_storage.json (not found)")
            
            print("=" * 50)
            
        except Exception as e:
            print(f"Error showing session info: {e}")

    def show_session_summary(self, session_status: Dict[str, Any], session_data: Optional[Dict] = None):
        """Show a concise summary of current session status."""
        print(f"Session Status: {session_status['cookies']} cookies, {session_status['localStorage']} localStorage items")
        if session_status['cookie_names']:
            print(f"Sample cookies: {', '.join(session_status['cookie_names'])}")
        
        if session_data:
            print(f"SessionStorage: {len(session_data)} keys restored")
        else:
            print("No sessionStorage file found")

    def print_session_info(self, after: str = "check"):
        """Unified method to load and display session information."""
        session_status = self.check_session_status()
        session_data = None
        
        if os.path.exists("session_storage.json"):
            try:
                with open("session_storage.json", "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                if after == "login":
                    print(f"Saved {len(session_data)} sessionStorage keys")
                elif after == "restore":
                    print(f"SessionStorage: {len(session_data)} keys restored")
            except Exception as e:
                logger.warning(f"Failed to read sessionStorage: {e}")
        else:
            if after == "login":
                print("Failed to save sessionStorage")
            elif after == "restore":
                print("No sessionStorage file found")
        
        self.show_session_summary(session_status, session_data)

    def run(self, headless: bool = False, target_count: int = 2332) -> bool:
        """Main execution method."""
        start_time = time.time()
        try:
            print("Starting Iden Challenge Unified Automation")
            logger.info("Starting Iden Challenge Unified Automation")

            # Show initial session status
            print("\nCHECKING EXISTING SESSION FILES")
            self.show_detailed_session_info()

            print("Setting up browser...")
            session_reused = self.setup_browser(headless)

            if not self.credentials["username"] or not self.credentials["password"]:
                raise Exception("Invalid credentials provided")

            # Check if we're already authenticated (session was reused)
            if session_reused:
                print("Using existing session - skipping authentication")
                logger.info("Using existing session - skipping authentication")
                
                # Show what session data we have
                self.print_session_info(after="restore")
            else:
                print("Starting authentication process")
                if not self.authenticate():
                    raise Exception("Authentication failed")
                print("Authentication successful!")
                
                # Show what we saved
                self.print_session_info(after="login")
            


            print("Navigating to product table")
            if not self.navigate_hidden_path(self.page):
                raise Exception("Navigation failed")
            print("Navigation successful!")

            print(f"Extracting product data (target: {target_count} products)")
            products = self.extract_product_data(target_count=target_count)
            if not products:
                raise Exception("Data extraction failed")
            print(f"Extracted {len(products)} products")

            print("Exporting data to JSON")
            self.export_to_json(products)

            execution_time = time.time() - start_time
            print(f"Automation completed successfully in {execution_time:.1f} seconds")
            print(f"Performance: {len(products)/execution_time:.1f} products/second")
            logger.info(f"Automation completed successfully in {execution_time:.1f} seconds")
            
            # Show final session status
            self.show_detailed_session_info()
            
            return len(products)  # Return actual count instead of just True

        except Exception as e:
            error_msg = f"Automation failed: {e}"
            print(f"{error_msg}")
            logger.error(error_msg)
            return False

        finally:
            self.cleanup_browser_resources()

def main():
    parser = argparse.ArgumentParser(
        description="Iden Challenge Unified Automation Script",
        epilog="""
Examples:
  python iden_unified.py                    # Run with default settings
  python iden_unified.py --headless         # Run in headless mode
  python iden_unified.py --target-count 1000 --output products.json  # Custom target and output
        """
    )
    parser.add_argument("--version", action="version", version="1.0.0")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--target-count", type=int, default=2332, help="Target number of products to extract (default: 2332)")
    parser.add_argument("--output", type=str, default="product_data.json", help="Output JSON file name (default: product_data.json)")
    
    args = parser.parse_args()
    
    if not os.getenv("IDEN_USERNAME") or not os.getenv("IDEN_PASSWORD"):
        print("Error: Missing IDEN_USERNAME / IDEN_PASSWORD environment variables")
        print("Please create a .env file in the current directory with:")
        print("IDEN_USERNAME=your_username")
        print("IDEN_PASSWORD=your_password")
        print("\nOr set them in your shell:")
        print("export IDEN_USERNAME=your_username")
        print("export IDEN_PASSWORD=your_password")
        return

    automation = IdenUnifiedAutomation()
    automation.output_file = args.output
    print(f"Running with target count: {args.target_count}, output: {args.output}")
    result = automation.run(headless=args.headless, target_count=args.target_count)
    if result and isinstance(result, int) and result > 0:  # result is now the actual count of products extracted
        actual_count = result
        print(f"\nAutomation completed successfully")
        print(f"Data exported to: {automation.output_file}")
        if actual_count >= args.target_count:
            print(f"Total products extracted: {actual_count} (target {args.target_count} reached)")
        else:
            print(f"Total products extracted: {actual_count} (target {args.target_count} not reached)")
        
        # Show what session files were created
        session_files = []
        if os.path.exists(automation.session_file):
            session_files.append(automation.session_file)
        if os.path.exists("session_storage.json"):
            session_files.append("session_storage.json")
        if os.path.exists("local_storage.json"):
            session_files.append("local_storage.json")
        
        if session_files:
            print(f"Session files created: {', '.join(session_files)}")
            print("Next time you run this script, it should skip login")
        else:
            print("No session files were created - login will be required next time")
    else:
        print("\nAutomation failed. Check logs for details.")
        exit(1)

if __name__ == "__main__":
    main()
