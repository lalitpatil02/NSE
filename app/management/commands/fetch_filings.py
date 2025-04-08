from django.core.management.base import BaseCommand
import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager


# Suppress TensorFlow logs if not needed
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

DOWNLOAD_DIR = os.path.abspath("./nse_downloads")

class Command(BaseCommand):
    help = 'Download NSE corporate filings CSV'

    def handle(self, *args, **kwargs):
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        chrome_options = Options()
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            url = 'https://www.nseindia.com/companies-listing/corporate-filings-announcements'
            driver.get(url)
            time.sleep(5)

            # Wait for the button and click with retry logic
            download_btn = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "CFanncEquity-download"))
            )
            
            try:
                download_btn.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", download_btn)

            self.stdout.write("Download initiated. Waiting...")
            time.sleep(15)

            # Verify download
            files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith('.csv')]
            if files:
                self.stdout.write(self.style.SUCCESS(f"Downloaded: {files[0]}"))
            else:
                self.stdout.write(self.style.ERROR("No CSV file found!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
        finally:
            driver.quit()