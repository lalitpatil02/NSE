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

    def handle(self, *args, **kwargs):
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
            
            # Wait for the download button with increased timeout
            self.stdout.write("Waiting for download button...")
            try:
                download_btn = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.ID, "CFanncEquity-download"))
                )
                self.stdout.write("Download button found")
            except TimeoutException:
                self.stdout.write(self.style.ERROR("Download button not found after 30 seconds"))
                driver.save_screenshot("nse_error.png")
                self.stdout.write("Screenshot saved as nse_error.png")
                return
            
            # Try to click the button
            try:
                self.stdout.write("Attempting to click download button...")
                download_btn.click()
            except ElementClickInterceptedException:
                self.stdout.write("Button click intercepted, trying JavaScript click...")
                driver.execute_script("arguments[0].click();", download_btn)

            self.stdout.write("Download initiated. Waiting for file...")
            
            # Wait for file to appear with timeout
            max_wait = 60  # seconds
            start_time = time.time()
            csv_file = None
            while time.time() - start_time < max_wait:
                files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.csv')]
                if files:
                    csv_file = os.path.join(DOWNLOAD_DIR, files[0])
                    self.stdout.write(self.style.SUCCESS(f"Downloaded: {files[0]}"))
                    break
                time.sleep(2)
            
            if not csv_file:
                self.stdout.write(self.style.ERROR(f"No CSV file found after {max_wait} seconds!"))
                self.stdout.write(f"Current directory contents: {os.listdir(DOWNLOAD_DIR)}")
                return

            # Read and process the CSV file
            self.stdout.write("Reading CSV file...")
            try:
                df = pd.read_csv(csv_file)
                
                # Print column names for debugging
                self.stdout.write("CSV Columns:")
                for col in df.columns:
                    self.stdout.write(f"- {col}")
                
                self.stdout.write(f"Found {len(df)} records in CSV")
                
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
                        }
                        
                        # Create or update the record
                        CorporateFiling.objects.update_or_create(
                            symbol=filing_data['symbol'],
                            filing_date=filing_data['filing_date'],
                            defaults=filing_data
                        )
                        
                        if index % 100 == 0:  # Progress update every 100 records
                            self.stdout.write(f"Processed {index + 1} records...")
                            
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Error processing row {index + 1}: {str(e)}"))
                        self.stdout.write(f"Row data: {row.to_dict()}")
                        continue
                
                self.stdout.write(self.style.SUCCESS(f"Successfully processed {len(df)} records"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading CSV file: {str(e)}"))
                return

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            driver.save_screenshot("nse_error.png")
            self.stdout.write("Screenshot saved as nse_error.png")
        finally:
            driver.quit()
            
            # Clean up downloaded file
            if csv_file and os.path.exists(csv_file):
                try:
                    os.remove(csv_file)
                    self.stdout.write("Cleaned up downloaded CSV file")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Could not remove CSV file: {str(e)}"))