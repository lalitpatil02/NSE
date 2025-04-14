from django.core.management.base import BaseCommand
import os
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from app.models import CorporateFiling


# Suppress TensorFlow logs if not needed
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

DOWNLOAD_DIR = os.path.abspath("./nse_downloads")

class Command(BaseCommand):
    help = 'Download NSE corporate filings CSV and save to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--categories',
            nargs='+',
            type=str,
            default=['equity', 'sme', 'mf'],
            help='Categories to fetch: equity, sme, mf (default: all three)'
        )

    def parse_datetime(self, value):
        if pd.isna(value) or not isinstance(value, str):
            return None
        try:
            # Remove curly quotes and other weird characters
            value = value.strip().strip('“”"\'')
            return datetime.strptime(value, "%d-%b-%Y %H:%M:%S")
        except ValueError:
            try:
                # Fallback to datetime with microseconds or time zone if needed
                return datetime.fromisoformat(value)
            except Exception:
                self.stdout.write(self.style.WARNING(f"Unrecognized datetime format: {value}"))
                return None
        
    def handle(self, *args, **kwargs):
        # Get the categories to fetch from the command line arguments
        categories_to_fetch = [category.lower() for category in kwargs.get('categories', ['equity', 'sme', 'mf'])]
        self.stdout.write(f"Fetching filings for categories: {', '.join(categories_to_fetch)}")
        
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        self.stdout.write(f"Download directory: {DOWNLOAD_DIR}")

        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--enable-javascript')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            url = 'https://www.nseindia.com/companies-listing/corporate-filings-announcements'
            self.stdout.write(f"Navigating to: {url}")
            driver.get(url)
            
            # Wait for page to load completely
            time.sleep(10)
            
            # Check if we're on the right page
            if "corporate-filings-announcements" not in driver.current_url:
                self.stdout.write(self.style.WARNING("Redirected to a different page. Current URL: " + driver.current_url))
                
            # Find all tab links on the page
            self.stdout.write("Finding all tab links on the page...")
            tab_links = driver.find_elements(By.CSS_SELECTOR, "a.nav-link[data-bs-toggle='tab']")
            
            if not tab_links:
                self.stdout.write(self.style.ERROR("No tab links found on the page!"))
                driver.save_screenshot("no_tabs_error.png")
                with open("no_tabs_error.html", "w") as f:
                    f.write(driver.page_source)
                return
            
            self.stdout.write(f"Found {len(tab_links)} tab links")
            
            # Create a list of tabs to process
            tabs_to_process = []
            for tab in tab_links:
                tab_id = tab.get_attribute("href")
                if tab_id:
                    # Extract the ID from the href (e.g., #Announcements_equity)
                    tab_id = tab_id.split("#")[-1]
                    data_variable = tab.get_attribute("data-variable")
                    data_tab = tab.get_attribute("data-tab")
                    
                    # Determine category from tab attributes
                    category = "unknown"
                    if "equity" in tab_id.lower() or "equity" in data_tab.lower() if data_tab else False:
                        category = "equity"
                    elif "sme" in tab_id.lower() or "sme" in data_tab.lower() if data_tab else False:
                        category = "sme"
                    elif "mf" in tab_id.lower() or "mf" in data_tab.lower() if data_tab else False:
                        category = "mf"
                    
                    # Skip if this category is not in the list of categories to fetch
                    if category not in categories_to_fetch:
                        self.stdout.write(f"Skipping tab {tab_id} with category {category} (not in requested categories)")
                        continue
                    
                    # Determine download button ID based on data-variable or tab ID
                    download_btn_id = None
                    if data_variable:
                        download_btn_id = f"{data_variable}-download"
                    elif tab_id:
                        download_btn_id = f"{tab_id}-download"
                    
                    # Add to tabs to process if we have a download button ID
                    if download_btn_id:
                        tabs_to_process.append({
                            "tab_element": tab,
                            "download_btn_id": download_btn_id,
                            "category": category,
                            "tab_id": tab_id
                        })
                        self.stdout.write(f"Added tab: {tab_id} | Category: {category} | Download button: {download_btn_id}")
            
            # Now process each tab
            for tab_info in tabs_to_process:
                self.process_tab(driver, tab_info)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            driver.save_screenshot("nse_error.png")
            self.stdout.write("Screenshot saved as nse_error.png")
        finally:
            driver.quit()
    
    def process_tab(self, driver, tab_info):
        tab_element = tab_info["tab_element"]
        download_btn_id = tab_info["download_btn_id"]
        category = tab_info["category"]
        tab_id = tab_info["tab_id"]
        
        self.stdout.write(f"Processing {category.upper()} tab (ID: {tab_id})...")
        
        # Click on the tab
        try:
            # Scroll to the element to ensure it's in view
            driver.execute_script("arguments[0].scrollIntoView(true);", tab_element)
            time.sleep(1)
            
            # Try direct click first, then JavaScript click if that fails
            try:
                tab_element.click()
                self.stdout.write(f"Direct click on {category.upper()} tab succeeded")
            except Exception as e:
                driver.execute_script("arguments[0].click();", tab_element)
                
            self.stdout.write(f"Clicked on {category.upper()} tab")
            time.sleep(5)  # Allow tab to load
            
            # Wait for the download button with increased timeout
            self.stdout.write(f"Waiting for {category.upper()} download button with ID: {download_btn_id}...")
            
            # Try to find download button by direct ID
            try:
                download_btn = WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.ID, download_btn_id))
                )
                self.stdout.write(f"{category.upper()} download button found by ID")
            except TimeoutException:
                # If not found by ID, try looking for any download button in the active tab content
                self.stdout.write(f"Download button not found by ID, looking for any download button in tab {tab_id}...")
                
                try:
                    # Find the active tab content
                    active_tab = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, tab_id))
                    )
                    # Look for download buttons within the active tab
                    download_buttons = active_tab.find_elements(By.CSS_SELECTOR, "button[id$='-download']")
                    
                    if download_buttons:
                        download_btn = download_buttons[0]
                        self.stdout.write(f"Found alternative download button: {download_btn.get_attribute('id')}")
                    else:
                        self.stdout.write(self.style.ERROR(f"No download buttons found in tab {tab_id}"))
                        driver.save_screenshot(f"error_{category}.png")
                        with open(f"error_{category}.html", "w") as f:
                            f.write(driver.page_source)
                        self.stdout.write(f"Screenshot and HTML saved as error_{category}.png/html")
                        return
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error finding download button: {str(e)}"))
                    driver.save_screenshot(f"error_{category}.png")
                    with open(f"error_{category}.html", "w") as f:
                        f.write(driver.page_source)
                    self.stdout.write(f"Screenshot and HTML saved as error_{category}.png/html")
                    return
            
            # Try to click the button
            try:
                self.stdout.write(f"Attempting to click {category.upper()} download button...")
                download_btn.click()
                self.stdout.write(f"Direct click on download button succeeded")
            except Exception as e:
                driver.execute_script("arguments[0].click();", download_btn)

            self.stdout.write(f"{category.upper()} download initiated. Waiting for file...")
            
            # Wait for file to appear with timeout
            max_wait = 60  # seconds
            start_time = time.time()
            csv_file = None
            while time.time() - start_time < max_wait:
                files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.csv')]
                if files:
                    csv_file = os.path.join(DOWNLOAD_DIR, files[0])
                    self.stdout.write(self.style.SUCCESS(f"Downloaded {category.upper()}: {files[0]}"))
                    break
                time.sleep(2)
            
            if not csv_file:
                self.stdout.write(self.style.ERROR(f"No {category.upper()} CSV file found after {max_wait} seconds!"))
                self.stdout.write(f"Current directory contents: {os.listdir(DOWNLOAD_DIR)}")
                return

            # Read and process the CSV file
            self.stdout.write(f"Reading {category.upper()} CSV file...")
            try:
                df = pd.read_csv(csv_file)
                
                # Print column names for debugging
                self.stdout.write(f"{category.upper()} CSV Columns:")
                for col in df.columns:
                    self.stdout.write(f"- {col}")
                
                self.stdout.write(f"Found {len(df)} records in {category.upper()} CSV")
                
                # Process each row and save to database
                for index, row in df.iterrows():
                    try:
                        # Extract date from BROADCAST DATE/TIME
                        broadcast_date = row.get('BROADCAST DATE/TIME', '')
                        if broadcast_date:
                            # Split the date and time
                            date_part = broadcast_date.split()[0]
                            try:
                                filing_date = datetime.strptime(date_part, '%d-%b-%Y').date()
                            except ValueError:
                                self.stdout.write(self.style.WARNING(f"Invalid date format for row {index + 1}: {date_part}"))
                                continue
                        else:
                            self.stdout.write(self.style.WARNING(f"No broadcast date found for row {index + 1}"))
                            continue
                        
                        # Map CSV columns to model fields
                        filing_data = {
                            'symbol': row.get('SYMBOL', ''),
                            'company_name': row.get('COMPANY NAME', ''),
                            'subject': row.get('SUBJECT', ''),
                            'filing_type': row.get('SUBJECT', ''),  # Using SUBJECT as filing type
                            'pdf_link': row.get('ATTACHMENT', ''),
                            'filing_date': filing_date,
                            'details': row.get('DETAILS', ''),
                            'source': 'NSE',
                            'category': category,  # Save the category (equity, sme, or mf)
                            'AMC_scheme_name': row.get('AMC/SCHEME NAME', ''),  
                            'broadcast_date': self.parse_datetime(row.get('BROADCAST DATE/TIME', '')),
                            'receipt_date': self.parse_datetime(row.get('RECEIPT', '')),
                            'dissemination': self.parse_datetime(row.get('DISSEMINATION', '')),
                            'difference':row.get('DIFFERENCE','')


                        }
                        
                        # Create or update the record
                        CorporateFiling.objects.update_or_create(
                            symbol=filing_data['symbol'],
                            filing_date=filing_data['filing_date'],
                            category=filing_data['category'],  # Ensure uniqueness per category
                            defaults=filing_data
                        )
                        
                        if index % 100 == 0:  # Progress update every 100 records
                            self.stdout.write(f"Processed {index + 1} records from {category.upper()}...")
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error processing {category.upper()} row {index + 1}: {str(e)}"))
                        self.stdout.write(f"Row data: {row.to_dict()}")
                        continue
                
                self.stdout.write(self.style.SUCCESS(f"Successfully processed {len(df)} records from {category.upper()}"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading {category.upper()} CSV file: {str(e)}"))
                return
            finally:
                # Clean up downloaded file
                if csv_file and os.path.exists(csv_file):
                    try:
                        # os.remove(csv_file)
                        self.stdout.write(f"Cleaned up downloaded {category.upper()} CSV file")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Could not remove {category.upper()} CSV file: {str(e)}"))
                        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error processing {category.upper()} tab: {str(e)}"))
            # Save detailed debugging info
            driver.save_screenshot(f"error_{category}.png")
            with open(f"error_{category}.html", "w") as f:
                f.write(driver.page_source)
            self.stdout.write(f"Screenshot and HTML saved as error_{category}.png/html")
            return